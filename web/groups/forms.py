from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired


class NewForm(FlaskForm):
    action = HiddenField('new')
    group_name = StringField(
        'Group Name',
        validators=[DataRequired()]
    )
    submit = SubmitField('Submit')


class UpdateForm(FlaskForm):
    action = HiddenField('update')
    group_name = StringField(
        'Group Name',
        validators=[DataRequired()]
    )

    @staticmethod
    def populate(group):
        form = UpdateForm()
        form.group_name.data = group.groupName
        form.action.data = 'update'
        return form
