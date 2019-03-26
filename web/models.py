from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from werkzeug import secure_filename
import os

from .app import db, app


def est_now():
    """
    Get EST now datetime object.
    :return:
    """
    return datetime.now(tz=timezone(offset=timedelta(hours=-5)))


class struct:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self.__setattr__(key, val)


class BaseModel:
    """
    All subclasses just need to define their own __table__
    to be the name of the table (along with any other convince
    methods).
    """
    __table__ = None
    __schemata__ = 'TS'
    __columns__ = None

    def __init__(self, *args):
        """
        Will fetch names of columns when initially called.

        :param list args: list of data members for object in order they were created.
        """
        if self.__columns__ is None:
            if self.__table__ is None:
                raise NotImplementedError('__table__ not implemented')

            with db.connect() as cursor:
                _attrs = cursor.execute(
                    'SELECT COLUMN_NAME FROM information_schema.columns '
                    'WHERE TABLE_SCHEMATA = %s AND TABLE_NAME = %s;',
                    (self.__schemata__, self.__table__)
                )
                cursor.fetchall()
                self.__columns__ = list(map(lambda x: x[0], _attrs))

        for key, val in zip(self.__columns__, args):
            self.__setattr__(key, val)


class Photo(BaseModel):
    __table__ = 'Photo'

    @staticmethod
    def create(image, owner, caption, all_followers):
        """

        :param image:
        :param owner:
        :param caption:
        :param all_followers:
        :return: new photo object
        """
        file_path=os.path.join(
            app.config['UPLOAD_FOLDER'],
            secure_filename(image.data.filename)
        )
        image.data.save()
        with db.connect() as cursor:
            cursor.execute(
                'INSERT INTO Photo (photoOwner, timestamp, filePath, caption, allFollowers) '
                'VALUES (%s, %s, %s, %s, %i)',
                (owner.username, str(est_now()), file_path, caption, all_followers)
            )

    @staticmethod
    def get_photos_by_owner(username):
        """
        Generates list of Photo object owner by username

        :param str username: owner of photos being selected
        :return: [
            Photo,
            ...
        ]
        """
        with db.connect() as cursor:
            cursor.execute(
                'SELECT * FROM Photos '
                'JOIN Person '
                'WHERE Person.owner = %s',
                (username,)
            )
            return [
                Photo(*photo)
                for photo in cursor.fetchall()
            ]


class User:
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """
    def __init__(self, username):
        self.username, self.password = (None,)*2
        with db.connect() as cursor:
            cursor.execute(
                'SELECT username, password '
                'FROM Person '
                'WHERE username = %s;',
                (username,)
            )
            res = cursor.fetchone()
            if res is not None:
                self.username, self.password = res

    def check_password(self, pword):
        return check_password_hash(self.password, pword) if self.username is not None else False

    def is_authenticated(self):
        return self.username is not None

    def is_active(self):
        return True

    def is_anonymous(self):
        return self.username is None

    def get_id(self):
        return self.username

    def get_photos(self):
        """
        :return list: Photo object owned by self.username
        """
        return Photo.get_photos_by_owner(self.username)

    @staticmethod
    def create(username, password):
        """
        Make new user from username, password.

        :param str username:
        :param str password:
        :return User: new User object
        """
        with db.connect() as cursor:
            cursor.execute(
                'INSERT INTO Person (username, password) VALUES '
                '(%s, %s);',
                (username, generate_password_hash(password),)
            )
        return User(username)
