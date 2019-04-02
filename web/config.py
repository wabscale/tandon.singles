import os
import sys


class Config:
    SECRET_KEY = os.urandom(32)
    DEBUG = False
    DOMAIN = 'https://tandon.singles'

    REGISTRATION_ENABLED = True

    MYSQL_DATABASE_USER = 'root'
    MYSQL_DATABASE_PASSWORD = 'password'
    MYSQL_DATABASE_HOST = 'db'
    MYSQL_DATABASE_DB = 'TS'

    VERBOSE_SQL_GENERATION = False
    VERBOSE_SQL_EXECUTION = True
    SQL_CACHE_TIMEOUT = 5

    UPLOAD_DIR = os.path.join(os.getcwd(), '.data/uploads')
    LOG_DIR = os.path.join(os.getcwd(), '.data/log')

    DB_LOG_FILE = os.path.join(LOG_DIR, 'db_log.log')

    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)
        if all('gunicorn' not in arg for arg in sys.argv):
            self.SECRET_KEY = 'DEBUG'
            self.DEBUG = True
            self.MYSQL_DATABASE_HOST = '127.0.0.1'
            self.DOMAIN = 'http://localhost:5000'
            self.VERBOSE_SQL_GENERATION = False
