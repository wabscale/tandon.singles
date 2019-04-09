import hashlib
import imghdr
import os
import tempfile
import time

from flask import flash
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

import bigsql
from .app import app, db
from . import home
from . import users


class Photo(bigsql.DynamicModel):
    @property
    def image_link(self):
        if self.filePath is None:
            return ''
        dir_name, image_name=os.path.split(self.filePath)
        _, dir_name=os.path.split(dir_name)
        return '/img/{}/{}'.format(dir_name, image_name)

    @staticmethod
    def create(form):
        """
        :param image:
        :param owner:
        :param caption:
        :param all_followers:
        :return: new photo object
        """

        filestream=form.image.data.stream
        with tempfile.NamedTemporaryFile() as f:
            f.write(filestream.read())
            filestream.seek(0)
            ext=imghdr.what(f.name)

        if ext not in ('png', 'jpeg', 'gif'):
            # handle invalid file
            return ext

        sha256=lambda s: hashlib.sha256(s.encode()).hexdigest()

        filename='{}.{}'.format(sha256('{}{}{}{}'.format(
            str(time.time()),
            form.caption.data,
            current_user.username,
            os.urandom(0x10)
        )), ext)

        filedir=os.path.join(
            app.config['UPLOAD_DIR'],
            sha256(current_user.username),
        )

        filepath=os.path.join(
            filedir,
            filename
        )

        os.makedirs(filedir, exist_ok=True)

        form.image.data.save(filepath)

        photo=db.query('Photo').new(
            allFollowers=form.public.data,
            photoOwner=current_user.username,
            filePath=filepath,
            caption=form.caption.data,
        )

        if form.group.data:
            group=db.query('CloseFriendGroup').find(
                groupName=form.group.data
            ).first()

            if group.groupOwner != current_user.username and (group is None or not any(
                    group.groupName == g.groupName
                    for g in current_user.person.belongs
            )):
                flash('Unable to post to {}'.format(group.groupName))

            db.query('Share').new(
                groupName=group.groupName,
                groupOwner=group.groupOwner,
                photoID=photo.photoID
            )
        try:
            db.session.commit()
            return True
        except bigsql.big_ERROR:
            db.session.rollback()
            return False

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
        return db.query('Photo').find(
            photoOwner=username
        ).all()

    @staticmethod
    def visible_to(username):
        """
        Should give back all photo object that are visible to username

        TODO:
        need to make this order all photos by timestamp

        :return: [ Photo ]
        """
        u=db.query('Person').find(
            username=username
        ).first()

        photos = []
        photos.extend(u.photos)
        photos.extend(
            cfg.photos
            for cfg in CloseFriendGroup.find_groups(u)
        )
        photos.extend(
            f.public_photos
            for f in u.follow
        )

        return list(sorted(
            u.photos,
            key=lambda x: x.timestamp,
            reverse=True
        ))

    @property
    def delete_form(self):
        return home.forms.DeleteForm.populate(self)

    @property
    def comment_form(self):
        return home.forms.CommentForm.populate(self)



class CloseFriendGroup(bigsql.DynamicModel):
    @property
    def photos(self):
        return [
            share.photo
            for share in self.shares
        ]

    @staticmethod
    def find_groups(person):
        return [
            b.closefriendgroup[0]
            for b in person.belongs
        ] + [
            cfg
            for cfg in person.closefriendgroup
        ]


class Person(bigsql.DynamicModel):
    @property
    def follow_form(self):
        return users.forms.FollowForm.populate(self)


class User:
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """

    def __init__(self, username):
        self.username, self.password=(None,) * 2
        self.person=db.query('Person').find(username=username).first()
        if self.person is not None:
            self.username, self.password=self.person.username, self.person.password

    def check_password(self, pword):
        return check_password_hash(self.password, pword) if self.username is not None else False

    def is_authenticated(self):
        return self.person is not None

    def is_active(self):
        return True

    def is_anonymous(self):
        return self.person is None

    def get_id(self):
        return None if self.person is None else self.username

    def get_owned_photos(self):
        """
        :return list: Photo object owned by self.username
        """
        return Photo.owned_by(self.username)

    def get_feed(self):
        return Photo.visible_to(self.username)

    def follows(self, user):
        return db.sql.SELECTFROM(
            'Follow'
        ).WHERE(
            followerUsername=self.username
        ).AND(
            followeeUsername=user.username
        ).first() is not None or user.username == self.username

    @staticmethod
    def create(username, password):
        """
        Make new user from username, password.

        :param str username:
        :param str password:
        :return User: new User object
        """
        password=generate_password_hash(password)
        u=db.query('Person').new(
            username=username,
            password=password
        )
        db.session.add(u)
        try:
            db.session.commit()
        except bigsql.big_ERROR:
            db.session.rollback()
        return User(u.username)

    @staticmethod
    def get(username):
        u=User(username)
        return u if u.person is not None else None
