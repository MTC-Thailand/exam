from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Email


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')


class UserForm(FlaskForm):
    password = PasswordField('New Password',
                             validators=[DataRequired()])
    confirm = PasswordField('Confirm Password',
                            validators=[DataRequired(),
                                        EqualTo('password', message='Password must match.')])
    email = EmailField('E-mail', validators=[Email(), DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')


class NewPasswordForm(FlaskForm):
    password = PasswordField('New Password',
                             validators=[DataRequired()])
    confirm = PasswordField('Confirm Password',
                            validators=[DataRequired(),
                                        EqualTo('password', message='Password must match.')])
    submit = SubmitField('Save')


class ResetPasswordForm(FlaskForm):
    email = EmailField('E-mail', validators=[Email(), DataRequired()])
    submit = SubmitField('Send')
