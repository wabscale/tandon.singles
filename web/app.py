import logging
import os
from datetime import datetime

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect
import bigsql

from .config import Config

host = '0.0.0.0'
port = 5000
start_time = datetime.now()

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config())

Bootstrap(app)
CSRFProtect(app)
db = bigsql.big_SQL(
    user=app.config['MYSQL_DATABASE_USER'],
    pword=app.config['MYSQL_DATABASE_PASSWORD'],
    db=app.config['MYSQL_DATABASE_DB'],
    host=app.config['MYSQL_DATABASE_HOST'],
    VERBOSE_SQL_EXECUTION=app.config['VERBOSE_SQL_EXECUTION'],
    # DB_LOG_FILE=app.config['DB_LOG_FILE']
)

if not app.config['DEBUG']:
    logging.basicConfig(filename=os.path.join(
        app.config['LOG_DIR'],
        'orm_log.log'
    ), filemode='w+', level='DEBUG')
else:
    logging.basicConfig(
        format='%(message)s',
        level='DEBUG'
    )

# register blueprints
from .auth import auth
from .users import users
from .home import home
from .groups import groups

list(map(app.register_blueprint, (
    home,
    auth,
    users,
    groups
)))

if __name__ == '__main__':
    app.run(
        debug=True,
        host=host,
        port=port
    )
