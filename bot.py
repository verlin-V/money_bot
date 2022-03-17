import os
from decimal import Decimal, ROUND_HALF_EVEN
import io


from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)

load_dotenv('env/.env')

from constants import DECIMAL_PATTERN, LIMIT, TABLE
from utils import (
    telegram_id_to_user_id,
    get_user_balance,
    add_transaction,
    get_user_last_transaction_id,
    delete_transaction,
    get_transactions_history,
    get_transactions_count,
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

    reply_markup = _convert_buttons_to_reply_markup((
        ('ADD TRANSACTION', 'add_transaction'),
        ('GET 10 LAST TRANSACTIONS', f'get_transactions_history_{LIMIT}_{0}'),
        ('EXPORT ALL TRANSACTIONS', 'get_all_transactions_history')
    ))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Current balance: {user_balance}',
        reply_markup=reply_markup,
    )


def help_command(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            '\U0001F4CD For adding transaction just enter the amount '
            'or use /add_transaction '
            '(if you want to add outcome transaction, '
            'add "-" before count)\n\n'
            '\U0001F4CD Use /start for return to menu\n\n'
            '\U0001F4CD Use /export_transactions to get a file '
            'with al your transactions history\n\n'
            '\U0001F643 Enjoy!'
        ),
    )


def enter_the_amount(update, context):
    get_user_id(update)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Enter the amount:',
    )


def add_user_transaction(update, context):
    user_input = update.effective_message.text
    transaction_amount = Decimal(user_input.replace(',', '.')).quantize(
        exp=Decimal('0.01'),
        rounding=ROUND_HALF_EVEN,
    )

    user_id = get_user_id(update)
    add_transaction(
        user_id=user_id,
        value=transaction_amount,
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
            text='Your transaction has been removed\nYour balance: {}'.format(
                get_user_balance(get_user_id(update))
            )
        )
    except TypeError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Transaction has been already deleted'
        )


def get_users_transactions_history(update, context):
    limit, offset = map(
        int,
        update.callback_query.data.replace(
            'get_transactions_history_', ''
        ).split('_')
    )

    reply_markup = None
    if get_transactions_count(get_user_id(update)) > limit+offset:
        reply_markup = _convert_buttons_to_reply_markup(((
            'Next 10 Transactions >>',
            f'get_transactions_history_{limit}_{offset + limit}'
         ),))

    history = get_transactions_history(get_user_id(update), limit, offset)
    message = ''
    for value, date_time in history:
        value = str(value)
        date_time = date_time.strftime('%d-%m-%Y %H:%M:%S')
        message += '<code>{} | {:>13}</code>\n'.format(date_time, value)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f'<u><strong>Your transactions history:</strong></u>\n \n{message}'
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


def get_all_users_transactions(update, context):
    list_of_transactions_row = get_transactions_history(get_user_id(update))
    list_of_transactions = tuple(
        (
            date_time.strftime('%d-%m-%Y'),
            date_time.strftime('%H:%M:%S'),
            str(value)
        )
        for value, date_time in list_of_transactions_row
    )

    transactions_table = TABLE.format(''.join(
        '<tr><td>{}</td><td>{}</td><td>{}</td>'.format(date, time, amount)
        for date, time, amount in list_of_transactions
    ))
    text = io.StringIO()

    text.write(transactions_table)
    text.seek(0)
    buf = io.BytesIO()
    buf.write(text.getvalue().encode())
    buf.seek(0)
    buf.name = 'my_transactions_history.html'
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=buf,
    )


updater.dispatcher.add_handler(CommandHandler('start', menu_command))
updater.dispatcher.add_handler(
    CommandHandler('export_transactions', get_all_users_transactions)
)
updater.dispatcher.add_handler(CommandHandler('help', help_command))
updater.dispatcher.add_handler(
    CommandHandler('add_transaction', enter_the_amount)
)

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
    CallbackQueryHandler(
        get_users_transactions_history,
        pattern=r'^get_transactions_history_[0-9]+\_[0-9]+$'
    )
)
updater.dispatcher.add_handler(
    CallbackQueryHandler(
        get_all_users_transactions,
        pattern=r'get_all_transactions_history'
    )
)


if __name__ == '__main__':
    updater.start_polling()
    updater.idle()
