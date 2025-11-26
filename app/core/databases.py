import os

import pandas as pd
import pymysqlpool
from pymysql.cursors import DictCursor

from app.core.config import LOGGER, SqidsHelper
from app.models.response_model import BasePageResponse


def get_connection_pool() -> pymysqlpool.Connection:
    config = {
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

    return pymysqlpool.ConnectionPool(**config).get_connection()


class DatabaseHelper:
    def __init__(self):
        self.sqids = SqidsHelper()
        self.con = get_connection_pool()

    def fetch_data(self, query: str, params: tuple = ()):
        try:
            with self.con as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    column = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return pd.DataFrame(rows, columns=column)
        except Exception as e:
            LOGGER.error(e)
        finally:
            cursor.close()

    def fetchone(self, query: str, params: tuple = ()):
        try:
            with self.con as conn:
                with conn.cursor(cursor=DictCursor) as cursor:
                    cursor.execute(query, params)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchone()
                    if not rows:
                        return None
                    return dict(zip(columns, rows))
        except Exception as e:
            LOGGER.error(e)
        finally:
            cursor.close()

    def fetch_tuple_data(self, query: str, params: tuple = (), fetchone: bool = False):
        try:
            with self.con as conn:
                with conn.cursor(cursor=DictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone() if fetchone else cursor.fetchall()
        except Exception as e:
            LOGGER.error(e)
        finally:
            cursor.close()

    def save_update(self, query: str, data: list):
        try:
            with self.con as conn:
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
        finally:
            cursor.close()

    def save_update_single(self, query: str, data: tuple):
        try:
            with self.con as conn:
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
        finally:
            cursor.close()

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

    def fetch_count(self, query: str, params: tuple = ()) -> int:
        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS subquery"
        try:
            with self.con as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_query, params)
                    result = cursor.fetchone()
                    if result:
                        return result['total']
        except Exception as e:
            LOGGER.error(e)
        finally:
            cursor.close()

        return 0
