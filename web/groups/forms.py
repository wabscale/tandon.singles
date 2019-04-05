from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, SelectField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired


class UpdateMemberForm(FlaskForm):
    id = HiddenField(
        'group_name',
        validators=[DataRequired()]
    )
    group_name=StringField(
        'Group Name',
        validators=[DataRequired()]
    )
    action = HiddenField(
        default='update',
        validators=[DataRequired()]
    )
    member_name = StringField(
        'Member Name'
    )

    @staticmethod
    def populate(username, group_name):
        form=UpdateMemberForm()
        form.id.data=group_name
        form.group_name.data=group_name
        form.member_name.data=username
        return form


class AddMemberForm(FlaskForm):
    id = HiddenField(
        'group_name',
        validators=[DataRequired()]
    )
    action = HiddenField(
        default='add',
        validators=[DataRequired()]
    )
    members = SelectField(
        'Add User To Group',
        default=('', '---'),
        validators=[DataRequired()]
    )


class NewGroupForm(FlaskForm):
    action = HiddenField('new')
    group_name = StringField(
        'Group Name',
        validators=[DataRequired()]
    )
    submit = SubmitField('Submit')


class UpdateGroupForm(FlaskForm):
    id = HiddenField('update')
    action = HiddenField('update')
    group_name = StringField(
        'Group Name',
        validators=[DataRequired()]
    )

    @staticmethod
    def populate(group):
        form = UpdateGroupForm()
        form.group_name.data = group.groupName
        form.id.data = group.groupName
        return form
