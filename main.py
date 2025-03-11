import os
import random as rand
import asyncio
import logging
import nest_asyncio

# Разрешаем вложенные вызовы цикла событий
nest_asyncio.apply()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройки токена и URL сайта
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SITE_URL = 'https://trychatgpt.ru'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Список случайных фраз для рассылки
random_phrases = [
    "Андрей, держись бодрей! А то Петька отмерзнет!",
    "Ну что, заскучали? Так займитесь делом!",
    "Эй, бездельники! Работа сама себя не сделает!",
    "Солнце ещё высоко! Вперёд, к свершениям!",
    "Кто рано встаёт, тому... тому работать надо!",
    "Не ленись, а то превратишься в ленивца!",
    "Работа не волк, но и без неё никак!",
    "Хватит мечтать, пора действовать!"
]

# Хранение истории сообщений для каждого чата
chat_history = {}  # {chat_id: [сообщения, ...]}

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message

async def send_random_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    message = rand.choice(random_phrases)
    await send_message(context, chat_id, message)

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str) -> None:
    await send_message(context, chat_id, message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Отправьте мне сообщение, и я перешлю его на trychatgpt.ru.')
    chat_id = update.message.chat_id
    if chat_id not in chat_history:
        chat_history[chat_id] = []

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await send_random_message(context, chat_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Сохраняем историю (ограничиваем до 20 сообщений)
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(user_message)
    if len(chat_history[chat_id]) > 20:
        chat_history[chat_id].pop(0)

    waiting_message = await update.message.reply_text("Готовлю для тебя ответ! Будь терпелив...")

    try:
        options = webdriver.ChromeOptions()
        # Классический headless-режим
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.binary_location = '/usr/bin/chromium'

        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.get(SITE_URL)

        wait = WebDriverWait(driver, 30)
        # Ждем появления ключевого слова "ChatGPT" на странице
        wait.until(lambda d: "ChatGPT" in d.page_source)

        # Сохраняем количество уже имеющихся сообщений на странице
        old_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
        old_count = len(old_elements)

        # Находим поле ввода и отправляем сообщение
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea#input')))
        input_field.clear()
        input_field.send_keys(user_message)
        input_field.send_keys(Keys.RETURN)

        # Ждем появления нового ответа
        def new_message_present(drv):
            new_elements = drv.find_elements(By.CSS_SELECTOR, 'div.message-content')
            return len(new_elements) > old_count

        wait.until(new_message_present)

        new_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
        reply_text = new_elements[-1].text.strip()

        # Если полученный ответ совпадает с запросом, сообщаем об ошибке
        if reply_text == user_message:
            reply_text = "Похоже, произошла ошибка. Попробуйте еще раз."

        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)

    except TimeoutException:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id,
                                              text="Превышено время ожидания ответа от ChatGPT.")
    except NoSuchElementException:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id,
                                              text="Не удалось найти поле ввода или ответ на странице.")
    except Exception as e:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id,
                                              text=f'Ошибка при взаимодействии с ChatGPT: {str(e)}')
    finally:
        try:
            driver.quit()
        except Exception:
            pass

async def scheduled_monday_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Отправка сообщения всем чатам
    for chat_id in chat_history.keys():
        await send_scheduled_message(context, chat_id,
            "Вставайте, Засранцы и давайте работайте над собой и на державу!")

async def scheduled_hourly_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Отправка случайного сообщения всем чатам
    for chat_id in chat_history.keys():
        await send_random_message(context, chat_id)

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('random', random_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Инициализируем асинхронный планировщик
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(scheduled_monday_message, CronTrigger(day_of_week="mon", hour=8, minute=0), args=[application.bot])
    scheduler.add_job(scheduled_hourly_message, CronTrigger(minute=0), args=[application.bot])
    scheduler.start()

    # Асинхронный старт приложения по рекомендуемой схеме:
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    # Ожидаем завершения работы (например, при получении сигнала остановки)
    await application.updater.idle()
    await application.shutdown()
    scheduler.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
