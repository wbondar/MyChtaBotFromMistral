import os
import logging
import asyncio
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI
from text_to_speech import send_voice_message

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_API_KEY = os.getenv("GitHubAPIKey")

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
    await update.message.reply_text('Привет! Задавай свои вопросы...')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    chat_id = update.message.chat_id

    # Удаляем символы новой строки из сообщения
    user_message = user_message.replace('\n', ' ')

    # Сохраняем сообщение пользователя для использования в callback_timeout
    context.user_data['user_message'] = user_message

    # Отправляем сообщение с выбором
    keyboard = [
        [InlineKeyboardButton("Ответить текстом", callback_data="text")],
        [InlineKeyboardButton("Ответить голосом", callback_data="voice")],
        [InlineKeyboardButton("Ответить текстом и голосом", callback_data="both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    waiting_message = await update.message.reply_text(
        "Готовлю для тебя ответ! Будь терпелив...\n\nДаю 5 секунд на размышление...",
        reply_markup=reply_markup
    )

    # Запускаем обратный отсчет
    async def countdown(context: ContextTypes.DEFAULT_TYPE):
        for i in range(5, 0, -1):
            await asyncio.sleep(1)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=waiting_message.message_id,
                text=f"Готовлю для тебя ответ! Будь терпелив...\n\n{i} секунд осталось...",
                reply_markup=reply_markup
            )

    context.user_data['countdown_task'] = asyncio.create_task(countdown(context))
    context.job_queue.run_once(callback_timeout, 5, chat_id=chat_id, data=waiting_message.message_id)

async def callback_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик таймаута."""
    chat_id = context.job.chat_id
    message_id = context.job.data
    user_message = context.user_data.get('user_message')

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
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f'Ошибка при взаимодействии с GitHub API: {str(e)}')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    chat_id = query.message.chat_id
    user_message = context.user_data.get('user_message')

    # Отменяем таймаут и обратный отсчет
    if 'countdown_task' in context.user_data:
        context.user_data['countdown_task'].cancel()

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
            await send_voice_message(context, chat_id, reply_text)
        elif query.data == "text":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=reply_text)
        elif query.data == "both":
            await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=reply_text)
            await send_voice_message(context, chat_id, reply_text)

    except Exception as e:
        logging.error(f"Ошибка при взаимодействии с GitHub API: {str(e)}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=query.message.message_id, text=f'Ошибка при взаимодействии с GitHub API: {str(e)}')

    await query.answer()
