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

    UPLOAD_FOLDER = 'web/.data/uploads'

    def __init__(self):
        if any('dev.py' in arg for arg in sys.argv):
            self.SECRET_KEY = 'DEBUG'
            self.MYSQL_DATABASE_HOST = 'localhost'
            self.DOMAIN = 'http://localhost:5000'
