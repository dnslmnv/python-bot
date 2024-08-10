from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
import requests
from cryptography.fernet import Fernet
import json

TOKEN = '7109843285:AAHNEnY-SpPbszZiODc60CKvHkDblO2fg88'
OWNER_ID = '543664962'

DJANGO_API_URL = 'http://127.0.0.1:8000/api/encrypted-user-ids/'
key = b'AvbQDh6i2LIRU-Wym_QrsKjFo1vdB-qSvsqVEiA_g5w='
cipher_suite = Fernet(key)

user_states = {}
broadcast_data = {}

# Список разрешённых user_id (администраторы)
allowed_user_ids = [358216042, 447294103, 543664962]  # Здесь должны быть user_id администраторов

# Создание клавиатуры с кнопками
def create_reply_keyboard(user_id):
    keyboard = [
        [KeyboardButton('Обратная связь🤖'),
         KeyboardButton('О Приложении')],
        [KeyboardButton('Инструкция🙏')]
    ]

    # Добавляем специальную кнопку только для администраторов
    if user_id in allowed_user_ids:
        keyboard.append([KeyboardButton("Специальная рассылка")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    reply_markup = create_reply_keyboard(user_id)
    # Клавиатура для кнопки "Открыть карту!"
    inline_keyboard = [
        [InlineKeyboardButton("Открыть карту!", url="https://t.me/DpsNet_bot/DPS_NET")]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(
        'Привет! ДПС.НЕТ - не способствует развитию преступности!\n\nНо если вдруг у вас просрочилась страховка или случайно наклеелась тонировка - Welcome.\n\nПрисоединяйся к нашей команде:',
        reply_markup=inline_markup
    )
    await update.message.reply_text(
        'Мы не отслеживаем вашу геопозицию!\n\nЗапрос отправляется для того чтоб корректно отобразить карту и показать посты ДПС рядом с вами!',
        reply_markup=inline_markup
    )
    # Отправляем видео
    video_path = 'BOT.mp4'  # Замените на URL вашего видео или используйте file_id, если оно загружено
    await update.message.reply_video(video=open(video_path, 'rb'))
    # Send the reply keyboard with commands

    await update.message.reply_text(
        'Вы можете использовать следующие команды:',
        reply_markup=reply_markup
    )

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id in allowed_user_ids:
        await update.message.reply_text('Введите текст для рассылки (или отправьте фото):')
        user_states[user_id] = 'awaiting_broadcast_text'
        broadcast_data[user_id] = {'text': '', 'photo': None}
    else:
        await update.message.reply_text("У вас нет прав для выполнения этого действия.")

async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    if user_states.get(user_id) == 'awaiting_broadcast_text':
        # Сохраняем текст для рассылки
        broadcast_data[user_id]['text'] = text

        # Проверка, было ли фото уже получено
        photo_present = broadcast_data[user_id].get('photo') is not None

        # Показать кнопки подтверждения
        keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data='confirm_broadcast')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_broadcast')],
            [InlineKeyboardButton("Редактировать", callback_data='edit_broadcast')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if photo_present:
            await update.message.reply_text(
                f"Текст и фото для рассылки готовы:\n\n{text}",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"Текст для рассылки: {text}",
                reply_markup=reply_markup
            )


async def handle_broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    photo = update.message.photo[-1] if update.message.photo else None

    if user_states.get(user_id) == 'awaiting_broadcast_text' and photo:
        # Сохраняем фото для рассылки
        broadcast_data[user_id]['photo'] = photo.file_id

        # Проверка, был ли текст уже получен
        broadcast_text = broadcast_data[user_id].get('text', '')

        # Показать кнопки подтверждения
        keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data='confirm_broadcast')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_broadcast')],
            [InlineKeyboardButton("Редактировать", callback_data='edit_broadcast')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if broadcast_text:
            await update.message.reply_text(
                f"Фото и текст для рассылки получены:\n\n{broadcast_text}",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Фото для рассылки получено.",
                reply_markup=reply_markup
            )


async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id

    if user_id in allowed_user_ids:
        # Получаем список user_id из Django
        response = requests.get(DJANGO_API_URL)
        encrypted_data = response.json().get('data')

        # Дешифруем данные
        decrypted_data = cipher_suite.decrypt(encrypted_data.encode('utf-8'))
        user_ids = json.loads(decrypted_data.decode('utf-8'))

        # Получаем текст и фото для рассылки
        broadcast_text = broadcast_data[user_id].get('text', '')
        broadcast_photo = broadcast_data[user_id].get('photo', None)

        # Ограничиваем длину подписи до 1024 символов
        caption = broadcast_text[:1024] if broadcast_text else None

        # Debugging logs
        print(f"Sending photo with ID: {broadcast_photo}")
        print(f"With caption: {caption}")

        # Отправляем фото с подписью
        for user in user_ids:
            try:
                if broadcast_photo:
                    await context.bot.send_photo(
                        chat_id=user,
                        photo=broadcast_photo,
                        caption=caption  # Убедитесь, что подпись включена здесь
                    )
                elif caption:
                    await context.bot.send_message(chat_id=user, text=caption)
            except Exception as e:
                print(f"Ошибка отправки пользователю {user}: {e}")

        await update.callback_query.message.reply_text("Рассылка успешно завершена.")
        user_states[user_id] = None
        broadcast_data.pop(user_id, None)
    else:
        await update.callback_query.answer("У вас нет прав для выполнения этого действия.")


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id

    if user_id in allowed_user_ids:
        await update.callback_query.message.reply_text("Рассылка отменена.")
        user_states[user_id] = None
        broadcast_data.pop(user_id, None)
    else:
        await update.callback_query.answer("У вас нет прав для выполнения этого действия.")

async def edit_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id

    if user_id in allowed_user_ids:
        await update.callback_query.message.reply_text("Введите новый текст для рассылки (или отправьте фото):")
        user_states[user_id] = 'awaiting_broadcast_text'
        broadcast_data[user_id] = {'text': '', 'photo': None}
    else:
        await update.callback_query.answer("У вас нет прав для выполнения этого действия.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video_path = 'BOT.mp4'
    await update.message.reply_video(video=open(video_path, 'rb'))

async def miniapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Сейчас мы находимся в стадии бета-тестирования!😎\n\n✔✔-- В Скором времени --✔✔\n\n- Построение маршрутов мимо постов🚔\n- Обновленные карты🗺\n- Предупреждение о постах на пути🌟', reply_markup=create_reply_keyboard(update.message.from_user.id))

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    # Mark this user as ready to send feedback
    user_states[user_id] = 'awaiting_feedback'
    await update.message.reply_text('Пожалуйста, введите ваше сообщение для отправки разработчикам бота.', reply_markup=create_reply_keyboard(user_id))

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
        await update.message.reply_text('Ваше сообщение отправлено разработчикам бота.', reply_markup=create_reply_keyboard(user_id))
        await update.message.reply_text('Спасибо за обратную связь!', reply_markup=create_reply_keyboard(user_id))
        # Reset user state
        user_states[user_id] = None
    elif user_states.get(user_id) == 'awaiting_broadcast_text':
        await handle_broadcast_text(update, context)
    elif text == 'Специальная рассылка' and user_id in allowed_user_ids:
        await start_broadcast(update, context)
    else:
        # Map the descriptive text to command handlers
        if text == 'Инструкция🙏':
            await help_command(update, context)
        elif text == 'О Приложении':
            await miniapp_command(update, context)
        elif text == 'Обратная связь🤖':
            await feedback_command(update, context)
        else:
            await update.message.reply_text('Используйте кнопки на клавиатуре, чтобы выбрать действие.', reply_markup=create_reply_keyboard(user_id))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in allowed_user_ids and user_states.get(user_id) == 'awaiting_broadcast_text':
        await handle_broadcast_photo(update, context)

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Route the callback query to the appropriate handler
    if query.data == 'confirm_broadcast':
        await confirm_broadcast(update, context)
    elif query.data == 'cancel_broadcast':
        await cancel_broadcast(update, context)
    elif query.data == 'edit_broadcast':
        await edit_broadcast(update, context)
    elif query.data == 'help':
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
    # Handle photo messages
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # Handle button clicks
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
