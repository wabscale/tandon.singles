from flask import request, redirect, url_for, flash, render_template, Blueprint
from flask_login import current_user, login_user, logout_user, login_required

from .forms import LoginForm, RegistrationForm

from ..app import db, app
from . import create_user, User

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()

    if not app.config['REGISTRATION_OPEN']:
        for field in form:
            field.render_kw={'disabled':''}
        return render_template('auth/register.html', form=form)

    if form.validate_on_submit():
        try:
            u=create_user(form.username.data, form.password.data)
            login_user(u)
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already in use')
            return render_template('auth/register.html', form=form)
    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        u = User(username)
        if u is None or not u.check_password(form.password.data):
            flash('Invalid username or password')
            return render_template('auth/login.html', form=form)
        login_user(u)
        return redirect(url_for('index'))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
