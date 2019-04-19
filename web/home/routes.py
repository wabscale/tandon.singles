from flask import flash, render_template, Blueprint, send_from_directory, request
from flask_login import current_user, login_required
from functools import wraps

import bigsql

from .forms import PostForm, DeleteForm, CommentForm
from .. import models
from ..app import app, db

home=Blueprint('home', __name__, url_prefix='/')


def validate(func):
    """
    validates forms before executing func
    """
    @wraps(func)
    def wrapper(form):
        if form.validate_on_submit():
            return func(form)
    return wrapper


@validate
def handle_post(form):
    ext=models.Photo.create(
        form,
    )
    if isinstance(ext, str):
        flash('{} is not a valid image type ;('.format(ext))
    if not ext:
        flash('unable to post')

@validate
def handle_delete(form):
    photo=db.query('Photo').find(
        photoID=form.id.data
    ).first()
    if photo is None:
        flash('invalid photo')
        return
    if photo.photoOwner == current_user.username:
        db.session.delete(photo)
        try:
            db.session.commit()
        except bigsql.big_ERROR:
            db.session.rollback()
    else:
        flash('Unable to delete photo')


@validate
def handle_comment(form):
    photo=db.query('Photo').find(
        photoID=form.id.data
    ).first()
    if photo is None:
        flash('invalid photo')
        return
    c = db.query('Comment').new(
        username=current_user.username,
        photoID=photo.photoID,
        commentText=form.content.data
    )
    db.session.add(c)
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@home.route('/', methods=['GET', 'POST'])
@login_required
def index():
    post_form=PostForm()
    delete_form=DeleteForm()
    comment_form=CommentForm()

    post_form.group.choices=[('', '---')]
    post_form.group.choices.extend(
        (group.groupName,) * 2
        for group in db.query('CloseFriendGroup').find(
            groupOwner=current_user.username
        ).all()
    )
    post_form.group.choices.extend(
        models.CloseFriendGroup.find_groups(current_user)
    )

    if request.method == 'POST':
        {
            'post'   : lambda: handle_post(post_form),
            'delete' : lambda: handle_delete(delete_form),
            'comment': lambda: handle_comment(comment_form),
            None     : lambda: None
        }[request.form.get('action', default=None)]()

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
