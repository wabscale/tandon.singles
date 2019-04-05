from flask import render_template, Blueprint, request, flash, redirect
from flask_login import login_required, current_user
import pymysql.err

from .forms import UpdateGroupForm, NewGroupForm, AddMemberForm, UpdateMemberForm
from ..orm import Query

groups=Blueprint('groups', __name__, url_prefix='/groups')


def handle_update_group(update_form):
    pass


def handle_delete_group(update_form):
    Query('CloseFriendGroup').find(
        groupName=update_form.id.data
    ).first().delete()


def handle_new_group(new_form):
    if new_form.validate_on_submit():
        Query('CloseFriendGroup').new(
            groupName=new_form.group_name.data,
            groupOwner=current_user.username
        )


def handle_update_member(update_form):
    if update_form.validate_on_submit():
        pass


def handle_delete_member(update_form):
    if update_form.validate_on_submit():
        pass


def handle_new_member(new_form):
    if new_form.validate_on_submit():
        pass


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
        for group in current_user.person.closefriendgroups
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
    group_name = request.args.get('group_name', default=None)
    if group_name is None:
        return redirect('home.index')

    update_form=UpdateMemberForm()
    new_form=AddMemberForm()

    new_form.members.choices=[
        (current_user.username,)*2
    ]
    new_form.members.choices.extend(
        (follower.followeeUsername,)*2
        for follower in Query('Follow').find(
            followerUsername=current_user.username
        ).all()
    )
    new_form.members.default=('---',)*2

    if request.method == 'POST':
        try:
            {
                'update': lambda: handle_update_member(update_form),
                'delete': lambda: handle_delete_member(update_form),
                'new'   : lambda: handle_new_member(new_form),
                None    : lambda: None
            }[request.form.get('action', default=None)]()
        except pymysql.err.IntegrityError:
            flash('Error')

    update_forms=[
        UpdateMemberForm.populate(
            current_user.username,
            group_name
        )
    ]
    update_forms.extend(
        UpdateMemberForm.populate(
            b.username,
            group_name
        )
        for b in Query('CloseFriendGroup').find(
            groupName=group_name
        ).first().belongs
    )
    return render_template(
        'groups/view.html',
        update_forms=update_forms,
        new_form=new_form,
        group_name=group_name
    )
