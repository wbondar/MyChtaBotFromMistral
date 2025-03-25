from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from database import get_message_stats, get_user_stats

MENU_STATE = range(1)

async def close_existing_menu(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Закрывает существующее меню, если оно есть."""
    if 'menu_messages' in context.chat_data:
        for msg_id in context.chat_data['menu_messages']:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=msg_id
                )
            except Exception as e:
                print(f"Ошибка при удалении меню: {e}")
        context.chat_data['menu_messages'] = []

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if user.id != context.bot_data.get('ADMIN_ID', 0):
        await update.message.reply_text("Извините, эта команда недоступна.")
        return ConversationHandler.END
    
    # Закрываем существующее меню, если оно есть
    await close_existing_menu(context, chat_id)
    
    # Получаем свежие данные статистики
    message_stats = get_message_stats()
    user_stats = get_user_stats()
    
    # Формируем текст с обновленной статистикой
    stats_text = (
        f"📊 Статистика бота (обновлено):\n\n"
        f"• Всего сообщений - {message_stats['total']} (шт.)\n"
        f"• Сообщений сегодня - {message_stats['today']} (шт.)\n"
        f"• Пользователей - {user_stats['count']} (шт.)\n\n"
        f"👥 Список пользователей:\n"
    )
    
    for user_id, data in user_stats['users'].items():
        username = data['username'] or "нет username"
        first_name = data['first_name'] or "нет имени"
        last_name = data['last_name'] or "нет фамилии"
        stats_text += f"🆔 {user_id}: {first_name} {last_name} (@{username})\n"
    
    # Создаем кнопку закрытия
    close_button = [[InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")]]
    reply_markup = InlineKeyboardMarkup(close_button)
    
    # Отправляем новое сообщение с меню
    msg = await update.message.reply_text(
        stats_text,
        reply_markup=reply_markup
    )
    
    # Сохраняем ID нового сообщения в chat_data
    if 'menu_messages' not in context.chat_data:
        context.chat_data['menu_messages'] = []
    context.chat_data['menu_messages'].append(msg.message_id)
    
    return MENU_STATE

async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    # Закрываем меню
    await close_existing_menu(context, chat_id)
    
    # Возвращаем кнопку MENU
    menu_button = KeyboardButton("📊 MENU")
    reply_markup = ReplyKeyboardMarkup([[menu_button]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Меню закрыто",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Закрываем меню
    await close_existing_menu(context, chat_id)
    
    # Возвращаем ответ в зависимости от прав пользователя
    if user.id == context.bot_data.get('ADMIN_ID', 0):
        menu_button = KeyboardButton("📊 MENU")
        reply_markup = ReplyKeyboardMarkup([[menu_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "Действие отменено",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Действие отменено")
    
    return ConversationHandler.END

def get_menu_handler(admin_id: int) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 MENU$"), show_menu)],
        states={
            MENU_STATE: [CallbackQueryHandler(close_menu, pattern="^close_menu$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
