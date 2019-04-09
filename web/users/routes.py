from flask import render_template, Blueprint, redirect, request
from flask_login import current_user, login_required

from .forms import FollowForm
from ..app import db
from .. import home

user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/<username>', methods=['GET', 'POST'])
@login_required
def view_user(username):
    comment_form=home.forms.CommentForm()
    follow_form=FollowForm()

    person = db.query('Person').find(
        username=username
    ).first()

    if request.method == 'POST':
        pass

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
