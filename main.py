import os
import logging
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    PicklePersistence
)
from text_to_speech import send_voice_message
from speech_to_text import handle_voice_to_text
from together import Together
from database import increment_message_count, add_user
from menu_config import get_menu_handler

# Загружаем переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Инициализация Together AI
together_client = Together(api_key=TOGETHER_API_KEY)

def clean_think_tags(text: str) -> str:
    """Удаляет текст между <think> и </think> включая сами теги."""
    start_tag = "<think>"
    end_tag = "</think>"
    while start_tag in text and end_tag in text:
        start_idx = text.find(start_tag)
        end_idx = text.find(end_tag) + len(end_tag)
        text = text[:start_idx] + text[end_idx:]
    return text.strip()

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    """Вспомогательная функция для отправки сообщений."""
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    
    context.bot_data['ADMIN_ID'] = ADMIN_ID
    
    if user.id == ADMIN_ID:
        menu_button = KeyboardButton("📊 MENU")
        reply_markup = ReplyKeyboardMarkup([[menu_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            'Привет! Задавай свои вопросы...',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text('Привет! Задавай свои вопросы...')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user = update.effective_user
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    if user_message == "📊 MENU" and user.id == ADMIN_ID:
        return
    
    add_user(user.id, user.username, user.first_name, user.last_name)
    increment_message_count()

    user_message = user_message.replace('\n', ' ')

    if context.user_data is None:
        context.user_data = {}

    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    context.user_data['user_message'][chat_id] = user_message

    keyboard = [
        [InlineKeyboardButton("Ответить текстом", callback_data="text")],
        [InlineKeyboardButton("Ответить голосом", callback_data="voice")],
        [InlineKeyboardButton("Ответить текстом и голосом", callback_data="both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите формат ответа:", reply_markup=reply_markup)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик голосовых сообщений."""
    user = update.effective_user
    chat_id = update.message.chat_id
    voice = update.message.voice
    
    add_user(user.id, user.username, user.first_name, user.last_name)
    increment_message_count()

    try:
        voice_file = await context.bot.get_file(voice.file_id)
        voice_path = f"/tmp/{voice.file_id}.ogg"
        await voice_file.download_to_drive(voice_path)

        text = await handle_voice_to_text(context, chat_id, voice_path)
        new_message = await context.bot.send_message(chat_id=chat_id, text=text)

        new_update = Update(
            update_id=update.update_id,
            message=new_message
        )
        await handle_message(new_update, context)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=str(e))

async def callback_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик таймаута."""
    chat_id = context.job.chat_id
    message_id = context.job.data

    if context.user_data is None:
        context.user_data = {}

    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    user_message = context.user_data['user_message'].get(chat_id)

    try:
        response = together_client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
        )

        reply_text = response.choices[0].message.content.strip()
        logging.info(f"Received reply from Together AI: {reply_text}")
        
        clean_text = clean_think_tags(reply_text)

        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=clean_text)
        await send_voice_message(context, chat_id, clean_text)

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с Together AI: {str(e)}")
        if "RateLimitReached" in str(e):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Превышен лимит запросов. Пожалуйста, попробуйте позже.")
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f'Ошибка при взаимодействии с Together AI: {str(e)}')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    chat_id = query.message.chat_id

    if query.data == "close_menu":
        from menu_config import close_menu
        await close_menu(update, context)
        return

    if context.user_data is None:
        context.user_data = {}

    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    user_message = context.user_data['user_message'].get(chat_id)

    waiting_message = await query.edit_message_text("🛠️⏰Готовлю для тебя ответ! Будь терпелив...")

    context.job_queue.run_once(callback_timeout, 0, chat_id=chat_id, data=waiting_message.message_id)

    try:
        response = together_client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
        )

        reply_text = response.choices[0].message.content.strip()
        logging.info(f"Received reply from Together AI: {reply_text}")
        
        clean_text = clean_think_tags(reply_text)

        if query.data == "voice":
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
            await send_voice_message(context, chat_id, clean_text)
        elif query.data == "text":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=clean_text)
        elif query.data == "both":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=clean_text)
            await send_voice_message(context, chat_id, clean_text)

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с Together AI: {str(e)}")
        if "RateLimitReached" in str(e):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Превышен лимит запросов. Пожалуйста, попробуйте позже.")
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f'Ошибка при взаимодействии с Together AI: {str(e)}')

    await query.answer()

async def main() -> None:
    """Основная функция бота."""
    # Создаем директорию для сохранения состояния, если ее нет
    os.makedirs("data", exist_ok=True)
    
    # Инициализируем persistence
    persistence = PicklePersistence(filepath="data/persistence")
    
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .persistence(persistence)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(get_menu_handler(ADMIN_ID))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice))
    application.add_handler(CallbackQueryHandler(button))

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
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
