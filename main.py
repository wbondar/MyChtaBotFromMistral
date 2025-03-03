import os
import random as rand
import schedule
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Ваш токен Telegram-бота
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# URL сайта
SITE_URL = 'https://trychatgpt.ru'

# Список случайных фраз
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

# Словарь для хранения истории сообщений
chat_history = {}

# Функция для отправки сообщений
async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    await context.bot.send_message(chat_id=chat_id, text=text)

# Функция для отправки случайного сообщения
async def send_random_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    message = rand.choice(random_phrases)
    await send_message(context, chat_id, message)

# Функция для отправки постоянного сообщения
async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str) -> None:
    await send_message(context, chat_id, message)

# Функция для планирования задач
def schedule_messages(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Постоянные сообщения
    schedule.every().monday.at("08:00").do(send_scheduled_message, context, chat_id, "Вставайте, Засранцы и давайте работайте над собой и на державу!")
    schedule.every().tuesday.at("08:00").do(send_scheduled_message, context, chat_id, "Вставайте, Засранцы и давайте работайте над собой и на державу!")
    schedule.every().wednesday.at("08:00").do(send_scheduled_message, context, chat_id, "Вставайте, Засранцы и давайте работайте над собой и на державу!")
    schedule.every().thursday.at("08:00").do(send_scheduled_message, context, chat_id, "Вставайте, Засранцы и давайте работайте над собой и на державу!")
    schedule.every().friday.at("08:00").do(send_scheduled_message, context, chat_id, "Вставайте, Засранцы и давайте работайте над собой и на державу!")

    schedule.every().monday.at("22:00").do(send_scheduled_message, context, chat_id, "Пора спать, Засранцы! Завтра все опять на работу, не проспите!")
    schedule.every().tuesday.at("22:00").do(send_scheduled_message, context, chat_id, "Пора спать, Засранцы! Завтра все опять на работу, не проспите!")
    schedule.every().wednesday.at("22:00").do(send_scheduled_message, context, chat_id, "Пора спать, Засранцы! Завтра все опять на работу, не проспите!")
    schedule.every().thursday.at("22:00").do(send_scheduled_message, context, chat_id, "Пора спать, Засранцы! Завтра все опять на работу, не проспите!")
    schedule.every().friday.at("22:00").do(send_scheduled_message, context, chat_id, "Пора спать, Засранцы! Завтра все опять на работу, не проспите!")

    schedule.every().saturday.at("09:00").do(send_scheduled_message, context, chat_id, "Спите еще? Вставайте завтракать!")
    schedule.every().sunday.at("09:00").do(send_scheduled_message, context, chat_id, "Спите еще? Вставайте завтракать!")

    schedule.every().saturday.at("22:00").do(send_scheduled_message, context, chat_id, "Хватит маяться! Спать пора уже!")
    schedule.every().sunday.at("22:00").do(send_scheduled_message, context, chat_id, "Хватит маяться! Спать пора уже!")

    # Случайные сообщения
    for hour in range(9, 22):
        schedule.every().day.at(f"{hour:02}:00").do(send_random_message, context, chat_id)

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

    # Обновляем историю сообщений
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(user_message)
    if len(chat_history[chat_id]) > 20:
        chat_history[chat_id].pop(0)

    async with async_playwright() as p:
        browser = None
        try:
            print("Запуск браузера...")
            browser = await p.firefox.launch(headless=False)  # Отключаем headless режим для отладки
            print("Браузер запущен.")
            page = await browser.new_page()
            print("Создана новая страница.")

            print(f"Переход на {SITE_URL}...")
            await page.goto(SITE_URL, timeout=60000)  # Увеличиваем таймаут до 60 секунд
            print("Страница загружена.")

            print("Ожидание селектора 'textarea#input'...")
            await page.wait_for_selector('textarea#input', timeout=60000)  # Увеличиваем таймаут до 60 секунд
            print("Селектор найден.")

            input_field = await page.query_selector('textarea#input')
            print("Поле ввода найдено.")
            await input_field.fill(user_message)
            print(f"Сообщение '{user_message}' отправлено.")
            await input_field.press('Enter')
            print("Нажата клавиша Enter.")

            print("Ожидание ответа...")
            await page.wait_for_selector('div.message-content', timeout=60000)  # Увеличиваем таймаут до 60 секунд
            print("Ответ получен.")

            reply_elements = await page.query_selector_all('div.message-content')
            if reply_elements:
                reply_text = await reply_elements[-1].text_content()
                if reply_text.strip().lower() != user_message.strip().lower():
                    await update.message.reply_text(reply_text)
                else:
                    await update.message.reply_text("Пожалуйста, подождите, я обрабатываю ваш запрос...")
                    await page.wait_for_timeout(5000)
                    reply_elements = await page.query_selector_all('div.message-content')
                    if reply_elements:
                        reply_text = await reply_elements[-1].text_content()
                        if reply_text.strip().lower() != user_message.strip().lower():
                            await update.message.reply_text(reply_text)
                        else:
                            await update.message.reply_text("Извините, я не могу обработать ваш запрос в данный момент. Пожалуйста, попробуйте позже.")
                    else:
                        await update.message.reply_text("Извините, я не могу обработать ваш запрос в данный момент. Пожалуйста, попробуйте позже.")
            else:
                await update.message.reply_text("Извините, я не могу обработать ваш запрос в данный момент. Пожалуйста, попробуйте позже.")

        except Exception as e:
            print(f"Ошибка: {e}")
            await update.message.reply_text(f"Произошла ошибка: {str(e)}")

        finally:
            if browser:
                await browser.close()
                print("Браузер закрыт.")

def main() -> None:
    # Создаем приложение и передаем ему токен вашего бота
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('random', random))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

    # Запускаем планировщик
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
