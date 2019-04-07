from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, FileField, BooleanField, SelectField,HiddenField
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
    group = SelectField(
        'Friend Group',
        validators=[]
    )
    public = BooleanField(
        'Public post',
        default=True
    )

    post = SubmitField('Post', )


class DeleteForm(FlaskForm):
    action=HiddenField(
        'delete',
        default='delete',
        validators=[DataRequired()]
    )
    photoid=HiddenField(
        'photoID',
        validators=[DataRequired()]
    )

    @staticmethod
    def populate(photo):
        form=DeleteForm()
        form.photoid.data=photo.photoID