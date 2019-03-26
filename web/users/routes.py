from flask import request, redirect, url_for, flash, render_template, Blueprint
from flask_login import current_user, login_required

from .forms import *

from ..app import app
from ..models import User

users = Blueprint('users', __name__, url_prefix='/users')


@users.route('/<username>')
@login_required
def view_user(username):
    if current_user.is_authenticated():
        pass
    photos = User(username).get_photos()
    return render_template(
        'users/view.html',
        photos=photos
    )
