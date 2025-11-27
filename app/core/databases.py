import os
from typing import Optional, Dict, Any

import pandas as pd
import pymysqlpool
from pymysql.cursors import DictCursor

from app.core.config import LOGGER, SqidsHelper
from app.models.response_model import BasePageResponse

_db_config = {
    "size": int(os.getenv('POOL_SIZE', 2)),
    "maxsize": int(os.getenv('POOL_SIZE', 5)),
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
db_pool = pymysqlpool.ConnectionPool(**_db_config)


class DatabaseHelper:
    def __init__(self):
        self.sqids = SqidsHelper()

    @staticmethod
    def fetch_data(query: str, params: tuple = ()):
        try:
            with db_pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    column = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return pd.DataFrame(rows, columns=column)
        except Exception as e:
            LOGGER.error(e)

    @staticmethod
    def fetchone(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        try:
            with db_pool.get_connection() as conn:
                with conn.cursor(cursor=DictCursor) as cursor:
                    cursor.execute(query, params)
                    rows = cursor.fetchone()
                    if not rows:
                        return None
                    return rows
        except Exception as e:
            LOGGER.error(e)

    @staticmethod
    def fetch_tuple_data(query: str, params: tuple = (), fetchone: bool = False):
        try:
            with db_pool.get_connection() as conn:
                with conn.cursor(cursor=DictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone() if fetchone else cursor.fetchall()
        except Exception as e:
            LOGGER.error(e)

    @staticmethod
    def save_update(query: str, data: list):
        try:
            with db_pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.executemany(query, data)
                        affected = cursor.rowcount
                        LOGGER.info(f"{affected} rows affected")
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        LOGGER.error(e)
        except Exception as e:
            LOGGER.error(e)

    @staticmethod
    def save_update_single(query: str, data: tuple):
        try:
            with db_pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.execute(query, data)
                        affected = cursor.rowcount
                        LOGGER.info(f"{affected} rows affected")
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        LOGGER.error(e)
        except Exception as e:
            LOGGER.error(e)

    def fetch_page(self, query: str, params: tuple = (), page: int = 1, page_size: int = 10) -> BasePageResponse:
        count = self.fetch_count(query, params)
        LOGGER.info(query % params)

        offset = (page - 1) * page_size
        query += " LIMIT %s OFFSET %s"
        paginated_params = params + (page_size, offset)
        rows = self.fetch_data(query, paginated_params)
        rows['id'] = rows['id'].apply(lambda x: self.sqids.encode(x)).astype(str)

        rows_len = len(rows)

        return BasePageResponse(
            content=rows.to_dict("records"),
            total=count,
            is_empty=rows_len == 0,
            total_elements=rows_len,
            is_first=page == 1,
            is_last=offset + page_size >= count,
            page=page,
            page_size=page_size,
            total_pages=round(count / page_size) + (1 if count % page_size > 0 else 0)
        )

    def fetch_count(self, query: str, params: tuple = ()) -> int:
        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
        try:
            result = self.fetchone(count_query, params)
            return result['total']
        except Exception as e:
            LOGGER.error(e)

        return 0
