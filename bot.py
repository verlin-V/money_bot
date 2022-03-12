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
    get_user_last_transaction_id,
    delete_transaction,
    get_transactions_history,
)

updater = Updater(
    token=os.environ['BOT_TOKEN'],
    use_context=True,
)
dispatcher = updater.dispatcher


def get_user_id(update):
    if not update.callback_query:
        telegram_id = update.effective_message.from_user['id']
    else:
        telegram_id = update.callback_query.from_user.id
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
    get_user_id(update)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Enter the amount:'
    )


def add_user_transaction(update, context):
    user_input = update.effective_message.text
    transaction_amount = Decimal(user_input.replace(',', '.')).quantize(
        exp=Decimal('0.01'),
        rounding=ROUND_HALF_EVEN,
    )
    if transaction_amount < 0:
        is_income = False
    else:
        is_income = True

    user_id = get_user_id(update)
    add_transaction(
        user_id=user_id,
        is_income=is_income,
        value=abs(transaction_amount),
    )

    reply_markup = _convert_buttons_to_reply_markup(((
         'Cancel transaction',
         f'remove_transaction_{get_user_last_transaction_id(user_id)}'
     ),))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Transaction {} added\nYour balance: {}'.format(
            transaction_amount,
            get_user_balance(get_user_id(update))
        ),
        reply_markup=reply_markup,
    )


def remove_transaction(update, context):
    try:
        transaction_id = int(
            update.callback_query.data.replace('remove_transaction_', '')
        )
        delete_transaction(transaction_id)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Your transaction {} has been removed\nYour balance: {}'.format(
                transaction_id,
                get_user_balance(get_user_id(update))
            )
        )
    except TypeError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Transaction has been already deleted'
        )


def get_users_transactions_history(update, context):
    history = get_transactions_history(get_user_id(update))
    message = ''
    for value, is_income, date_time in history:
        if not is_income:
            value = '-' + str(value)
        date_time = date_time.strftime('%Y-%m-%d | %H:%M:%S')
        message += '{}  |  {}\n'.format(date_time, value)
    separator = '_' * 35
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Your transactions history:\n{separator}\n{message}'
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
updater.dispatcher.add_handler(
    CallbackQueryHandler(
        remove_transaction, pattern=r'^remove_transaction_[0-9]+$')
)
updater.dispatcher.add_handler(
    CallbackQueryHandler(get_users_transactions_history, pattern=r'get_transactions_history')
)

if __name__ == '__main__':
    updater.start_polling()
    updater.idle()
