from flask import flash, render_template, Blueprint, send_from_directory
from flask_login import current_user, login_required

from .forms import PostForm
from ..app import app
from ..models import Photo
from ..orm import Query

home = Blueprint('home', __name__, url_prefix='/')


@home.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    form.group.choices = [('', '---')]
    form.group.choices.extend(
        (group.groupName,)*2
        for group in Query('CloseFriendGroup').find(
            groupOwner=current_user.username
        ).all()
    )
    form.group.choices.extend(map(
        lambda belongs: (
            belongs.closefriendsgroups[0].groupName,
        )*2,
        current_user.person.belongs
    ))

    if form.validate_on_submit():
        ext = Photo.create(
            form,
        )
        if ext is not None:
            flash('{} is not a valid image type ;('.format(ext))
    # print(''.join(str(p) for p in Photo.visible_to(current_user.username)))
    return render_template(
        'home/index.html',
        form=form,
        photos=Photo.visible_to(current_user.username)
    )


@home.route('/img/<path:path>')
@login_required
def img(path):
    return send_from_directory(
        app.config['UPLOAD_DIR'],
        path
    )
