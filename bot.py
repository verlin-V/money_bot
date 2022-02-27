import os

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import Updater, CommandHandler

load_dotenv('env/.env')

from utils import (
    telegram_id_to_user_id,
    get_user_balance,
)

updater = Updater(
    token=os.environ['BOT_TOKEN'],
    use_context=True,
)
dispatcher = updater.dispatcher

COMMANDS_BUTTONS = (
    ('ADD TRANSACTION', 'add_transaction'),
    ('GET TRANSACTIONS HISTORY', 'get_transactions_history'),
)


def menu_command(update, context):
    telegram_id = update.message.from_user['id']
    user_id = telegram_id_to_user_id(telegram_id)
    user_balance = get_user_balance(user_id)

    buttons = [
        [InlineKeyboardButton(text=text, callback_data=callback)]
        for text, callback in COMMANDS_BUTTONS
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Current balance: {user_balance}',
        reply_markup=reply_markup,
    )


updater.dispatcher.add_handler(CommandHandler('start', menu_command))


if __name__ == '__main__':
    updater.start_polling()
