from flask_wtf import FlaskForm
from wtforms.fields import HiddenField
from wtforms.validators import InputRequired


class FollowForm(FlaskForm):
    id=HiddenField(
        'id',
        validators=[InputRequired()]
    )
    action=HiddenField(
        'action',
        validators=[InputRequired()]
    )
    type=HiddenField(
        'type',
        default='follow',
        validators=[InputRequired()]
    )


class TagForm(FlaskForm):
    id=HiddenField(
        'id',
        validators=[InputRequired()]
    )
    action=HiddenField(
        'action',
        validators=[InputRequired()]
    )
    type=HiddenField(
        'type',
        default='tag',
        validators=[InputRequired()]
    )
