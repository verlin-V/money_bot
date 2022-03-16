import re
from datetime import datetime, timezone, timedelta
import decimal
import random
from unittest import TestCase

from dotenv import load_dotenv

load_dotenv('env/.test_env')

from constants import DECIMAL_PATTERN
from utils import (
    conn,
    add_user,
    telegram_id_to_user_id,
    add_transaction,
    get_user_balance,
    get_transactions_history,
    delete_transaction,
    get_user_last_transaction_id,
    get_transactions_count,
)


def _run_sql(sql, fetch=False):
    with conn.cursor() as cur:
        cur.execute(sql)
        if fetch:
            return cur.fetchall()


def _generate_telegram_id():
    return random.randint(100000, 999999)


class DBMethodsTestCase(TestCase):
    SQL_FORMAT_USER_BALANCE = '''
        SELECT balance FROM "user" WHERE id = {}
    '''
    SQL_FORMAT_COUNT_OF_TRANSACTION = '''
        SELECT COUNT(*) FROM "transaction"
        WHERE user_id = {}
    '''
    SQL_FORMAT_ADD_TRANSACTION = '''
        INSERT INTO "transaction" (user_id, "value", date_time)
        VALUES ({}, {}, '{}')
    '''
    SQL_FORMAT_GET_TRANSACTION_ID = '''
        SELECT "id" FROM transaction
        WHERE date_time = '{}' and user_id = {}
        LIMIT 1
    '''

    def setUp(self):
        self.telegram_id = _generate_telegram_id()
        _run_sql(
            f'INSERT INTO "user" (telegram_id) VALUES ({self.telegram_id})'
        )
        self.user_id = _run_sql(
            f'SELECT id from "user" WHERE telegram_id = {self.telegram_id}',
            fetch=True
        )[0][0]
        self.value = decimal.Decimal(random.randrange(-999999, 999999)) / 100

    def test_add_user_adds_user(self):
        sql_code = 'SELECT COUNT(*) FROM "user"'
        users_count = _run_sql(sql_code, True)[0][0]
        add_user(_generate_telegram_id())
        users_count_upd = _run_sql(sql_code, True)[0][0]
        self.assertEqual(users_count + 1, users_count_upd)

    def test_add_user_adds_user_with_specific_telegram_id(self):
        telegram_id = _generate_telegram_id()
        sql_code = (
            f'SELECT COUNT(*) FROM "user" WHERE telegram_id = {telegram_id}'
        )
        users_count = _run_sql(sql_code, True)[0][0]
        add_user(telegram_id)
        users_count_upd = _run_sql(sql_code, True)[0][0]
        self.assertEqual(users_count + 1, users_count_upd)

    def test_telegram_id_to_user_id_for_existing_user(self):
        self.assertEqual(telegram_id_to_user_id(self.telegram_id), self.user_id)

    def test_telegram_id_to_user_id_for_not_existing_user(self):
        sql_code = 'SELECT id from "user" WHERE telegram_id = {} LIMIT 1;'

        user_exists = True
        while user_exists:
            telegram_id = _generate_telegram_id()
            user_exists = bool(_run_sql(sql_code.format(telegram_id), True))

        user_id = telegram_id_to_user_id(telegram_id)

        self.assertEqual(
            user_id,
            _run_sql(sql_code.format(telegram_id), True)[0][0]
        )

    def test_get_user_balance_returns_correct_balance_for_specific_user(self):
        sql_code = (f'SELECT balance FROM "user" WHERE id = {self.user_id}')
        self.assertEqual(
            _run_sql(sql_code, fetch=True)[0][0], get_user_balance(self.user_id)
        )

    def test_add_transaction_adds_transaction_to_specific_user(self):
        sql_code = self.SQL_FORMAT_COUNT_OF_TRANSACTION.format(self.user_id
                                                               )
        transaction_count = _run_sql(sql_code, True)[0][0]
        user_balance_sql = self.SQL_FORMAT_USER_BALANCE.format(self.user_id)
        user_balance = _run_sql(user_balance_sql, True)[0][0]

        add_transaction(self.user_id, self.value)

        transaction_count_upd = _run_sql(sql_code, True)[0][0]
        self.assertEqual(transaction_count + 1, transaction_count_upd)
        self.assertEqual(
            user_balance + self.value,
            _run_sql(user_balance_sql, True)[0][0]
        )

    def test_get_transactions_history_returns_history_for_specific_user(self):
        for n in range(1, 4):
            timestamp = (
                datetime.now(timezone.utc) +
                timedelta(days=n*(-1, 1)[n % 2])
            )
            _run_sql(self.SQL_FORMAT_ADD_TRANSACTION.format(
                self.user_id,
                self.value * n,
                timestamp,
            ))

        count_of_transactions = _run_sql(
            self.SQL_FORMAT_COUNT_OF_TRANSACTION.format(self.user_id),
            True
        )[0][0]
        history = get_transactions_history(self.user_id)

        self.assertEqual(count_of_transactions, len(history))

        list_of_dates = [date for _, date in history]
        self.assertEqual(
            list_of_dates,
            sorted(list_of_dates, reverse=True)
        )

    def test_get_transactions_history_returns_limited_history_with_offset(self):
        for n in range(1, 11):
            _run_sql(self.SQL_FORMAT_ADD_TRANSACTION.format(
                self.user_id,
                self.value * n,
                datetime.now(timezone.utc) + timedelta(seconds=n),
            ))

        history = get_transactions_history(self.user_id)

        for limit, offset in (
            (random.randint(1, 9), None),
            (None, random.randint(1, 9)),
            (random.randint(1, 9), random.randint(1, 9)),
        ):
            with self.subTest(limit=limit, offset=offset):
                if not limit:
                    right_bound = len(history)
                else:
                    right_bound = (limit or 0) + (offset or 0)

                self.assertEqual(
                    get_transactions_history(self.user_id, limit, offset),
                    history[offset or 0:right_bound]
                )



    def test_delete_transaction_deletes_specific_transaction(self):
        timestamp = datetime.now(timezone.utc)
        _run_sql(self.SQL_FORMAT_ADD_TRANSACTION.format(
            self.user_id,
            self.value,
            timestamp
        ))
        count_of_transactions_sql = self.SQL_FORMAT_COUNT_OF_TRANSACTION.format(
            self.user_id
        )
        transaction_count = _run_sql(count_of_transactions_sql, True)[0][0]
        user_balance_sql = self.SQL_FORMAT_USER_BALANCE.format(self.user_id)
        user_balance = _run_sql(user_balance_sql, True)[0][0]
        transaction_id = _run_sql(
            self.SQL_FORMAT_GET_TRANSACTION_ID.format(timestamp, self.user_id),
            True
        )[0][0]

        delete_transaction(transaction_id)

        self.assertFalse(
            _run_sql(
                f'''SELECT * FROM transaction
                WHERE id = {transaction_id}
                ''',
                True
            )
        )
        self.assertEqual(
            transaction_count - 1,
            _run_sql(count_of_transactions_sql, True)[0][0]
        )
        self.assertEqual(
            user_balance - self.value,
            _run_sql(user_balance_sql, True)[0][0]
        )

    def test_decimal_pattern_accepts_only_correct_numbers(self):
        cases = (
            ('0', True),
            ('175', True),
            ('-776', True),
            ('+776', True),
            ('214324,323', True),
            ('3423332.98765', True),
            ('-3453553.435', True),
            ('+3453553.435', True),
            ('-56324,533', True),
            ('+56324,533', True),
            ('+004,533', True),
            ('', False),
            ('a;f["pkasfd', False),
            ('1.22.2', False),
            ('1.22,2', False),
            ('1,22.2', False),
            ('1..2', False),
            ('1,,2', False),
            ('1,.2', False),
            ('a1.2', False),
            ('--1', False),
            ('++1', False),
         )
        for item, result in cases:
            with self.subTest(item=item, result=result):
                self.assertEqual(
                    bool(re.match(DECIMAL_PATTERN, item)),
                    result
                )

    def test_get_user_last_transaction_id_returns_last_transaction(self):
        for n in range(1, 4):
            timestamp = datetime.now(timezone.utc) + timedelta(days=n)
            _run_sql(self.SQL_FORMAT_ADD_TRANSACTION.format(
                self.user_id,
                self.value * n,
                timestamp,
            ))

        transaction_id = get_user_last_transaction_id(self.user_id)

        self.assertEqual(
            transaction_id,
            _run_sql(self.SQL_FORMAT_GET_TRANSACTION_ID.format(
                timestamp,
                self.user_id),
                True)[0][0]
        )

    def test_get_transactions_count_returns_correct_count(self):
        sql_code = self.SQL_FORMAT_COUNT_OF_TRANSACTION.format(self.user_id)
        expected_result = _run_sql(sql_code, True)[0][0]

        result = get_transactions_count(self.user_id)

        self.assertEqual(expected_result, result)
        self.assertTrue(isinstance(result, int))
