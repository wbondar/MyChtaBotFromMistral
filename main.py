import os
import logging
import asyncio
from datetime import datetime, time
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from openai import OpenAI
from text_to_speech import send_voice_message
from speech_to_text import handle_voice_to_text
from message_counter import update_message_counter, get_message_count, reset_daily_counters
from user_manager import add_user, get_all_users

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_API_KEY = os.getenv("GitHubAPIKey")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Ваш Telegram ID

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=GITHUB_API_KEY,
)

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None) -> None:
    """Вспомогательная функция для отправки сообщений."""
    message = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    return message  # Возвращаем объект сообщения

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    add_user(chat_id, username)

    message_count = get_message_count(chat_id)
    await update.message.reply_text(f'Привет! Задавай свои вопросы...')

    # Добавляем кнопку меню для админа
    if chat_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("Меню", callback_data="menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Счетчик сообщений за день - {message_count} шт.", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Обновляем счетчик сообщений
    update_message_counter(chat_id)

    # Удаляем символы новой строки из сообщения
    user_message = user_message.replace('\n', ' ')

    # Инициализируем user_data, если он не существует
    if context.user_data is None:
        context.user_data = {}

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

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды для отображения списка пользователей."""
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    users = get_all_users()
    user_list = "\n".join(f"{username} (ID: {user_id})" for user_id, username in users.items())
    await update.message.reply_text(f"Количество пользователей: {len(users)}\n\n{user_list}")

async def reset_counters(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сбрасывает счетчики сообщений каждый день в 03:00."""
    reset_daily_counters()

async def callback_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик таймаута."""
    chat_id = context.job.chat_id
    message_id = context.job.data

    # Инициализируем user_data, если он не существует
    if context.user_data is None:
        context.user_data = {}

    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    # Получаем сообщение пользователя из user_data
    user_message = context.user_data['user_message'].get(chat_id)

    try:
        # Используем OpenAI API для получения ответа от ИИ
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            model="gpt-4o",
            temperature=1.0,
            top_p=1.0,
            max_tokens=1000,
        )

        reply_text = response.choices[0].message.content.strip()
        logging.info(f"Received reply from GitHub API: {reply_text}")

        # Отправляем текст и голос
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply_text)
        await send_voice_message(context, chat_id, reply_text)

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с GitHub API: {str(e)}")
        if "RateLimitReached" in str(e):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Превышен лимит запросов. Пожалуйста, попробуйте позже.")
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f'Ошибка при взаимодействии с GitHub API: {str(e)}')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    chat_id = query.message.chat_id

    # Инициализируем user_data, если он не существует
    if context.user_data is None:
        context.user_data = {}

    if 'user_message' not in context.user_data:
        context.user_data['user_message'] = {}

    user_message = context.user_data['user_message'].get(chat_id)

    if query.data == "menu":
        # Отправляем сообщение с меню для админа
        if chat_id == ADMIN_ID:
            keyboard = [
                [InlineKeyboardButton("Счетчик сообщений", callback_data="message_count")],
                [InlineKeyboardButton("Количество пользователей", callback_data="user_count")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Выберите опцию:", reply_markup=reply_markup)
        else:
            await query.answer("У вас нет доступа к этому меню.")
        await query.answer()
        return

    # Отправляем сообщение с обратным отсчетом
    waiting_message = await query.edit_message_text("🛠️⏰Готовлю для тебя ответ! Будь терпелив...")

    # Запускаем обработку ответа
    context.job_queue.run_once(callback_timeout, 0, chat_id=chat_id, data=waiting_message.message_id)

    try:
        # Используем OpenAI API для получения ответа от ИИ
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            model="gpt-4o",
            temperature=1.0,
            top_p=1.0,
            max_tokens=1000,
        )

        reply_text = response.choices[0].message.content.strip()
        logging.info(f"Received reply from GitHub API: {reply_text}")

        if query.data == "voice":
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
            await send_voice_message(context, chat_id, reply_text)
        elif query.data == "text":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)
        elif query.data == "both":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=reply_text)
            await send_voice_message(context, chat_id, reply_text)
        elif query.data == "message_count":
            message_count = get_message_count(chat_id)
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f"Счетчик сообщений за день: {message_count} шт.")
        elif query.data == "user_count":
            users = get_all_users()
            user_list = "\n".join(f"{username} (ID: {user_id})" for user_id, username in users.items())
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f"Количество пользователей: {len(users)}\n\n{user_list}")

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с GitHub API: {str(e)}")
        if "RateLimitReached" in str(e):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text="Превышен лимит запросов. Пожалуйста, попробуйте позже.")
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=waiting_message.message_id, text=f'Ошибка при взаимодействии с GitHub API: {str(e)}')

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
    application.add_handler(CommandHandler('users', list_users))

    # Устанавливаем ежедневный сброс счетчиков в 03:00
    application.job_queue.run_daily(reset_counters, time=time(hour=3, minute=0))

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
