import os
import random
import schedule
import time
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import asyncio
import pytz
import functools

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SITE_URL = 'https://trychatgpt.ru'

#  =======  НАСТРОЙКИ  =======
TARGET_TIMEZONE = 'Europe/Moscow'  #  Целевой часовой пояс

# Сообщения для будних дней
weekday_morning_message = "Вставайте, Засранцы и давайте работайте над собой и на державу!"
weekday_evening_message = "Пора спать, Засранцы! Завтра все опять на работу, не проспите!"

# Сообщения для выходных
weekend_morning_message = "Спите еще? Вставайте завтракать!"
weekend_evening_message = "Хватит маяться! Спать пора уже!"

#  Случайные фразы (расширенный список)
random_phrases = [
    "Андрей, держись бодрей! А то Петька отмерзнет!",
    "Ну что, заскучали? Так займитесь делом!",
    "Эй, бездельники!  Работа сама себя не сделает!",
    "Солнце ещё высоко!  Вперёд, к свершениям!",
    "Кто рано встаёт, тому... тому работать надо!",
    "Не ленись, а то превратишься в ленивца!",
    "Работа не волк, но и без неё никак!",
    "Хватит мечтать, пора действовать!",
    "Что-то вы расслабились!  Соберитесь!",
    "Время – деньги!  Не тратьте его зря!",
    "А ну-ка, встряхнитесь!  Покажите, на что способны!",
    "Работа зовёт!  Отправляйтесь в бой!",
    "Не время для отдыха!  Ещё много дел впереди!",
    "Выше голову!  И с песней – вперёд!",
    "Сегодня ваш день!  Сделайте его незабываемым!",
]

# ==========================

chat_history = {}

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    """Вспомогательная функция для отправки сообщений."""
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message

async def send_random_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Отправляет случайное сообщение из списка."""
    message = random.choice(random_phrases)
    await send_message(context, chat_id, message)

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str) -> None:
    """Отправляет запланированное сообщение."""
    await send_message(context, chat_id, message)

def schedule_messages(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Планирует отправку сообщений."""
    tz = pytz.timezone(TARGET_TIMEZONE)  # Создаем объект часового пояса

    # Используем functools.partial для передачи аргументов и tz
    schedule.every().monday.at(functools.partial(lambda tz: "08:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_morning_message)
    )
    schedule.every().tuesday.at(functools.partial(lambda tz: "08:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_morning_message)
    )
    schedule.every().wednesday.at(functools.partial(lambda tz: "08:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_morning_message)
    )
    schedule.every().thursday.at(functools.partial(lambda tz: "08:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_evening_message)
    )
    schedule.every().monday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_evening_message)
    )
    schedule.every().tuesday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_evening_message)
    )
    schedule.every().wednesday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_evening_message)
    )
    schedule.every().thursday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_evening_message)
    )
    schedule.every().friday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekday_evening_message)
    )

    schedule.every().saturday.at(functools.partial(lambda tz: "09:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekend_morning_message)
    )
    schedule.every().sunday.at(functools.partial(lambda tz: "09:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekend_morning_message)
    )

    schedule.every().saturday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekend_evening_message)
    )
    schedule.every().sunday.at(functools.partial(lambda tz: "22:00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_scheduled_message, context=context, chat_id=chat_id, message=weekend_evening_message)
    )

    # Ежечасные случайные сообщения (с 9 до 21 включительно)
    schedule.every().hour.at(functools.partial(lambda tz: ":00", tz=tz)(), tz).do(  # Исправлено
        functools.partial(send_random_message, context=context, chat_id=chat_id)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text('Привет! Отправьте мне сообщение, и я перешлю его на trychatgpt.ru.')
    chat_id = update.message.chat_id
    schedule_messages(chat_id, context)  # Планируем сообщения

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /random (для ручной отправки)."""
    chat_id = update.message.chat_id
    await send_random_message(context, chat_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    # История сообщений (не используется в текущей логике, но может пригодиться)
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(user_message)
    if len(chat_history[chat_id]) > 20:
        chat_history[chat_id].pop(0)

    # Отправляем сообщение "Готовлю ответ..."
    waiting_message = await update.message.reply_text("Готовлю для тебя ответ! Будь терпелив...")

    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # Работа в фоновом режиме
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.binary_location = '/usr/bin/chromium'
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.set_page_load_timeout(30)  # Таймаут загрузки страницы
            driver.get(SITE_URL)
            await asyncio.sleep(5)  # Ждем загрузки

            # Проверяем, загрузилась ли страница (простой способ)
            if "ChatGPT" not in driver.page_source:
                raise Exception("Страница не загружена корректно.")

            input_field = driver.find_element(By.CSS_SELECTOR, 'textarea#input')
            input_field.send_keys(user_message)
            input_field.send_keys(Keys.RETURN)  # Отправляем сообщение
            await asyncio.sleep(5)  # Ждем ответа

            reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
            if reply_elements:
                reply_text = reply_elements[-1].text  # Берем последний ответ
                # Редактируем сообщение "Готовлю ответ..." и вставляем туда текст ответа
                await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)

            else:
                raise Exception("Ответ не найден.")

        except TimeoutException:
            await context.bot.edit_message_text(chat_id=chat_message_id, message_id=waiting_message.message_id, text="Превышено время ожидания ответа от ChatGPT.")

        except NoSuchElementException:
            await context.bot.edit_message_text(chat_id=chat_message_id, message_id=waiting_message.message_id, text="Не удалось найти поле ввода или ответ на странице.")
        except Exception as e:
            await context.bot.edit_message_text(chat_id=chat_message_id, message_id=waiting_message.message_id, text=f'Ошибка при взаимодействии с ChatGPT: {str(e)}')
        finally:
            if 'driver' in locals():
                try:
                    driver.quit()  # Закрываем браузер в любом случае
                except Exception:
                    pass  # Игнорируем ошибки при закрытии

    except Exception as e:
        await context.bot.edit_message_text(chat_id=chat_message_id, message_id=waiting_message.message_id,
                                              text=f'Ошибка: {str(e)}')


async def scheduler() -> None:
    """Планировщик задач."""
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)  # Проверяем задачи каждую секунду


async def main() -> None:
    """Основная функция бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('random', random))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    asyncio.create_task(scheduler())  # Запускаем планировщик в отдельной задаче

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(1)  # Просто чтобы не загружать процессор
    finally:
        # Корректно завершаем работу при остановке
        await application.stop()
        await application.updater.stop()
        await application.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
