from functools import wraps

import pymysql.cursors
from flask import render_template, Blueprint, redirect, request, flash
from flask_login import current_user, login_required

from bigsql import bigsql
from .forms import FollowForm, SearchForm
from .. import home
from .. import models
from ..app import db
from ..notifications import enable_notifications

users=Blueprint('users', __name__, url_prefix='/u')


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
def handle_follow(form):
    db.query('Follow').new(
        followerUsername=current_user.username,
        followeeUsername=form.id.data,
        acceptedfollow=False
    )
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@validate
def handle_unfollow(form):
    f=db.query('Follow').find(
        followerUsername=current_user.username,
        followeeUsername=form.id.data,
        acceptedfollow=True
    ).first()
    if f is not None:
        db.session.delete(f)
        try:
            db.session.commit()
        except bigsql.big_ERROR:
            db.session.rollback()
    else:
        flash('unable to unfollow')


@validate
def search_users(form):
    return db.query('Person').append_raw(
        'WHERE Person.username LIKE %s',
        ('%%{}%%'.format(form.content.data),)
    ).all()


def handle_users(func):
    @wraps(func)
    def handler(*args, **kwargs):
        follow_form=FollowForm()
        if request.method == 'POST':
            try:
                {
                    'follow'  : lambda: handle_follow(follow_form),
                    'unfollow': lambda: handle_unfollow(follow_form),
                    None      : lambda: None
                }[request.form.get('action', default=None)]()
            except KeyError:
                pass
            except pymysql.err.IntegrityError:
                db.session.rollback()
        return func(*args, **kwargs)

    return handler


@users.route('/', methods=['GET', 'POST'])
@login_required
@enable_notifications
@home.handle_photos
@handle_users
def index():
    search_form=SearchForm()

    persons=None

    if request.form.get('action', default=None) == 'search':
        persons=search_users(search_form)

    return render_template(
        'users/home.html',
        FollowForm=FollowForm,
        search_form=search_form,
        persons=persons if persons is not None else models.Person.query.all()
    )


@users.route('/<username>', methods=['GET', 'POST'])
@login_required
@enable_notifications
@home.handle_photos
@handle_users
def view(username):
    person=db.query('Person').find(
        username=username
    ).first()

    if person is None:
        return redirect('home.index')

    return render_template(
        'users/view.html',
        person=person,
        photos=db.sql.SELECTFROM('Photo').WHERE(
            photoOwner=person.username
        ).AND(
            allFollowers=True
        ).all()
    )
