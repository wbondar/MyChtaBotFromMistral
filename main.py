import os
import logging
import asyncio
import json
import http.server
import socketserver
import threading
import webbrowser
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from text_to_speech import send_voice_message
from speech_to_text import handle_voice_to_text

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Путь к HTML файлу
HTML_FILE_PATH = "puter_ai.html"

# Порт для HTTP сервера
PORT = 8000

# Глобальная переменная для хранения ответа
global_response = ""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = HTML_FILE_PATH
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def start_server():
    handler = RequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

def open_html_file():
    webbrowser.open(f"http://localhost:{PORT}")

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    """Вспомогательная функция для отправки сообщений."""
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message  # Возвращаем объект сообщения

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text('Привет! Задавай свои вопросы...')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Удаляем символы новой строки из сообщения
    user_message = user_message.replace('\n', ' ')

    # Убедимся, что user_data инициализирован
    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    # Сохраняем сообщение пользователя для использования в callback_timeout
    context.user_data['user_message'][chat_id] = user_message

    # Отправляем сообщение с выбором
    keyboard = [
        [InlineKeyboardButton("Ответить текстом", callback_data="text")],
        [InlineKeyboardButton("Ответить голосом", callback_data="voice")],
        [InlineKeyboardButton("Ответить текстом и голосом", callback_data="both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите формат ответа:", reply_markup=reply_markup)

async def callback_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик таймаута."""
    chat_id = context.job.chat_id
    message_id = context.job.data

    # Убедимся, что user_data инициализирован
    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    # Получаем сообщение пользователя из user_data
    user_message = context.user_data['user_message'].get(chat_id)

    if not user_message:
        logging.error("User message not found in user_data")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Ошибка: сообщение пользователя не найдено.")
        return

    try:
        # Отправляем запрос на HTML файл для получения ответа от Puter.js
        global global_response
        global_response = ""
        open_html_file()
        await asyncio.sleep(5)  # Даем время для получения ответа

        reply_text = global_response
        logging.info(f"Received reply from Puter.js: {reply_text}")

        if not reply_text.strip():
            raise ValueError("Message text is empty")

        # Отправляем текст и голос
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply_text)
        await send_voice_message(context, chat_id, reply_text)

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с Puter.js: {str(e)}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f'Ошибка при взаимодействии с Puter.js: {str(e)}')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    chat_id = query.message.chat_id

    # Убедимся, что user_data инициализирован
    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    # Получаем сообщение пользователя из user_data
    user_message = context.user_data['user_message'].get(chat_id)

    if not user_message:
        logging.error("User message not found in user_data")
        await query.edit_message_text("Ошибка: сообщение пользователя не найдено.")
        await query.answer()
        return

    # Отправляем сообщение с обратным отсчетом
    waiting_message = await query.edit_message_text("🛠️⏰Готовлю для тебя ответ! Будь терпелив...")

    # Запускаем обработку ответа
    context.job_queue.run_once(callback_timeout, 0, chat_id=chat_id, data=waiting_message.message_id)

    try:
        # Отправляем запрос на HTML файл для получения ответа от Puter.js
        global global_response
        global_response = ""
        open_html_file()
        await asyncio.sleep(5)  # Даем время для получения ответа

        reply_text = global_response
        logging.info(f"Received reply from Puter.js: {reply_text}")

        if query.data == "voice":
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
            await send_voice_message(context, chat_id, reply_text)
        elif query.data == "text":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)
        elif query.data == "both":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)
            await send_voice_message(context, chat_id, reply_text)

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с Puter.js: {str(e)}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f'Ошибка при взаимодействии с Puter.js: {str(e)}')

    await query.answer()

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик голосовых сообщений."""
    chat_id = update.message.chat_id
    voice = update.message.voice

    try:
        # Скачиваем голосовое сообщение
        voice_file = await context.bot.get_file(voice.file_id)
        voice_path = f"/tmp/{voice.file_id}.ogg"
        await voice_file.download_to_drive(voice_path)

        # Преобразуем голосовое сообщение в текст
        text = await handle_voice_to_text(context, chat_id, voice_path)

        # Используем существующий контекст для отправки нового текстового сообщения
        new_message = await context.bot.send_message(chat_id=chat_id, text=text)

        # Создаем новый объект Update с текстом
        new_update = Update(
            update_id=update.update_id,
            message=new_message
        )
        await handle_message(new_update, context)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=str(e))

async def main() -> None:
    """Основная функция бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice))
    application.add_handler(CallbackQueryHandler(button))

    # Запускаем HTTP сервер в отдельном потоке
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

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
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
