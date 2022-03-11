import os
from decimal import Decimal, ROUND_HALF_EVEN

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)

load_dotenv('env/.env')

from constants import DECIMAL_PATTERN
from utils import (
    telegram_id_to_user_id,
    get_user_balance,
    add_transaction,
)

updater = Updater(
    token=os.environ['BOT_TOKEN'],
    use_context=True,
)
dispatcher = updater.dispatcher


def get_user_id(update):
    telegram_id = update.effective_message.from_user['id']
    return telegram_id_to_user_id(telegram_id)


def _convert_buttons_to_reply_markup(buttons):
    buttons = [
        [InlineKeyboardButton(text=text, callback_data=callback)]
        for text, callback in buttons
    ]
    return InlineKeyboardMarkup(buttons)


def menu_command(update, context):
    user_balance = get_user_balance(get_user_id(update))

    BUTTONS = (
        ('ADD TRANSACTION', 'add_transaction'),
        ('GET TRANSACTIONS HISTORY', 'get_transactions_history'),
    )
    reply_markup = _convert_buttons_to_reply_markup(BUTTONS)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Current balance: {user_balance}',
        reply_markup=reply_markup,
    )


def enter_the_amount(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Enter the amount:'
    )


def add_user_transaction(update, context):
    user_input = update.effective_message.text
    transaction_amount = Decimal(user_input).quantize(
        exp=Decimal('0.01'),
        rounding=ROUND_HALF_EVEN,
    )
    if transaction_amount < 0:
        is_income = False
    else:
        is_income = True

    add_transaction(
        user_id=get_user_id(update),
        is_income=is_income,
        value=abs(transaction_amount),
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Transaction added'
    )


updater.dispatcher.add_handler(CommandHandler('start', menu_command))
updater.dispatcher.add_handler(
    CallbackQueryHandler(enter_the_amount, pattern=r'add_transaction')
)
updater.dispatcher.add_handler(
    MessageHandler(
        Filters.regex(DECIMAL_PATTERN), add_user_transaction
    )
)

if __name__ == '__main__':
    updater.start_polling()
    updater.idle()
