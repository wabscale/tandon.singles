from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, FileField, BooleanField, SelectField,HiddenField
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets import TextArea


class PostForm(FlaskForm):
    action=HiddenField(
        'post',
        default='post',
        validators=[DataRequired()]
    )
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
    id=HiddenField(
        'photoID',
        validators=[DataRequired()]
    )

    @staticmethod
    def populate(photo):
        form=DeleteForm()
        form.id.data=photo.photoID
        return form


class CommentForm(FlaskForm):
    id=HiddenField(
        'photoID',
        validators=[DataRequired()]
    )
    action=HiddenField(
        'comment',
        default='comment',
        validators=[DataRequired()]
    )
    content=StringField(
        'content',
        widget=TextArea(),
        validators=[InputRequired()]
    )

    @staticmethod
    def populate(photo):
        form=CommentForm()
        form.id.data=photo.photoID
        return form