import os
from decimal import Decimal
from typing import Union

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


def add_transaction(user_id: int, value: Decimal):
    with conn.cursor() as cur:
        cur.execute(
            f'''
            INSERT INTO "transaction" (user_id, "value", date_time)
            VALUES ({user_id}, {value}, CURRENT_TIMESTAMP)
            '''
        )
    _update_user_balance(user_id, value)


def _update_user_balance(user_id: int, value: Decimal):
    balance = get_user_balance(user_id) + value

    with conn.cursor() as cur:
        cur.execute(
            f'''
            UPDATE "user"
            SET balance = {balance}
            WHERE id = {user_id}
            '''
        )


def get_transactions_history(
    user_id: int,
    limit: Union[int, None] = None,
    offset: Union[int, None] = None,
):
    sql_code = (f'''
       SELECT value, date_time FROM "transaction"
       WHERE user_id = {user_id}
       ORDER BY date_time DESC
    ''')

    if limit:
        sql_code += f'LIMIT {limit}\n'
    if offset:
        sql_code += f'OFFSET {offset}'

    with conn.cursor() as cur:
        cur.execute(sql_code)
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
            SELECT user_id, value
            FROM transaction
            WHERE id = {transaction_id}
            '''
        )
        user_id, value = cur.fetchone()

        cur.execute(
            f'''
            DELETE FROM transaction
            WHERE id = {transaction_id}
            '''
        )
        _update_user_balance(user_id, -value)


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


def get_transactions_count(user_id:int):
    with conn.cursor() as cur:
        cur.execute(
            f'''
            SELECT COUNT(*) FROM "transaction"
            WHERE user_id = {user_id}
            '''
        )
        return cur.fetchone()[0]
