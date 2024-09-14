# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class VehicleForm(FlaskForm):
    vehicle_model = StringField('Vehicle Model', validators=[DataRequired()])
    vehicle_size = SelectField('Vehicle Size', choices=[
        ('Compact', 'Compact'), ('Large', 'Large'), ('Handicap', 'Handicap')
    ], validators=[DataRequired()])
    license_plate = StringField('License Plate', validators=[DataRequired()])
    submit = SubmitField('Add Vehicle')

class ReservationForm(FlaskForm):
    vehicle_id = SelectField('Select Vehicle', coerce=int, validators=[DataRequired()])
    reservation_date_in = DateField('Check-In Date', validators=[DataRequired()], format='%Y-%m-%d')
    reservation_date_out = DateField('Check-Out Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Reserve')

    def validate_reservation_date_out(self, reservation_date_out):
        if reservation_date_out.data <= self.reservation_date_in.data:
            raise ValidationError('Check-Out Date must be after Check-In Date.')