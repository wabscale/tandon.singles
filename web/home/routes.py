from functools import wraps

import pymysql.cursors
from flask import flash, render_template, Blueprint, send_from_directory, request
from flask_login import current_user, login_required

import bigsql
from .forms import PostForm, DeleteForm, CommentForm, LikeForm
from .. import models
from ..app import app, db
from ..notifications import enable_notifications

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
    if ext == 'invalid':
        flash('png, jpg and gifs only plz ;(')
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
    c=db.query('Comment').new(
        username=current_user.username,
        photoID=photo.photoID,
        commentText=form.content.data
    )
    db.session.add(c)
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@validate
def handle_like(form):
    like=db.query('Liked').find(
        username=current_user.username,
        photoID=form.id.data
    ).first()

    if like is None:  # like
        db.query('Liked').new(
            username=current_user.username,
            photoID=form.id.data
        )
    else:  # unlike
        db.session.delete(like)

    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


def handle_photos(func):
    @wraps(func)
    def handler(*args, **kwargs):
        if request.method == 'POST':
            delete_form=DeleteForm()
            comment_form=CommentForm()
            like_form=LikeForm()
            try:
                {
                    'delete' : lambda: handle_delete(delete_form),
                    'comment': lambda: handle_comment(comment_form),
                    'like'   : lambda: handle_like(like_form)
                }[request.form.get('action', default=None)]()
            except KeyError as e:
                print('KeyError', e)
            except pymysql.err.IntegrityError:
                db.session.rollback()
        return func(*args, **kwargs)

    return handler


@home.route('/', methods=['GET', 'POST'])
@login_required
@enable_notifications
@handle_photos
def index():
    post_form=PostForm()

    try:
        {
            'post': lambda: handle_post(post_form),
        }[request.form.get('action', default=None)]()
    except KeyError as e:
        print('KeyError', e)
    except pymysql.err.IntegrityError:
        db.session.rollback()

    group_choices=set()
    group_choices.add(('', '---'))
    for group in db.query('CloseFriendGroup').find(
            groupOwner=current_user.username
    ).all():
        group_choices.add((group.groupName,) * 2)
    for b in current_user.belongs:
        group_choices.add((b.groupName,) * 2)
    post_form.group.choices=list(group_choices)

    return render_template(
        'home/index.html',
        post_form=post_form,
        photos=models.Photo.visible_to(current_user.username)
    )


@home.route('/img/<path:path>')
# @login_required
def img(path):
    return send_from_directory(
        app.config['UPLOAD_DIR'],
        path
    )
