from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, URL, Email, Length, Optional
from flask_wtf.file import FileAllowed, FileSize

class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    name = StringField("Name", validators=[DataRequired()])
    
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    
class EditProfileForm(FlaskForm):
    name = StringField("Name")
    image = FileField(
        "Avatar:", 
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!'),
            FileSize(max_size=3 * 1024 * 1024, message='File size must be less than 10MB!')
        ]
    )
    
class EditAccForm(FlaskForm):
    email = EmailField("Email", validators=[Optional(), Email()])
    password = PasswordField("Password", validators=[Optional(), Length(min=8)])