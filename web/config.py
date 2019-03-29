import os
import sys


class Config:
    SECRET_KEY = os.urandom(32)
    DOMAIN = 'https://tandon.singles'

    REGISTRATION_ENABLED = True

    MYSQL_DATABASE_USER = 'root'
    MYSQL_DATABASE_PASSWORD = 'password'
    MYSQL_DATABASE_HOST = 'db'
    MYSQL_DATABASE_DB = 'TS'

    UPLOAD_DIR = 'web/.data/uploads'
    LOG_DIR = '.data/log'

    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)
        if any('dev.py' in arg for arg in sys.argv):
            self.SECRET_KEY = 'DEBUG'
            self.MYSQL_DATABASE_HOST = 'localhost'
            self.DOMAIN = 'http://localhost:5000'
