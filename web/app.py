from flask import Flask, render_template, request, redirect, g, Blueprint, send_from_directory
from flask_login import current_user, login_required
from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect
from flaskext.mysql import MySQL

from .config import Config

host = '0.0.0.0'
port = 5000

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config())

Bootstrap(app)
CSRFProtect(app)
db = MySQL(app)

# register blueprints
from .auth import auth
from .users import users
from .home import home
from .api import api

list(map(app.register_blueprint, (
    home,
    auth,
    users,
    api
)))


if __name__ == '__main__':
    app.run(
        debug=True,
        host=host,
        port=port
    )
