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

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id != context.bot_data.get('ADMIN_ID', 0):
        await update.message.reply_text("Извините, эта команда недоступна.")
        return ConversationHandler.END
    
    # Удаляем предыдущее меню, если оно есть (с обработкой ошибок)
    if 'menu_message_id' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['menu_message_id']
            )
        except Exception as e:
            print(f"Не удалось удалить предыдущее меню: {e}")
        finally:
            # Всегда очищаем ID, даже если удаление не удалось
            del context.user_data['menu_message_id']
    
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
    context.user_data['menu_message_id'] = msg.message_id
    
    return MENU_STATE

async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Удаляем сообщение меню
    try:
        await query.message.delete()
    except Exception as e:
        print(f"Ошибка при закрытии меню: {e}")
    
    # Очищаем сохраненный ID сообщения
    if 'menu_message_id' in context.user_data:
        del context.user_data['menu_message_id']
    
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
    
    # Удаляем меню, если оно открыто
    if 'menu_message_id' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['menu_message_id']
            )
        except Exception as e:
            print(f"Ошибка при отмене: {e}")
        finally:
            if 'menu_message_id' in context.user_data:
                del context.user_data['menu_message_id']
    
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
