from flask import redirect, url_for
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

from .routes import auth
from ..app import app


login_manager = LoginManager()
login_manager.init_app(app)


class User:
    def __init__(self, username):
        self.id=None
        self.username=None
        self.password=None
        with db.connect() as cursor:
            res=cursor.execute(
                'SELECT id, username, password FROM Person WHERE username = ?;',
                (username,)
            ).fetchone()
            if res is not None:
                self.id, self.username, self.password = res

    def check_password(self, pword):
        return check_password_hash(self.password, pword) if self.username is not None else False

    def is_authenticated(self):
        return self.username is not None

    def is_active(self):
        return True

    def is_anonymous(self):
        return self.username is None

    def get_id(self):
        return self.id


def create_user(self, username, password):
    with db.connect() as cursor:
        cursor.execute(
            'INSERT INTO Person (username, password) VALUES (?, ?);',
            (username, generate_password_hash(password),)
        )
        cursor.commit()
    return User(username)


@login_manager.user_loader
def load_user(username):
    with mysql.connect() as cursor:
        return cursor.execute(
            'SELECT username FROM users WHERE username = ?',
            (username,)
        ).fetchone()

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('auth.login'))
