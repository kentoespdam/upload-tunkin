import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from pymysql.cursors import DictCursor
from sqids import Sqids

from app.core.log_loader import setup_logging

load_dotenv()

setup_logging()

LOGGER = logging.getLogger(os.getenv('APP_NAME', "app"))
fastapi_logger = logging.getLogger("watchfiles")
fastapi_logger.setLevel(logging.ERROR)


class Config:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASS', '')
        self.database = os.getenv('DB_NAME', '')
        self.kpi_table_name = os.getenv('KPI_TABLE_NAME', '')
        self.charset = 'utf8mb4'
        self.cursorclass = DictCursor
        self.jwt_secret_key = os.getenv('JWT_SECRET_KEY', 'your_secret_key')
        self.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.jwt_access_token_expire_minutes = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30))
        self.jwt_client_id = os.getenv('JWT_CLIENT_ID', 'upload-tunkin-client')
        self.jwt_client_secret = os.getenv('JWT_CLIENT_SECRET', 'your_client_secret')
        self.sqids_alphabet = os.getenv('SQIDS_ALPHABET', '')
        self.sqids_min_length = int(os.getenv('SQIDS_MIN_LENGTH', 6))


class SqidsHelper:
    def __init__(self, config: Config = Config()):
        self.sqids = Sqids(alphabet=config.sqids_alphabet, min_length=config.sqids_min_length)

    def encode(self, number: int) -> str:
        now = datetime.now()
        return self.sqids.encode([now.second, number, now.month, now.day, now.minute, now.microsecond])

    def decode(self, hashid: str) -> int:
        decoded = self.sqids.decode(hashid)
        return decoded[1]


TIMEZONE = pytz.timezone('Asia/Jakarta')
