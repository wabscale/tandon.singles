from flask import flash, render_template, Blueprint, send_from_directory
from flask_login import current_user, login_required

from .forms import PostForm, DeleteForm
from ..app import app, db
from .. import models

import bigsql

home = Blueprint('home', __name__, url_prefix='/')


@home.route('/', methods=['GET', 'POST'])
@login_required
def index():
    post_form = PostForm()
    delete_form = DeleteForm()

    post_form.group.choices = [('', '---')]
    post_form.group.choices.extend(
        (group.groupName,)*2
        for group in db.query('CloseFriendGroup').find(
            groupOwner=current_user.username
        ).all()
    )
    post_form.group.choices.extend(map(
        lambda belongs: (
            belongs.closefriendsgroups[0].groupName,
        )*2,
        current_user.person.belongs
    ))

    if post_form.validate_on_submit():
        ext = models.Photo.create(
            post_form,
        )
        if isinstance(ext, str):
            flash('{} is not a valid image type ;('.format(ext))
        if not ext:
            flash('unable to post')

    if delete_form.validate_on_submit():
        photo = db.query('Photo').find(
            photoID=delete_form.photoid.data
        ).first()
        if photo.photoOwner == current_user.username:
            db.session.delete(photo)
            try:
                db.session.commit()
            except bigsql.big_ERROR:
                db.session.rollback()
        else:
            flash('Unable to delete photo')

    return render_template(
        'home/index.html',
        form=post_form,
        photos=models.Photo.visible_to(current_user.username)
    )


@home.route('/img/<path:path>')
@login_required
def img(path):
    return send_from_directory(
        app.config['UPLOAD_DIR'],
        path
    )
