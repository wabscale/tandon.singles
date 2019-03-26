from flask import request, redirect, url_for, flash, render_template, Blueprint
from flask_login import current_user, login_user, logout_user, login_required
import pymysql

from .forms import PostForm

from ..app import app
from ..models import User

home = Blueprint('home', __name__, url_prefix='/')


@home.route('/')
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        pass  # handle post
    return render_template(
        'home/index.html',
        form=form
    )
