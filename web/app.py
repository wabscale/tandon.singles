from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect
from flaskext.mysql import MySQL
from datetime import datetime
from flask import Flask
import logging
import os

from .config import Config

host = '0.0.0.0'
port = 5000
start_time = datetime.now()

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config())

Bootstrap(app)
CSRFProtect(app)
db = MySQL(app)

if app.config['VERBOSE_SQL_GENERATION']:
    logging.basicConfig(filename=os.path.join(
        app.config['LOG_DIR'],
        'orm_log.log'
    ), filemode='w+')



# register blueprints
from .auth import auth
from .users import users
from .home import home

list(map(app.register_blueprint, (
    home,
    auth,
    users
)))


if __name__ == '__main__':
    app.run(
        debug=True,
        host=host,
        port=port
    )
