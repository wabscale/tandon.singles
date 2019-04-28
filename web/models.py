import hashlib
import imghdr
import os
import time

from flask import flash
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

import bigsql
from . import home
from . import notifications
from . import users
from .app import app, db


class Share(bigsql.DynamicModel):
    @property
    def photo(self):
        return Photo.query.find(
            photoID=self.photoID
        ).first()

class Tag(bigsql.DynamicModel):
    @property
    def photo(self):
        p=Photo.query.find(
            photoID=self.photoID
        ).first()
        return p

    def to_form(self):
        form=notifications.TagForm()
        form.id.data=self.username
        return form


class Follow(bigsql.DynamicModel):
    def to_form(self):
        form=notifications.FollowForm()
        form.id.data=self.followerUsername
        return form


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

        try:
            ext=imghdr.what(
                '',
                form.image.raw_data[0].stream._file.getbuffer().tobytes()
            )
        except TypeError:
            return False

        if ext not in ('png', 'jpeg', 'gif'):
            # handle invalid file
            return 'invalid'

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

        caption=form.caption.data.split()

        tags, caption=Photo.parse_caption(caption)
        photo=db.query('Photo').new(
            allFollowers=form.public.data,
            photoOwner=current_user.username,
            filePath=filepath,
            caption=caption,
        )

        for tag in tags:
            db.query('Tag').new(
                username=tag,
                photoID=photo.photoID,
                acceptedTag=False
            )

        if form.group.data:
            group=db.query('CloseFriendGroup').find(
                groupName=form.group.data
            ).first()

            if group.groupOwner != current_user.username and (group is None or not any(
                    group.groupName == g.groupName
                    for g in current_user.belongs
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
    def parse_caption(caption):
        tags=[]
        rem=set()
        for index, word in enumerate(caption):
            if word.startswith('@'):
                username=word[1:]
                if Person.query.find(
                        username=username
                ).first() is not None:
                    rem.add(index)
                    tags.append(username)
        return tags, caption

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

        photos=[]
        photos.extend(u.photos)
        photos.extend(CloseFriendGroup.find_shared_photos(u))

        for f in filter(lambda x: x.acceptedfollow, u.follow):
            p=Person.query.find(
                username=f.followeeUsername
            ).first()
            photos.extend(filter(
                lambda x: x.allFollowers,
                p.photos
            ))

        return set(sorted(
            photos,
            key=lambda x: x.timestamp,
            reverse=True
        ))

    @property
    def delete_form(self):
        return home.forms.DeleteForm.populate(self)

    @property
    def comment_form(self):
        return home.forms.CommentForm.populate(self)

    @property
    def like_form(self):
        return home.forms.LikeForm.populate(self)


class CloseFriendGroup(bigsql.DynamicModel):
    @property
    def photos(self):
        return [
            share.photo
            for share in self.shares
        ]

    @staticmethod
    def find_shared_photos(person):
        """
        This will return photo object that have been
        shared in all groups that person belongs to.

        :param person: PersonModel
        :return: [PhotoModel]
        """

        for b in person.belongs:
            shares=CloseFriendGroup.query.find(
                groupName=b.groupName,
                groupOwner=b.groupOwner
            ).first().shares
            for s in shares:
                yield s.photo


class Person(bigsql.DynamicModel):
    """
    Base user class. Just give it a username, and it will attempt
    to load its information out of the database.
    """

    def check_password(self, pword):
        return check_password_hash(self.password, pword) if self.username is not None else False

    def is_authenticated(self):
        return self.person is not None

    def is_active(self):
        return True

    def is_anonymous(self):
        return self.person is None

    def get_id(self):
        return self.username

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
        return u

    def awaiting_accept(self, other):
        return db.query('Follow').find(
            followeeUsername=other.username,
            followerUsername=self.username,
            acceptedfollow=False
        ).first() is not None

    @staticmethod
    def get(username):
        return Person.query.find(username=username).first()

    @property
    def follow_form(self):
        return users.forms.FollowForm.populate(self)

    @property
    def notifications(self):
        return db.query('Tag').find(
            username=self.username,
            acceptedTag=False,
        ).all() + db.query('Follow').find(
            followeeUsername=self.username,
            acceptedfollow=False,
        ).all()
