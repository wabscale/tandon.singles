from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, SelectField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired


class UpdateMemberForm(FlaskForm):
    action = HiddenField(
        default='update',
        validators=[DataRequired()]
    )
    member_name = StringField(
        'Member Name'
    )

    @staticmethod
    def populate(username):
        form=UpdateMemberForm()
        form.member_name.data=username
        return form


class AddMemberForm(FlaskForm):
    action = HiddenField(
        default='add',
        validators=[DataRequired()]
    )
    members = SelectField(
        'Add User To Group',
        default=('', '---'),
        validators=[DataRequired()]
    )
    submit = SubmitField('Submit')


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
