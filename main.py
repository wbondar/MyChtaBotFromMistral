import os
import logging
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
import asyncio
import speech_recognition as sr
from pydub import AudioSegment

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SITE_URL = 'https://trychatgpt.ru'

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    """Вспомогательная функция для отправки сообщений."""
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message  # Возвращаем объект сообщения

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text('Опаньки!!! Кого я вижу!😁😜 Ну валяй, задавай свои вопросы...')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    chat_id = update.message.chat_id
    # Удаляем символы новой строки из сообщения
    user_message = user_message.replace('\n', ' ')

    # Отправляем сообщение "Готовлю ответ..."
    waiting_message = await update.message.reply_text("Готовлю для тебя ответ! Будь терпелив...")

    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # Работа в фоновом режиме
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1924x1080')
        options.binary_location = '/usr/bin/chromium'

        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.set_page_load_timeout(60)  # Увеличиваем таймаут загрузки страницы
            driver.get(SITE_URL)
            logging.info("Page loaded successfully.")
            logging.info(f"Page source: {driver.page_source[:1000]}")  # Логируем часть HTML

            # Используем явное ожидание для загрузки страницы
            WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[placeholder="Введите сообщение"]')))
            logging.info("Input field located successfully.")

            # Проверка на наличие всплывающих окон
            try:
                accept_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Accept cookies"]')
                accept_button.click()
                logging.info("Accepted cookies.")
            except NoSuchElementException:
                logging.info("No cookie consent found.")

            input_field = driver.find_element(By.CSS_SELECTOR, 'textarea[placeholder="Введите сообщение"]')
            input_field.send_keys(user_message)
            input_field.send_keys(Keys.RETURN)  # Отправляем сообщение
            logging.info("Message sent to input field.")

            # Используем явное ожидание для получения ответа
            WebDriverWait(driver, 60).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, 'div.message-content') and
                           d.find_elements(By.CSS_SELECTOR, 'div.message-content')[-1].is_displayed() and
                           d.find_elements(By.CSS_SELECTOR, 'div.message-content')[-1].text.strip() != user_message.strip()
            )
            logging.info("Response received from site.")

            # Повторное получение элемента перед взаимодействием
            reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
            if reply_elements:
                reply_text = reply_elements[-1].text  # Берем последний ответ
                logging.info(f"Received reply from site: {reply_text}")
                logging.info(f"Page source: {driver.page_source[:1000]}")  # Логируем часть HTML
                # Редактируем сообщение "Готовлю ответ..." и вставляем туда текст ответа
                await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)

            else:
                raise Exception("Ответ не найден.")

        except TimeoutException:
            logging.error("Превышено время ожидания ответа от ChatGPT.")
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Превышено время ожидания ответа от ChatGPT.")

        except NoSuchElementException:
            logging.error("Не удалось найти поле ввода или ответ на странице.")
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Не удалось найти поле ввода или ответ на странице.")

        except ElementNotInteractableException:
            logging.error("Элемент не может быть использован. Возможно, он не виден или не загружен.")
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Элемент не может быть использован. Попробуйте позже.")

        except StaleElementReferenceException:
            logging.error("Элемент больше не присутствует в DOM. Попробуем получить его снова.")
            # Повторное получение элемента
            reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
            if reply_elements:
                reply_text = reply_elements[-1].text  # Берем последний ответ
                await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)
            else:
                raise Exception("Ответ не найден после повторного получения элемента.")

        except Exception as e:
            logging.error(f"Ошибка при взаимодействии с ChatGPT: {str(e)}")
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f'Ошибка при взаимодействии с ChatGPT: {str(e)}')
        finally:
            if 'driver' in locals():
                try:
                    driver.quit()  # Закрываем браузер в любом случае
                except Exception:
                    pass  # Игнорируем ошибки при закрытии

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id,
                                              text=f'Ошибка: {str(e)}')

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик голосовых сообщений."""
    chat_id = update.message.chat_id
    voice = update.message.voice

    try:
        # Скачиваем голосовое сообщение
        voice_file = await context.bot.get_file(voice.file_id)
        voice_path = f"/tmp/{voice.file_id}.ogg"
        await voice_file.download_to_drive(voice_path)

        # Конвертируем OGG в WAV
        audio = AudioSegment.from_ogg(voice_path)
        wav_path = f"/tmp/{voice.file_id}.wav"
        audio.export(wav_path, format="wav")

        # Преобразуем голосовое сообщение в текст
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")

        # Используем существующий контекст для отправки нового текстового сообщения
        new_message = await context.bot.send_message(chat_id=chat_id, text=text)

        # Создаем новый объект Update с текстом
        new_update = Update(
            update_id=update.update_id,
            message=new_message
        )
        await handle_message(new_update, context)

    except sr.UnknownValueError:
        logging.error("Не удалось распознать речь.")
        await context.bot.send_message(chat_id=chat_id, text="Не удалось распознать речь.")

    except sr.RequestError as e:
        logging.error(f"Ошибка сервиса распознавания речи: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text=f"Ошибка сервиса распознавания речи: {str(e)}")

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text=f'Ошибка: {str(e)}')

async def main() -> None:
    """Основная функция бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice))

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(1) # Просто чтобы не загружать процессор
    finally:
        # Корректно завершаем работу при остановке
        await application.stop()
        await application.updater.stop()
        await application.shutdown()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
