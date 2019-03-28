from flask import request, redirect, url_for, flash, render_template, Blueprint
from flask_login import current_user, login_user, logout_user, login_required
import pymysql

from ..app import app
from ..models import User

api = Blueprint('api', __name__, url_prefix='/api')


