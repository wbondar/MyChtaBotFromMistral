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
from menu_manager import MenuManager

MENU_STATE = range(1)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id != context.bot_data.get('ADMIN_ID', 0):
        await update.message.reply_text("Извините, эта команда недоступна.")
        return ConversationHandler.END
    
    # Удаляем все предыдущие меню в этом чате
    await MenuManager.close_previous_menus(update, context)
    
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
    
    # Сохраняем ID нового сообщения
    await MenuManager.add_menu_message(update, context, msg.message_id)
    
    return MENU_STATE

async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Удаляем сообщение меню
    try:
        await query.message.delete()
    except Exception as e:
        print(f"Ошибка при закрытии меню: {e}")
    
    # Очищаем сохраненные ID сообщений для этого чата
    await MenuManager.clear_menus_for_chat(update, context)
    
    # Возвращаем кнопку MENU
    menu_button = KeyboardButton("📊 MENU")
    reply_markup = ReplyKeyboardMarkup([[menu_button]], resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Меню закрыто",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Удаляем все меню в этом чате
    await MenuManager.close_previous_menus(update, context)
    await MenuManager.clear_menus_for_chat(update, context)
    
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
