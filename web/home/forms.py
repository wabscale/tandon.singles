from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired


class PostForm(FlaskForm):
    image = FileField('Image', validators=[DataRequired()])
    caption = StringField('Caption', validators=[DataRequired()])
    public = BooleanField('Public post')
    post=SubmitField('Post', )
