from unittest import TestCase
from source import conn, add_user
import random


def _run_sql(sql, fetch=False):
	with conn.cursor() as cur:
		cur.execute(sql)
		if fetch:
			return cur.fetchall()


class DBMethodsTestCase(TestCase):

	def setUp(self):
		pass

	def test_add_user_adds_user(self):
		sql_code = 'SELECT COUNT(*) FROM "user"'
		users_count = _run_sql(sql_code, True)[0][0]
		add_user(random.randint(100000, 999999))
		users_count_upd = _run_sql(sql_code, True)[0][0]
		self.assertEqual(users_count + 1, users_count_upd)
