from flask import Blueprint, render_template, redirect, url_for

from ..app import db

photos=Blueprint('photos', __name__, url_prefix='/p')


@photos.route('/<photoID>')
def view(photoID):
    p=db.query('Photo').find(
        photoID=photoID,
    ).first()

    if p is None:
        return redirect(url_for('home.index'))

    return render_template(
        'photos/view.html',
        photo=p
    )
