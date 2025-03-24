from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from count_messages import get_message_stats
from count_users import get_user_stats

# Состояния для ConversationHandler
MENU_STATE = range(1)

async def show_menu(update, context):
    """Показывает меню статистики."""
    user = update.effective_user
    
    if user.id != context.bot_data.get('ADMIN_ID', 0):
        await update.message.reply_text("Извините, эта команда недоступна.")
        return ConversationHandler.END
    
    # Получаем статистику
    message_stats = get_message_stats()
    user_stats = get_user_stats()
    
    # Формируем текст сообщения
    stats_text = (
        f"📊 Статистика бота:\n\n"
        f"• Total messages - {message_stats['total']} (шт.)\n"
        f"• Today messages - {message_stats['today']} (шт.)\n"
        f"• Users - {user_stats['count']} (шт.)\n\n"
        f"👥 Список пользователей:\n"
    )
    
    # Добавляем информацию о каждом пользователе
    for user_id, data in user_stats['users'].items():
        username = data['username'] or "нет username"
        first_name = data['first_name'] or "нет имени"
        last_name = data['last_name'] or "нет фамилии"
        stats_text += f"🆔 {user_id}: {first_name} {last_name} (@{username})\n"
    
    # Кнопка для закрытия меню
    close_button = [[InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")]]
    reply_markup = InlineKeyboardMarkup(close_button)
    
    # Отправляем сообщение с меню
    await update.message.reply_text(
        stats_text,
        reply_markup=reply_markup
    )
    
    return MENU_STATE

async def close_menu(update, context):
    """Закрывает меню статистики."""
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    # Восстанавливаем кнопку меню
    menu_button = KeyboardButton("📊 MENU")
    reply_markup = ReplyKeyboardMarkup([[menu_button]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Меню закрыто",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def cancel(update, context):
    """Отменяет диалог и возвращает кнопку меню."""
    user = update.effective_user
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

def get_menu_handler(admin_id):
    """Возвращает обработчик меню с установленным ADMIN_ID."""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 MENU$"), show_menu)],
        states={
            MENU_STATE: [CallbackQueryHandler(close_menu, pattern="^close_menu$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
