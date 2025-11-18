from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator, Optional, Union, Dict, Any

import numpy as np
import pandas as pd
import pymysql
import pymysqlpool

from app.core.config import LOGGER, Config

_config = Config()


class DatabaseConfig:
    """Database configuration manager."""

    __slots__ = ('host', 'port', 'user', 'password', 'database', 'charset', 'cursorclass')

    def __init__(self):
        self.host = _config.host
        self.port = _config.port
        self.user = _config.user
        self.password = _config.password
        self.database = _config.database
        self.charset = _config.charset
        self.cursorclass = _config.cursorclass

    def to_dict(self) -> dict:
        return {attr: getattr(self, attr) for attr in self.__slots__}


@lru_cache(maxsize=2)  # Cache for both autocommit and non-autocommit pools
def _create_connection_pool(autocommit: bool = False) -> pymysqlpool.ConnectionPool:
    """Create and cache connection pool."""
    config = DatabaseConfig()

    return pymysqlpool.ConnectionPool(
        size=10,
        maxsize=20,  # Increased maxsize for better concurrency
        pre_create_num=3,
        name=f'db_pool_autocommit_{autocommit}',
        autocommit=autocommit,
        **config.to_dict()
    )


@contextmanager
def database_connection(autocommit: bool = False) -> Iterator[pymysql.connections.Connection]:
    """
    Context manager for database connections with proper cleanup.

    Usage:
    with database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
    """
    conn = None
    try:
        pool = _create_connection_pool(autocommit)
        conn = pool.get_connection()
        conn.ping(reconnect=True)  # Ensure connection is alive
        yield conn
    except pymysql.MySQLError as e:
        # Clear cache on connection error
        _create_connection_pool.cache_clear()
        raise pymysql.MySQLError(f"Database connection error: {e}") from e
    finally:
        if conn:
            conn.close()  # Return to pool


@contextmanager
def _database_cursor(autocommit: bool = False):
    """Context manager untuk handle database cursor dengan automatic cleanup."""
    conn = None
    cursor = None
    try:
        conn = _create_connection_pool(autocommit).get_connection()
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_data(
        query: str,
        params: Optional[Union[tuple, dict, list]] = None,
        chunksize: Optional[int] = None,
        dtype: Optional[Dict[str, Any]] = None,
        parse_dates: Optional[list] = None,
        index_col: Optional[Union[str, list]] = None
) -> pd.DataFrame:
    """
    Fetch data dari database dan return sebagai pandas DataFrame dengan berbagai optimasi.

    Parameters:
    -----------
    query : str
        SQL query untuk dieksekusi
    params : tuple, dict, or list, optional
        Parameters untuk query parameterized
    chunksize : int, optional
        Jika specified, fetch data dalam chunks (untuk data besar)
    dtype : dict, optional
        Data types untuk kolom spesifik {col: dtype}
    parse_dates : list, optional
        List of columns to parse as dates
    index_col : str or list, optional
        Column(s) to set as index

    Returns:
    --------
    pd.DataFrame
        Hasil query sebagai DataFrame

    Raises:
    -------
    pymysql.MySQLError: Jika terjadi error database
    ValueError: Jika query tidak valid
    """
    if not query or not query.strip():
        raise ValueError("Query tidak boleh kosong")

    start_time = pd.Timestamp.now()

    try:
        with _database_cursor() as cursor:
            # Execute query
            cursor.execute(query, params or ())

            # Get column names
            if not cursor.description:
                return pd.DataFrame()

            columns = [column[0] for column in cursor.description]

            # Fetch data based on chunksize
            if chunksize:
                return _fetch_data_chunked(cursor, columns, chunksize, dtype, parse_dates, index_col)
            else:
                rows = cursor.fetchall()
                return _create_dataframe(rows, columns, dtype, parse_dates, index_col, start_time)

    except pymysql.MySQLError as e:
        LOGGER.error(f"Database error dalam fetch_data: {e}")
        raise
    except Exception as e:
        LOGGER.error(f"Unexpected error dalam fetch_data: {e}")
        raise


