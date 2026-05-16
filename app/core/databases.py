import os
from typing import Optional, Dict, Any

import pandas as pd
import pymysqlpool
from pymysql.cursors import DictCursor

from app.core.config import LOGGER
from app.models.response_model import BasePageResponse

# Module-level pool — created once on first use, reused across all calls.
_pool: Optional[pymysqlpool.ConnectionPool] = None


def _get_pool() -> pymysqlpool.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = pymysqlpool.ConnectionPool(
            size=int(os.getenv('POOL_SIZE', 2)),
            maxsize=int(os.getenv('POOL_SIZE', 5)),
            pre_create_num=2,
            name="kepegawaian-pool",
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT') or 3306),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4',
            cursorclass=DictCursor,
        )
    return _pool


def _get_connection() -> pymysqlpool.Connection:
    return _get_pool().get_connection()


class DatabaseHelper:
    def __init__(self):
        pass

    @staticmethod
    def fetch_data(query: str, params: tuple = ()):
        try:
            with _get_connection() as conn:
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
            with _get_connection() as conn:
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
            with _get_connection() as conn:
                with conn.cursor(cursor=DictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone() if fetchone else cursor.fetchall()
        except Exception as e:
            LOGGER.error(e)

    @staticmethod
    def save_update(query: str, data: list):
        """Execute a batch INSERT/UPDATE statement.

        For INSERT ... ON DUPLICATE KEY UPDATE, MySQL's cursor.rowcount returns
        2 per new row (1 for INSERT + 1 for internal "delete" of old row) and 1 per
        updated row — not the number of rows processed. We return the actual number
        of rows in the batch instead, which is the meaningful count for callers
        like KPIRepository.upsert_batch().
        """
        try:
            with _get_connection() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.executemany(query, data)
                        LOGGER.info(f"{len(data)} rows in batch")
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        LOGGER.error(e)
        except Exception as e:
            LOGGER.error(e)
        return len(data)

    @staticmethod
    def save_update_single(query: str, data: tuple):
        """Execute a single INSERT/UPDATE statement.

        Returns 1 on success (single row processed), matching the number of
        records passed in for single-record operations.
        """
        try:
            with _get_connection() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.execute(query, data)
                        LOGGER.info(f"1 row affected")
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        LOGGER.error(e)
        except Exception as e:
            LOGGER.error(e)
        return 1

    def fetch_page(self, query: str, params: tuple = (), page: int = 1, page_size: int = 10) -> BasePageResponse:
        count = self.fetch_count(query, params)

        offset = (page - 1) * page_size
        query += " LIMIT %s OFFSET %s"
        paginated_params = params + (page_size, offset)
        rows = self.fetch_data(query, paginated_params)

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
            result = self.fetchone(count_query, params)
            return result['total']
        except Exception as e:
            LOGGER.error(e)

        return 0
