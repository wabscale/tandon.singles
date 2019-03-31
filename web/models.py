from werkzeug.security import generate_password_hash, check_password_hash

import tempfile
import hashlib
import imghdr
import time
import os

from .orm import Sql, BaseModel, utils
from .app import app


class Person(BaseModel):
    __table__ = 'Person'
    __relationships__ = {
        'photos': 'Photo'
    }


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

        filestream = image.data.stream
        with tempfile.NamedTemporaryFile() as f:
            f.write(filestream.read())
            filestream.seek(0)
            ext = imghdr.what(f.name)

        if ext not in ('png', 'jpeg', 'gif'):
            # handle invalid file
            return ext

        sha256 = lambda s: hashlib.sha256(s.encode()).hexdigest()

        filename = '{}.{}'.format(sha256('{}{}{}{}'.format(
            str(time.time()), caption, owner, os.urandom(0x10)
        )), ext)

        filedir = os.path.join(
            app.config['UPLOAD_DIR'],
            sha256(owner),
        )

        filepath = os.path.join(
            filedir,
            filename
        )

        os.makedirs(filedir, exist_ok=True)

        image.data.save(filepath)

        Sql.INSERT(
            allFollowers=all_followers,
            photoOwner=owner.username,
            timestamp=str(est_now()),
            filePath=filepath,
            caption=caption,
        ).INTO('Photo')()

    @staticmethod
    def owned_by(username):
        """
        Generates list of Photo object owner by username

        :param str username: owner of photos being selected
        :return: [
            Photo,
            ...
        ]
        """
        return [
            Sql.SELECTFROM('Photos').WHERE(owner=username)
        ]

    @staticmethod
    def visible_to(username):
        """
        Should give back all photo object that are visible to username

        TODO:
        need to make this order all photos by timestamp

        :return: [ Photo ]
        """
        return sorted(list(
            # photos that are in close friend groups that username is in
            Sql.SELECTFROM('Photos').JOIN('Share', 'CloseFriendGroup', 'Belong').WHERE(
                username=username
            )
        ) + list(
            # subscibed photos
            Sql.SELECTFROM('Photos').JOIN('Follow').WHERE(
                followeeUsername=username,
                acceptedfollow=True
            )
        ) + list(
            # users photos
            Sql.SELECTFROM('Photos').JOIN('Person').WHERE(
                username=username
            )
        ), key=lambda photo: photo.timestamp)


class User:
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """
    def __init__(self, username):
        self.username, self.password = (None,)*2
        self.person = Query(Person).find(username=username).first()
        if self.person is not None:
            self.username, self.password = self.person.username, self.person.password

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

    def get_owned_photos(self):
        """
        :return list: Photo object owned by self.username
        """
        return Photo.owned_by(self.username)

    def get_feed(self):
        return Photo.visible_to(self.username)

    @staticmethod
    def create(username, password):
        """
        Make new user from username, password.

        :param str username:
        :param str password:
        :return User: new User object
        """
        password = generate_password_hash(password)
        print(password)
        Sql.INSERT(
            username=username,
            password=password
        ).INTO('Person').do()
        return User(username)


# p = Query(Photo).new(photoOwner='admin')
# print(p)

# print(app.config['MYSQL_DATABASE_HOST'])
# User.create('admin', 'password')
# p = Query(Person).find(username='admin').first()
# print(list(p.photos))
# print(User('admin'))
# p = Sql.SELECTFROM('Person').WHERE(username='admin').execute()[0]
# print(p.photos)
# print(Sql.UPDATE('Photo').SET(photoID=1).WHERE(photoID=2).gen())
# print(*Sql.SELECT('username').FROM('Person').WHERE(username='j'))
# print(e.INSERT(username='d',password='pwrod').INTO('Person').execute())
