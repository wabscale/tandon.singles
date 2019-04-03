from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets import TextArea


class PostForm(FlaskForm):
    image = FileField(
        'Image',
        validators=[DataRequired()]
    )
    caption = StringField(
        'Caption',
        widget=TextArea(),
        validators=[InputRequired()]
    )
    public = BooleanField(
        'Public post',
        default=True
    )

    post = SubmitField('Post', )
