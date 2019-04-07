from flask import render_template, Blueprint
from flask_login import current_user, login_required

from ..models import User

users = Blueprint('users', __name__, url_prefix='/users')


@users.route('/<username>')
@login_required
def view_user(username):
    if current_user.is_authenticated():
        pass
    photos = list(User(username).person.photos)
    return render_template(
        'users/view.html',
        photos=photos
    )
