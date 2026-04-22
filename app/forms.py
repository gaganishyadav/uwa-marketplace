import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FloatField, IntegerField
from wtforms.validators import (
    DataRequired,
    Email,
    InputRequired,
    Length,
    NumberRange,
    Regexp,
    ValidationError,
)

from app.models import User


class RegistrationForm(FlaskForm):
    """Registration form per D-09: email + password + display name."""

    display_name = StringField('Display Name', validators=[
        DataRequired(message='Display name is required.'),
        Length(min=2, max=50, message='Display name must be 2-50 characters.'),
    ])

    email = StringField('University Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
    ])

    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(
            r'^(?=.*[A-Za-z])(?=.*\d)',
            message='Password must contain at least one letter and one number.',
        ),
    ])

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
    ])

    def validate_email(self, field):
        """Only accept @student.uwa.edu.au addresses (per D-09)."""
        if not field.data.endswith('@student.uwa.edu.au'):
            raise ValidationError('Please use your UWA student email address.')

    def validate_confirm_password(self, field):
        """Passwords must match."""
        if self.password.data != field.data:
            raise ValidationError('Passwords do not match.')

    def validate_email_duplicate(self):
        """Check for duplicate email. Call this manually after validate_on_submit.
        Returns True if duplicate exists (per D-11)."""
        existing = User.query.filter_by(email=self.email.data).first()
        return existing is not None


class LoginForm(FlaskForm):
    email = StringField('University Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
    ])

    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
    ])


class OTPForm(FlaskForm):
    """OTP verification form for post-registration (per D-06, D-08)."""
    otp_code = StringField('Verification Code', validators=[
        DataRequired(message='Verification code is required.'),
        Length(min=6, max=6, message='Verification code must be 6 digits.'),
    ])


class ForgotPasswordForm(FlaskForm):
    """Step 1: user enters email to receive reset link (per D-17)."""
    email = StringField('University Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
    ])


class ResetPasswordForm(FlaskForm):
    """Step 2: user sets new password via reset link (per D-17, D-18)."""
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(
            r'^(?=.*[A-Za-z])(?=.*\d)',
            message='Password must contain at least one letter and one number.',
        ),
    ])

    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your password.'),
    ])

    def validate_confirm_password(self, field):
        if self.password.data != field.data:
            raise ValidationError('Passwords do not match.')


CATEGORIES = [('Textbooks', 'Textbooks'), ('Electronics', 'Electronics'),
              ('Furniture', 'Furniture'), ('Supplies', 'Supplies'),
              ('Sports', 'Sports'), ('Clothing', 'Clothing')]

CONDITIONS = [('New', 'New'), ('Like New', 'Like New'),
              ('Good', 'Good'), ('Fair', 'Fair')]

MEETUP_SPOTS = [('Reid Library', 'Reid Library'),
                ('Barry J. Marshall Library', 'Barry J. Marshall Library'),
                ('Student Guild', 'Student Guild'),
                ('Winthrop Hall', 'Winthrop Hall'),
                ('Oak Lawn', 'Oak Lawn')]


class ListingForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(), Length(min=5, max=200)])
    category = SelectField('Category', choices=CATEGORIES, validators=[DataRequired()])
    condition = SelectField('Condition', choices=CONDITIONS, validators=[DataRequired()])
    price = FloatField('Price', validators=[InputRequired(), NumberRange(min=0, message='Price must be a non-negative number.')])
    stock = IntegerField('Quantity', default=1, validators=[
        InputRequired(), NumberRange(min=1, message='Quantity must be at least 1.')])
    description = TextAreaField('Description', validators=[
        DataRequired(), Length(min=10, max=2000)])
    meetup_spot = SelectField('Meetup Spot', choices=MEETUP_SPOTS, validators=[DataRequired()])
    image = FileField('Photo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'JPG or PNG images only!')])


class EditProfileForm(FlaskForm):
    display_name = StringField('Display Name', validators=[
        DataRequired(), Length(min=2, max=50)])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
