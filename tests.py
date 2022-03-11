import decimal
import random
from unittest import TestCase

from dotenv import load_dotenv

load_dotenv('env/.test_env')

from utils import (
    conn,
    add_user,
    telegram_id_to_user_id,
    add_transaction,
    get_user_balance,
    get_transactions_history,
)


def _run_sql(sql, fetch=False):
    with conn.cursor() as cur:
        cur.execute(sql)
        if fetch:
            return cur.fetchall()


def _generate_telegram_id():
    return random.randint(100000, 999999)


class DBMethodsTestCase(TestCase):

    def setUp(self):
        self.telegram_id = _generate_telegram_id()
        _run_sql(
            f'INSERT INTO "user" (telegram_id) VALUES ({self.telegram_id})'
        )
        self.user_id = _run_sql(
            f'SELECT id from "user" WHERE telegram_id = {self.telegram_id}',
            fetch=True
        )[0][0]
        self.value = decimal.Decimal(random.randrange(1, 999999)) / 100
        self.is_income = random.choice([True, False])

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
        sql_code = (
            f'SELECT COUNT(*) FROM "transaction" '
            f'WHERE user_id = {self.user_id} AND is_income = {self.is_income} '
            f'AND value = {self.value}'
        )
        transaction_count = _run_sql(sql_code, True)[0][0]
        user_balance_sql = (
            f'SELECT balance FROM "user" WHERE id = {self.user_id}'
        )
        user_balance = _run_sql(user_balance_sql, True)[0][0]

        add_transaction(self.user_id, self.is_income, self.value)
        transaction_count_upd = _run_sql(sql_code, True)[0][0]
        self.assertEqual(transaction_count + 1, transaction_count_upd)
        self.assertEqual(
            user_balance + self.value * (-1, 1)[int(self.is_income)],
            _run_sql(user_balance_sql, True)[0][0]
        )

    def test_get_transactions_history_returns_history_for_specific_user(self):
        sql_code = (
            f'SELECT value, is_income FROM "transaction" '
            f'WHERE user_id = {self.user_id}'
        )
        self.assertEqual(
            get_transactions_history(self.user_id),
            _run_sql(sql_code, True)
        )
