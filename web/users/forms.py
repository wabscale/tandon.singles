from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, FileField, BooleanField, SelectField,HiddenField
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets import TextArea


class FollowForm(FlaskForm):
    id = HiddenField(
        'username',
        validators=[DataRequired()]
    )

    @staticmethod
    def populate(person):
        form=FollowForm()
        form.id.data=person.username
        return form
