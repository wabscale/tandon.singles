from flask import render_template, Blueprint, request
from flask_login import login_required, current_user
import pymysql.err

from .forms import UpdateForm, NewForm
from ..orm import Query

groups = Blueprint('groups', __name__, url_prefix='/groups')


def handle_update(update_form, _):
    pass


def handle_delete(update_form, _):
    pass


def handle_new(_, new_form):
    if new_form.validate_on_submit():
        Query('CloseFriendGroup').new(
            groupName=new_form.group_name.data,
            groupOwner=current_user.username
        )


@groups.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    """
    manage owned groups

    delete or create

    :return:
    """
    update_form = UpdateForm()
    new_form = NewForm()

    try:
        if request.method == 'POST':
            {
                'update': handle_update,
                'delete': handle_delete,
                'new': handle_new,
                None: lambda x, y: None
            }[request.form.get('action', default=None)](
                update_form, new_form
            )
    except pymysql.err.IntegrityError:
        pass

    update_forms = [
        UpdateForm.populate(
            group
        )
        for group in current_user.person.closefriendgroups
    ]

    new_form.action.data = 'new'
    return render_template(
        'groups/groups.html',
        update_forms=update_forms,
        new_form=new_form
    )


@groups.route('/view')
@login_required
def view():
    """
    view group owned or belonged too

    :param group_name:
    :return:
    """
    pass
