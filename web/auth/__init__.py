from flask import redirect, url_for
from flask_login import LoginManager

from .routes import auth
from ..app import app
from ..models import Person

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(username):
    return Person.get(username)


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('auth.login'))
