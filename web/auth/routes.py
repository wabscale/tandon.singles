import string

import pymysql
from flask import redirect, url_for, flash, render_template, Blueprint
from flask_login import current_user, login_user, logout_user, login_required

from .forms import LoginForm, RegistrationForm
from ..app import app
from ..models import Person

auth = Blueprint('auth', __name__, url_prefix='/auth')


class InvalidUsername(Exception):
    pass


def check_username(username):
    return all(
        c in string.ascii_letters or c in string.digits or c in '!#$&*+-.:<=>?@[]^_|~'
        for c in username
    )


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    form = RegistrationForm()
    registration_enabled = app.config['REGISTRATION_ENABLED']

    if not registration_enabled:
        for field in form:
            field.render_kw = {'disabled': ''}
        return render_template('auth/register.html', form=form)

    if form.validate_on_submit():
        try:
            if not check_username(form.username.data):
                raise InvalidUsername()
            u = Person.create(form.username.data, form.password.data)
            login_user(u)
            return redirect(url_for('home.index'))
        except pymysql.err.IntegrityError:
            flash('Username already in use')
        except InvalidUsername:
            flash('{} contains invalid characters'.format(
                form.username.data
            ))

    return render_template(
        'auth/register.html',
        form=form,
        registration_enabled=registration_enabled
    )


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    form = LoginForm()
    if form.validate_on_submit():
        u = Person.get(form.username.data)
        if u is None or not u.check_password(form.password.data):
            flash('Invalid username or password')
            return render_template('auth/login.html', form=form)
        login_user(u)
        return redirect(url_for('home.index'))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))
