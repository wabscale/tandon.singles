from functools import wraps

from flask import request
from flask_login import current_user

from bigsql import bigsql
from .forms import FollowForm, TagForm
from ..app import db


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
    f=db.query('Follow').find(
        followerUsername=form.id.data,
        followeeUsername=current_user.username,
        acceptedfollow=False
    ).first()

    if f is None:
        return

    if form.action.data == "accept":
        f.acceptedfollow=True
    elif form.action.data == "reject":
        db.session.delete(f)

    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@validate
def handle_tag(form):
    t=db.query('Tag').find(
        username=form.id.data,
        acceptedTag=False,
    ).first()

    if t is None:
        return

    if form.action.data == "accept":
        t.acceptedTag=True
    elif form.action.data == "reject":
        db.session.delete(t)

    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


def enable_notifications(func):
    @wraps(func)
    def handle_notifications(*args, **kwargs):
        ff=FollowForm()
        tf=TagForm()

        if request.method == 'POST':
            try:
                {
                    'follow': lambda: handle_follow(ff),
                    'tag'   : lambda: handle_tag(tf),
                    None    : lambda: None
                }[request.form.get('type', default=None)]()
            except KeyError:
                pass
        return func(*args, **kwargs)

    return handle_notifications
