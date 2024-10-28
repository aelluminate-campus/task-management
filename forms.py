from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateTimeField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateTimeField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User, db, Task
from datetime import datetime, timedelta, date

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], validators=[DataRequired()])

    # Dropdowns for month, day, and year
    deadline_month = SelectField('Month', choices=[
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], validators=[DataRequired()])

    deadline_day = SelectField('Day', choices=[(str(i), str(i)) for i in range(1, 32)], validators=[DataRequired()])
    deadline_year = SelectField('Year', choices=[(str(i), str(i)) for i in range(2023, 2032)], validators=[DataRequired()])
    
    submit = SubmitField('Save Task')




class ShareTaskForm(FlaskForm):
    users = SelectMultipleField('Share with Users', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Share Task')
