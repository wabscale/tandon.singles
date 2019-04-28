from functools import wraps

import pymysql.err
from flask import render_template, Blueprint, request, flash, redirect
from flask_login import login_required, current_user

import bigsql
from .forms import UpdateGroupForm, NewGroupForm, AddMemberForm, UpdateMemberForm
from ..app import db

groups=Blueprint('groups', __name__, url_prefix='/g')


def validate(func):
    """
    validates forms before executing func
    """

    @wraps(func)
    def wrapper(form, *args):
        if form.validate_on_submit():
            return func(form, *args)

    return wrapper


def handle_update_group(update_form):
    pass


@validate
def handle_delete_group(update_form):
    db.query('CloseFriendGroup').find(
        groupName=update_form.id.data
    ).first()
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@validate
def handle_new_group(new_form):
    db.query('CloseFriendGroup').new(
        groupName=new_form.group_name.data,
        groupOwner=current_user.username
    )
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@validate
def handle_delete_member(update_form, group):
    db.query('Belong').delete(
        groupName=group.groupName,
        groupOwner=group.groupOwner,
        username=update_form.member_name.data,
    )
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@validate
def handle_new_member(new_form, group):
    db.query('Belong').new(
        groupName=group.groupName,
        groupOwner=group.groupOwner,
        username=new_form.members.data,
    )
    try:
        db.session.commit()
    except bigsql.big_ERROR:
        db.session.rollback()


@groups.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    """
    manage owned groups

    delete or create

    :return:
    """
    update_form=UpdateGroupForm()
    new_form=NewGroupForm()

    if request.method == 'POST':
        try:
            {
                'update': lambda: handle_update_group(update_form),
                'delete': lambda: handle_delete_group(update_form),
                'new'   : lambda: handle_new_group(new_form),
                None    : lambda: None
            }[request.form.get('action', default=None)]()
        except pymysql.err.IntegrityError:
            flash('Error')

    update_forms=[
        UpdateGroupForm.populate(
            group
        )
        for group in current_user.closefriendgroups
    ]

    new_form.action.data='new'
    return render_template(
        'groups/groups.html',
        update_forms=update_forms,
        new_form=new_form
    )


@groups.route('/view', methods=['GET', 'POST'])
@login_required
def view():
    """
    view group owned or belonged too

    :param group_name:
    :return:
    """
    group_name=request.args.get('group_name', default=None)
    if group_name is None:
        return redirect('home.index')
    group=db.query('CloseFriendGroup').find(
        groupName=group_name,
        groupOwner=current_user.username
    ).first()

    if group is None:
        return redirect('home.index')

    update_form=UpdateMemberForm()
    new_form=AddMemberForm()

    new_form.members.choices=[
        ('',) * 2
    ]
    new_form.members.choices.extend(
        (follower.followeeUsername,) * 2
        for follower in db.query('Follow').find(
            followerUsername=current_user.username
        ).all()
    )
    new_form.members.default=('---',) * 2

    if request.method == 'POST':
        try:
            {
                'delete': lambda: handle_delete_member(update_form, group),
                'add'   : lambda: handle_new_member(new_form, group),
                None    : lambda: None
            }[request.form.get('action', default=None)]()
        except KeyError:
            pass
        except pymysql.err.IntegrityError:
            db.session.rollback()

    update_forms=[
        UpdateMemberForm.populate(
            b.username
        )
        for b in db.query('CloseFriendGroup').find(
            groupName=group_name
        ).first().belongs
    ]
    return render_template(
        'groups/view.html',
        update_forms=update_forms,
        new_form=new_form,
        group_name=group.groupName,
        group_owner=group.groupOwner
    )
