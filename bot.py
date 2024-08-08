from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler

TOKEN = '6947402319:AAEAx0tj9I0kYPm2sPuVafUUEMSKfbwERAc'
OWNER_ID = '543664962'

user_states = {}

# Create a ReplyKeyboardMarkup with more descriptive button labels
reply_keyboard = [
    [KeyboardButton('Обратная связь🤖'),
    KeyboardButton('О Приложении')]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Открыть карту!", url="https://t.me/DpsNet_bot/DPS_NET")]
    ]
    inline_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        'Привет! ДПС.НЕТ - не способствует развитию преступности!\n\nНо если вдруг у вас просрочилась страховка или случайно наклеелась тонировка - Welcome.\n\nПрисоединяйся к нашей команде:',
        reply_markup=inline_markup
    )
    await update.message.reply_text(
        'Мы не отслеживаем вашу геопозицию!\n\nЗапрос отправляется для того чтоб корректно отобразить карту и показать посты ДПС рядом с вами!',
        reply_markup=inline_markup
    )
    # Send the reply keyboard with commands
    await update.message.reply_text(
        'Вы можете использовать следующие команды:',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Доступные команды:\n'
        'Start - Начать работу с ботом\n'
        'Help - Получить помощь\n'
        'Mini App - Информация о Mini Apps\n'
        'Feedback - Отправить отзыв владельцу бота',
        reply_markup=reply_markup
    )

async def miniapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Сейчас мы находимся в стадии бета-тестирования!😎\n\n✔✔-- В Скором времени --✔✔\n\n- Построение маршрутов мимо постов🚔\n- Обновленные карты🗺\n- Предупреждение о постах на пути🌟', reply_markup=reply_markup)

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    # Mark this user as ready to send feedback
    user_states[user_id] = 'awaiting_feedback'
    await update.message.reply_text('Пожалуйста, введите ваше сообщение для отправки разработчикам бота.', reply_markup=reply_markup)

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text
    # Check if the user is in the feedback state
    if user_states.get(user_id) == 'awaiting_feedback':
        user_message = update.message.text
        # Send the message to the bot owner
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"Сообщение от пользователя @{update.message.from_user.username or update.message.from_user.id}:\n\n{user_message}"
        )
        # Confirm receipt to the user
        await update.message.reply_text('Ваше сообщение отправлено разработчикам бота.', reply_markup=reply_markup)
        await update.message.reply_text('Спасибо за обратную связь!', reply_markup=reply_markup)
        # Reset user state
        user_states[user_id] = None
    else:
        # Map the descriptive text to command handlers
        if text == 'Помощь🙏':
            await help_command(update, context)
        elif text == 'О Приложении':
            await miniapp_command(update, context)
        elif text == 'Обратная связь🤖':
            await feedback_command(update, context)
        else:
            await update.message.reply_text('Используйте кнопки на клавиатуре, чтобы выбрать действие.', reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'help':
        await help_command(update, context)
    elif query.data == 'miniapp':
        await miniapp_command(update, context)
    elif query.data == 'feedback':
        await feedback_command(update, context)

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("miniapp", miniapp_command))
    app.add_handler(CommandHandler("feedback", feedback_command))
    # Use filters to catch all text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Handle button clicks
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
