from decimal import Decimal

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="moneyflow",
    user="postgres",
    password="postgres",
)
conn.autocommit = True


# cur = conn.cursor()

# cur.execute('select * from "user";')
# # cur.execute('insert to "user" (telegram_id), ({})'.format())
# print(*cur.fetchall())
# # print(*cur.fetchone())

# cur.close()


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
            WHERE telegram_id = {telegram_id};
            '''
        )
        return cur.fetchone()[0]


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

if __name__ == '__main__':
    user_id = add_user(telegram_id=5679)
    print(user_id)
    conn.close()
