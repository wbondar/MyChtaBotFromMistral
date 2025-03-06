#import os
import random as rand
import schedule
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
import asyncio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SITE_URL = 'https://trychatgpt.ru'

random_phrases = [
    "Андрей, держись бодрей! А то Петька отмерзнет!",
    "Ну что, заскучали? Так займитесь делом!",
    "Пора бы и за работу, но лучше выпейте по 100 грамм!",
    "Кто охотчий до еды, пусть пожалует сюды...",
    "Чем вы вообще вот занимаетесь, что я должен вас все время контролировать?",
    "Андрей! Прекрати ЭТО делать! Коллеги могут увидеть!",
    "Шайтаны, ну вы чего? Кто это опять такую кучу навалял?!",
    "Саня, расскажи про БАБ и про женщин!",
    "Вадик, проснись! Тебя все ищут!",
    "Перцы, рассказывайте кому что снилось сегодня?",
    "МЕРНЕМ ЖАНИД - значит на армянском (Дай мне умереть на твоем теле!)",
    "- Эх Яблочко да на тарелочке - Погибай же ты КОНТРА в перестрелочке!"
]

chat_history = {}

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    await context.bot.send_message(chat_id=chat_id, text=text)

async def send_random_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    message = rand.choice(random_phrases)
    await send_message(context, chat_id, message)

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str) -> None:
    await send_message(context, chat_id, message)

def schedule_messages(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule.every().monday.at("08:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Вставайте, Засранцы и давайте работайте над собой и на державу!"
    )
    schedule.every().tuesday.at("08:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Вставайте, Засранцы и давайте работайте над собой и на державу!"
    )
    schedule.every().wednesday.at("08:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Вставайте, Засранцы и давайте работайте над собой и на державу!"
    )
    schedule.every().thursday.at("08:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Вставайте, Засранцы и давайте работайте над собой и на державу!"
    )
    schedule.every().friday.at("08:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Вставайте, Засранцы и давайте работайте над собой и на державу!"
    )

    schedule.every().monday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Пора спать, Засранцы! Завтра все опять на работу, не проспите!"
    )
    schedule.every().tuesday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Пора спать, Засранцы! Завтра все опять на работу, не проспите!"
    )
    schedule.every().wednesday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Пора спать, Засранцы! Завтра все опять на работу, не проспите!"
    )
    schedule.every().thursday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Пора спать, Засранцы! Завтра все опять на работу, не проспите!"
    )
    schedule.every().friday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Пора спать, Засранцы! Завтра все опять на работу, не проспите!"
    )

    schedule.every().saturday.at("09:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Спите еще? Вставайте завтракать!"
    )
    schedule.every().sunday.at("09:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Спите еще? Вставайте завтракать!"
    )

    schedule.every().saturday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Хватит маяться! Спать пора уже!"
    )
    schedule.every().sunday.at("22:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Хватит маяться! Спать пора уже!"
    )

    for hour in range(9, 22):
        schedule.every().day.at(f"{hour:02}:00").do(
            send_random_message, context=context, chat_id=chat_id
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Отправьте мне сообщение, и я перешлю его на trychatgpt.ru.')
    chat_id = update.message.chat_id
    schedule_messages(chat_id, context)

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await send_random_message(context, chat_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    chat_id = update.message.chat_id

    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(user_message)
    if len(chat_history[chat_id]) > 20:
        chat_history[chat_id].pop(0)

    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.binary_location = '/usr/bin/chromium'

        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.set_page_load_timeout(30)
            driver.get(SITE_URL)
            await asyncio.sleep(5)

            if "ChatGPT" not in driver.page_source:
                raise Exception("Страница не загружена корректно.")

            input_field = driver.find_element(By.CSS_SELECTOR, 'textarea#input')
            input_field.send_keys(user_message)
            input_field.send_keys(Keys.RETURN)
            await asyncio.sleep(5)

            reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
            if reply_elements:
                reply_text = reply_elements[-1].text
                if reply_text.strip().lower() != user_message.strip().lower():
                    await update.message.reply_text(reply_text)
                else:
                    await update.message.reply_text("Пожалуйста, подождите...")
                    await asyncio.sleep(5)
                    reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
                    if reply_elements:
                        reply_text = reply_elements[-1].text
                        await update.message.reply_text(reply_text)
                    else:
                        await update.message.reply_text("Ошибка: ответ не найден.")
            else:
                raise Exception("Ответ не найден.")
        finally:
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
    except Exception as e:
        await update.message.reply_text(f'Ошибка: {str(e)}')

async def scheduler() -> None:
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('random', random))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем планировщик в фоновом режиме
    asyncio.create_task(scheduler())

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await application.stop()
        await application.updater.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
