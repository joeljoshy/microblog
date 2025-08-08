import phonenumbers

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, URL, Email, EqualTo, ValidationError, Length

from app.models import User
import sqlalchemy as sa
from app import db


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Log In")


def validate_mobile(form, field):
    try:
        number = phonenumbers.parse(field.data, None)
        if not phonenumbers.is_valid_number(number):
            raise ValidationError("Invalid mobile number.")
    except phonenumbers.NumberParseException:
        raise ValidationError("Invalid mobile number.")


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')]
    )
    mobile = StringField('Mobile', validators=[DataRequired(), validate_mobile])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError('Please use a different username.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField("Say something", validators=[\
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField("Submit")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired()])
    submit = SubmitField("Request Password Reset")

    def validate_password(self, password):
        if password.data != self.password2.data:
            raise ValidationError('Passwords must match.')


class CommentForm(FlaskForm):
    body = TextAreaField('Add Comment', validators=[DataRequired(), Length(min=1, max=280)])
    submit = SubmitField('Post Comment')