import logging
import os

from dotenv import load_dotenv
from pymysql.cursors import DictCursor

from app.core.log_loader import setup_logging

load_dotenv()

setup_logging()
LOGGER = logging.getLogger('cronjob')
schedule_logger = logging.getLogger("schedule")
fastapi_logger = logging.getLogger("watchfiles")
fastapi_logger.setLevel(logging.ERROR)


class Config:
    def __init__(self):
        self.lokasi = os.getenv("LOKASI")
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASS', '')
        self.database = os.getenv('DB_NAME', '')
        self.charset = 'utf8mb4'
        self.cursorclass = DictCursor
