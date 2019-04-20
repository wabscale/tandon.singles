from flask_wtf import FlaskForm
from wtforms.fields import HiddenField
from wtforms.validators import DataRequired


class FollowForm(FlaskForm):
    id=HiddenField(
        'username',
        validators=[DataRequired()]
    )
    action=HiddenField(
        'follow_user',
        default='follow_user',
        validators=[DataRequired()]
    )

    @staticmethod
    def populate(person):
        form=FollowForm()
        form.id.data=person.username
        return form