def fetch_count_data(query: str, params: Optional[Union[tuple, dict]] = None) -> int:
    """
    Optimized function to fetch count data from database.

    Parameters:
    query (str): SQL query, preferably COUNT(*) queries
    params (tuple | dict): Query parameters

    Returns:
    int: Count result, returns 0 if no results

    Examples:
    >>> fetch_count_data("SELECT COUNT(*) FROM users WHERE active = %s", (True,))
    42
    """
    with database_connection() as conn:
        with conn.cursor(cursor=pymysqlpool.Cursor) as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            if not result:
                return 0

            # Efficiently extract first value regardless of result type
            return result[0] if cursor.description else 0


def _fetch_data_chunked(cursor, columns: list, chunksize: int, dtype, parse_dates, index_col) -> pd.DataFrame:
    """Fetch data dalam chunks untuk memory efficiency."""
    chunks = []
    while True:
        rows = cursor.fetchmany(chunksize)
        if not rows:
            break

        chunk_df = _create_dataframe(rows, columns, dtype, parse_dates, index_col)
        chunks.append(chunk_df)

    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def _create_dataframe(rows: list, columns: list, dtype, parse_dates, index_col, start_time=None) -> pd.DataFrame:
    """Create DataFrame dari rows dengan optimasi memory."""
    if not rows:
        return pd.DataFrame(columns=columns)

    # Create DataFrame
    df = pd.DataFrame(rows, columns=columns)

    # Apply data type optimizations
    df = _optimize_dataframe_dtypes(df, dtype, parse_dates)

    # Set index jika specified
    if index_col:
        df.set_index(index_col, inplace=True)

    # Log performance jika start_time provided
    if start_time:
        execution_time = (pd.Timestamp.now() - start_time).total_seconds()
        LOGGER.debug(f"Fetched {len(df)} rows in {execution_time:.3f}s")

    return df


def _optimize_dataframe_dtypes(df: pd.DataFrame, dtype: Optional[dict] = None,
                               parse_dates: Optional[list] = None) -> pd.DataFrame:
    """Optimize DataFrame data types untuk reduce memory usage."""
    result = df.copy()

    # Parse dates
    if parse_dates:
        for col in parse_dates:
            if col in result.columns:
                result[col] = pd.to_datetime(result[col], errors='coerce')

    # Apply specified dtypes
    if dtype:
        for col, col_dtype in dtype.items():
            if col in result.columns:
                try:
                    result[col] = result[col].astype(col_dtype)
                except (ValueError, TypeError):
                    # Fallback to object type jika conversion gagal
                    pass

    # Auto-optimize numeric columns
    result = _auto_optimize_numeric_dtypes(result)

    return result


def _auto_optimize_numeric_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Automatically optimize numeric data types."""
    result = df.copy()

    for col in result.select_dtypes(include=[np.number]).columns:
        col_min = result[col].min()
        col_max = result[col].max()

        # Optimize integer columns
        if result[col].dtype == np.int64:
            if col_min >= 0:
                if col_max < np.iinfo(np.uint8).max:
                    result[col] = result[col].astype(np.uint8)
                elif col_max < np.iinfo(np.uint16).max:
                    result[col] = result[col].astype(np.uint16)
                elif col_max < np.iinfo(np.uint32).max:
                    result[col] = result[col].astype(np.uint32)
            else:
                if col_min > np.iinfo(np.int8).min and col_max < np.iinfo(np.int8).max:
                    result[col] = result[col].astype(np.int8)
                elif col_min > np.iinfo(np.int16).min and col_max < np.iinfo(np.int16).max:
                    result[col] = result[col].astype(np.int16)
                elif col_min > np.iinfo(np.int32).min and col_max < np.iinfo(np.int32).max:
                    result[col] = result[col].astype(np.int32)

    return result


def save_update(query: str, data: list):
    with database_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.executemany(query, data)
                affected = cursor.rowcount
                LOGGER.info(f"{affected} rows affected")
                conn.commit()
            except Exception as e:
                conn.rollback()
                LOGGER.error(e)


def save_update_single(query: str, data: tuple):
    with database_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(query, data)
                affected = cursor.rowcount
                LOGGER.info(f"{affected} rows affected")
                conn.commit()
            except Exception as e:
                conn.rollback()
                LOGGER.error(e)
