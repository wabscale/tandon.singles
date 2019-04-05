from flask import flash, render_template, Blueprint, send_from_directory
from flask_login import current_user, login_required

from .forms import PostForm
from ..app import app
from ..models import Photo

home = Blueprint('home', __name__, url_prefix='/')


@home.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    form.groups.choices = [('', '---')]
    form.groups.choices.extend(map(
        lambda belongs: (
            belongs.closefriendsgroups[0].groupName,
            belongs.closefriendsgroups[0].groupName,
        ),
        current_user.person.belongs
    ))

    if form.validate_on_submit():
        ext = Photo.create(form.image, current_user.username, form.caption.data, form.public.data)
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
