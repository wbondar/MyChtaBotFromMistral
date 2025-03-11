import os
import random as rand
import asyncio
import aioschedule as schedule
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess


TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SITE_URL = 'https://trychatgpt.ru'

RANDOM_PHRASES = [
    "Андрей, держись бодрей! А то Петька отмерзнет!",
    "Ну что, заскучали? Так займитесь делом!",
    "Эй, бездельники!  Работа сама себя не сделает!",
    "Солнце ещё высоко!  Вперёд, к свершениям!",
    "Кто рано встаёт, тому... тому работать надо!",
    "Не ленись, а то превратишься в ленивца!",
    "Работа не волк, но и без неё никак!",
    "Хватит мечтать, пора действовать!"
]


async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    """Вспомогательная функция для отправки сообщений."""
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message

async def send_random_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет случайное сообщение из списка."""
    message = rand.choice(RANDOM_PHRASES)
    await send_message(context, chat_id, message)

async def send_scheduled_message(chat_id: int, message: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет запланированное сообщение."""
    await send_message(context, chat_id, message)

async def restart_railway_service(context: ContextTypes.DEFAULT_TYPE):
    """Перезапускает сервис на Railway, используя Project Token."""
    railway_token = os.getenv("RAILWAY_TOKEN")
    if not railway_token:
        print("Ошибка: Не задан RAILWAY_TOKEN.")
        return

    try:
        # Используем asyncio.to_thread для запуска блокирующей операции в отдельном потоке
        await asyncio.to_thread(subprocess.run, ["railway", "restart"], env={"RAILWAY_TOKEN": railway_token}, check=True, capture_output=True, text=True)
        print("Сервис Railway успешно перезапущен.")

    except subprocess.CalledProcessError as e:
        print(f"Ошибка при перезапуске сервиса Railway: {e}")
        print(f"Stdout: {e.stdout}")  # Выводим stdout
        print(f"Stderr: {e.stderr}")  # Выводим stderr

def schedule_messages(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Планирует отправку сообщений."""
    schedule.every().monday.at("08:00").do(send_scheduled_message, chat_id=chat_id, message="Вставайте, Засранцы и давайте работайте над собой и на державу!", context=context)

    # Ежечасные случайные сообщения
    schedule.every().hour.at(":00").do(send_random_message, chat_id=chat_id, context=context)

    #Добавляем задачу перезапуска
    schedule.every().day.at("03:00").do(restart_railway_service, context=context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text('Привет! Отправьте мне сообщение, и я перешлю его на trychatgpt.ru.')
    chat_id = update.message.chat_id
    schedule_messages(chat_id, context)  # Планируем сообщения

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /random (для ручной отправки)."""
    chat_id = update.message.chat_id
    await send_random_message(chat_id, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    waiting_message = await update.message.reply_text("Готовлю для тебя ответ! Будь терпелив...")

    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--window-size=1920x1080')  # Удаляем
        # options.binary_location = '/usr/bin/chromium'  # Удаляем
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.set_page_load_timeout(30)
            driver.get(SITE_URL)

            # Ждем появления поля ввода
            input_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea#input'))
            )

            input_field.send_keys(user_message)
            input_field.send_keys(Keys.RETURN)

            # Ждем появления *последнего* ответа (с учетом возможной задержки)
            WebDriverWait(driver, 60).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, 'div.message-content')) > 0
            )
            reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
            reply_text = reply_elements[-1].text

            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)

        except TimeoutException:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Превышено время ожидания ответа от ChatGPT.")
        except NoSuchElementException:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Не удалось найти поле ввода или ответ на странице.")

        except WebDriverException as e:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f'Ошибка WebDriver: {str(e)}')

        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f'Неожиданная ошибка: {str(e)}')
        finally:
            driver.quit()

    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id,
                                              text=f'Ошибка: {str(e)}')


async def scheduler() -> None:
    """Планировщик задач."""
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)

async def main() -> None:
    """Основная функция бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('random', random))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    asyncio.create_task(scheduler())  # Запускаем планировщик

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        # Корректно завершаем работу при остановке
        await application.stop()
        await application.updater.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
