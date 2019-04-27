from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from ..app import db

photos=Blueprint('photos', __name__, url_prefix='/p')


@photos.route('/<photoID>')
@login_required
def view(photoID):
    p=db.query('Photo').find(
        photoID=photoID,
    ).first()

    if p is None:
        return redirect(url_for('home.index'))

    follows=db.query('Follow').find(
        followerUsername=current_user.username,
        followeeUsername=p.PhotoOwner
    ).first()

    if follows is None or not follows.acceptedfollow or not p.allFollowers:
        return redirect(url_for('home.index'))

    shares = list(p.shares)

    if len(shares) != 0:
        share=shares[0]
        if all(
            share.groupName != group.groupName and share.groupOwner != group.groupName
            for group in current_user.closefriendgroups
        ):
            return redirect('home.index')

    return render_template(
        'photos/view.html',
        photo=p
    )
