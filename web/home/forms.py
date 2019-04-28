from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, FileField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired, InputRequired, Optional
from wtforms.widgets import TextArea

from ..app import db


class PostForm(FlaskForm):
    action=HiddenField(
        'post',
        default='post',
        validators=[DataRequired()]
    )
    image=FileField(
        'Image',
        validators=[DataRequired()]
    )
    caption=StringField(
        'Caption',
        widget=TextArea(),
        validators=[InputRequired()]
    )
    group=SelectField(
        'Friend Group',
        validators=[Optional()]
    )
    public=BooleanField(
        'Public post',
        default=True,
        validators=[DataRequired()]
    )

    post=SubmitField('Post')


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


class LikeForm(FlaskForm):
    id=HiddenField(
        'photoID',
        validators=[InputRequired()]
    )
    action=HiddenField(
        'action',
        default='like',
        validators=[InputRequired()]
    )
    liked=0

    @staticmethod
    def populate(photo):
        form=LikeForm()
        form.liked=int(db.query('Liked').find(
            username=current_user.username,
            photoID=photo.photoID
        ).first() is not None)
        form.id.data=photo.photoID
        return form
