import os

import pandas as pd
import pymysqlpool
from pymysql.cursors import DictCursor

from app.core.config import LOGGER, SqidsHelper
from app.models.response_model import BasePageResponse


def get_connection_pool() -> pymysqlpool.Connection:
    config = {
        "size": 2,
        "maxsize": 10,
        "pre_create_num": 2,
        "name": "kepegawaian-pool",
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT') or 3306),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,
    }

    return pymysqlpool.ConnectionPool(**config).get_connection()


class DatabaseHelper:
    def __init__(self):
        self.sqids = SqidsHelper()

    @staticmethod
    def fetch_data(query: str, params: tuple = ()):
        connection = get_connection_pool()
        try:
            with get_connection_pool() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    column = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return pd.DataFrame(rows, columns=column)
        finally:
            connection.close()

    @staticmethod
    def fetch_tuple_data(query: str, params: tuple = (), fetchone: bool = False):
        connection = get_connection_pool()
        try:
            with get_connection_pool() as conn:
                with conn.cursor(cursor=DictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone() if fetchone else cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def save_update(query: str, data: list):
        with get_connection_pool() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.executemany(query, data)
                    affected = cursor.rowcount
                    LOGGER.info(f"{affected} rows affected")
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    LOGGER.error(e)

    @staticmethod
    def save_update_single(query: str, data: tuple):
        with get_connection_pool() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(query, data)
                    affected = cursor.rowcount
                    LOGGER.info(f"{affected} rows affected")
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    LOGGER.error(e)

    def fetch_page(self, query: str, params: tuple = (), page: int = 1, page_size: int = 10) -> BasePageResponse:
        count = self.fetch_count(query, params)

        offset = (page - 1) * page_size
        query += " LIMIT %s OFFSET %s"
        paginated_params = params + (page_size, offset)
        rows = self.fetch_data(query, paginated_params)
        rows['id'] = rows['id'].apply(lambda x: self.sqids.encode(x)).astype(str)

        return BasePageResponse(
            content=rows.to_dict("records"),
            total=count,
            is_first=page == 1,
            is_last=offset + page_size >= count,
            page=page,
            page_size=page_size,
            total_pages=round(count / page_size) + (1 if count % page_size > 0 else 0)
        )

    @staticmethod
    def fetch_count(query: str, params: tuple = ()) -> int:
        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
        try:
            with get_connection_pool() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_query, params)
                    result = cursor.fetchone()
                    if result:
                        return result['total']
        except Exception as e:
            LOGGER.error(e)

        return 0
