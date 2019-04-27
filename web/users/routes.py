from functools import wraps

from flask import render_template, Blueprint, redirect, request
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
def search_users(form):
    return db.query('Person').append_raw(
        'WHERE Person.username LIKE %s',
        ('%%{}%%'.format(form.content.data),)
    ).all()


@users.route('/', methods=['GET', 'POST'])
@login_required
@enable_notifications
def index():
    follow_form=FollowForm()
    search_form=SearchForm()

    persons=None
    if request.method == 'POST':
        try:
            {
                'follow': lambda: handle_follow(follow_form),
                None    : lambda: None
            }[request.form.get('action', default=None)]()
        except KeyError:
            pass

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
def view(username):
    comment_form=home.forms.CommentForm()
    follow_form=FollowForm()

    person=db.query('Person').find(
        username=username
    ).first()

    if request.method == 'POST':
        {
            'follow' : lambda: handle_follow(follow_form),
            'comment': lambda: home.routes.handle_comment(comment_form),
            None     : lambda: None
        }[request.form.get('action', default=None)]()

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
