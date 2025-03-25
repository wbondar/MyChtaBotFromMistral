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
from database import get_message_stats, get_user_stats

MENU_STATE = range(1)

async def show_menu(update, context):
    user = update.effective_user
    
    if user.id != context.bot_data.get('ADMIN_ID', 0):
        await update.message.reply_text("Извините, эта команда недоступна.")
        return ConversationHandler.END
    
    # Удаляем предыдущее меню, если оно есть
    if 'menu_message_id' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['menu_message_id']
            )
        except Exception:
            pass
    
    message_stats = get_message_stats()
    user_stats = get_user_stats()
    
    stats_text = (
        f"📊 Статистика бота:\n\n"
        f"• Total messages - {message_stats['total']} (шт.)\n"
        f"• Today messages - {message_stats['today']} (шт.)\n"
        f"• Users - {user_stats['count']} (шт.)\n\n"
        f"👥 Список пользователей:\n"
    )
    
    for user_id, data in user_stats['users'].items():
        username = data['username'] or "нет username"
        first_name = data['first_name'] or "нет имени"
        last_name = data['last_name'] or "нет фамилии"
        stats_text += f"🆔 {user_id}: {first_name} {last_name} (@{username})\n"
    
    close_button = [[InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")]]
    reply_markup = InlineKeyboardMarkup(close_button)
    
    msg = await update.message.reply_text(
        stats_text,
        reply_markup=reply_markup
    )
    context.user_data['menu_message_id'] = msg.message_id  # Сохраняем ID сообщения
    
    return MENU_STATE

async def close_menu(update, context):
    query = update.callback_query
    await query.answer()
    
    # Удаляем ID сообщения из user_data при закрытии меню
    if 'menu_message_id' in context.user_data:
        del context.user_data['menu_message_id']
    
    await query.message.delete()
    
    menu_button = KeyboardButton("📊 MENU")
    reply_markup = ReplyKeyboardMarkup([[menu_button]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Меню закрыто",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def cancel(update, context):
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
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 MENU$"), show_menu)],
        states={
            MENU_STATE: [CallbackQueryHandler(close_menu, pattern="^close_menu$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
