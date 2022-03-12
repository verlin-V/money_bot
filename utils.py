import os
from decimal import Decimal

import psycopg2

conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_DATABASE'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
)
conn.autocommit = True


def add_user(telegram_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f'''
            INSERT INTO "user" (telegram_id, balance)
            VALUES ({telegram_id}, 0);
            '''
        )

    return telegram_id_to_user_id(telegram_id)


def telegram_id_to_user_id(telegram_id: int):
    with conn.cursor() as cur:
        cur.execute(
            f'''
            SELECT id from "user"
            WHERE telegram_id = {telegram_id}
            LIMIT 1;
            '''
        )
        user_id = cur.fetchone()

    if user_id:
        return user_id[0]

    return add_user(telegram_id)


def add_transaction(user_id: int, is_income: bool, value: Decimal):
    with conn.cursor() as cur:
        cur.execute(
            f'''
            INSERT INTO "transaction" (user_id, "value", is_income, date_time)
            VALUES ({user_id}, {value}, {is_income}, CURRENT_TIMESTAMP)
            '''
        )
    _update_user_balance(user_id, is_income, value)


def _update_user_balance(user_id: int, is_income: bool, value: Decimal):
    balance = get_user_balance(user_id)
    if is_income:
        balance += value
    else:
        balance -= value

    with conn.cursor() as cur:
        cur.execute(
            f'''
            UPDATE "user"
            SET balance = {balance}
            WHERE id = {user_id}
            '''
        )


def get_transactions_history(user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            f'''
           SELECT value, is_income FROM "transaction"
           WHERE user_id = {user_id};
           '''
        )
        return cur.fetchall()


def get_user_balance(user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            f'''
            SELECT balance FROM "user"
            WHERE id = {user_id};
            '''
        )
        return Decimal(cur.fetchone()[0])


def delete_transaction(transaction_id: int):
    with conn.cursor() as cur:
        cur.execute(
            f'''
            SELECT user_id, is_income, value
            FROM transaction
            WHERE id = {transaction_id}
            '''
        )
        user_id, is_income, value = cur.fetchone()

        cur.execute(
            f'''
            DELETE FROM transaction
            WHERE id = {transaction_id}
            '''
        )
        _update_user_balance(user_id, not is_income, value)


def get_user_last_transaction_id(user_id:int):
    with conn.cursor() as cur:
        cur.execute(
            f'''
               SELECT id FROM transaction
               WHERE user_id = {user_id}
               ORDER BY id DESC LIMIT 1
            '''
        )
        return cur.fetchone()[0]
