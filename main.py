import os
import random as rand
import schedule
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import asyncio
import pytz

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SITE_URL = 'https://trychatgpt.ru'

random_phrases = [
    "Андрей, держись бодрей! А то Петька отмерзнет!",
    "Ну что, заскучали? Так займитесь делом!",
]

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    await context.bot.send_message(chat_id=chat_id, text=text)

async def send_random_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    await send_message(context, chat_id, rand.choice(random_phrases))

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str) -> None:
    await send_message(context, chat_id, message)

def schedule_messages(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule.set_timezone(pytz.timezone('Europe/Moscow'))
    
    schedule.every().monday.at("08:00").do(
        send_scheduled_message, context=context, chat_id=chat_id,
        message="Вставайте, Засранцы и давайте работайте над собой и на державу!"
    )
    
    for hour in range(9, 22):
        schedule.every().day.at(f"{hour:02}:00").do(
            send_random_message, context=context, chat_id=chat_id
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Отправьте мне сообщение, и я перешлю его на trychatgpt.ru.')
    schedule_messages(update.message.chat_id, context)

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_random_message(context, update.message.chat_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    chat_id = update.message.chat_id
    temp_message = await update.message.reply_text("Готовлю для тебя ответ! Будь терпелив...")
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-infobars')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            driver.set_page_load_timeout(30)
            driver.get(SITE_URL)
            
            # Явное ожидание загрузки элемента
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea#input'))
            )
            
            input_field = driver.find_element(By.CSS_SELECTOR, 'textarea#input')
            driver.execute_script("arguments[0].scrollIntoView();", input_field)
            driver.execute_script("arguments[0].click();", input_field)
            
            input_field.send_keys(user_message)
            input_field.send_keys(Keys.RETURN)
            
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.message-content'))
            )
            
            reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
            if reply_elements:
                reply_text = reply_elements[-1].text
                if reply_text.strip().lower() != user_message.strip().lower():
                    await context.bot.delete_message(chat_id, temp_message.message_id)
                    await update.message.reply_text(reply_text)
                else:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.message-content'))
                    )
                    reply_elements = driver.find_elements(By.CSS_SELECTOR, 'div.message-content')
                    await context.bot.delete_message(chat_id, temp_message.message_id)
                    await update.message.reply_text(reply_elements[-1].text)
            else:
                raise Exception("Ответ не найден")
                
        finally:
            driver.quit()
            
    except Exception as e:
        await context.bot.delete_message(chat_id, temp_message.message_id)
        await update.message.reply_text(f'Ошибка: {str(e)}')

async def keep_alive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Сервис активен!")

async def scheduler() -> None:
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('random', random))
    application.add_handler(CommandHandler('ping', keep_alive))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
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
