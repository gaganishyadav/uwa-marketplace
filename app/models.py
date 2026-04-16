import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


def _utcnow():
    """Return current UTC time as a naive datetime for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    bio = db.Column(db.Text, nullable=True, default='')
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=_utcnow,
        nullable=False,
    )

    def set_password(self, password):
        """Hash and store password using werkzeug pbkdf2:sha256."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def generate_otp(self):
        """Generate a 6-digit cryptographically secure OTP (per D-08)."""
        self.otp_code = str(secrets.randbelow(900000) + 100000)
        self.otp_created_at = _utcnow()
        return self.otp_code

    def is_otp_valid(self, code):
        """Check if provided OTP matches and is within 5-minute window (per D-08)."""
        if not self.otp_code or not self.otp_created_at:
            return False
        if self.otp_code != code:
            return False
        expiry = self.otp_created_at + timedelta(minutes=5)
        return _utcnow() < expiry

    def can_resend_otp(self):
        """Check if 60-second cooldown has passed since last OTP (per D-08)."""
        if not self.otp_created_at:
            return True
        cooldown = self.otp_created_at + timedelta(seconds=60)
        return _utcnow() >= cooldown

    @staticmethod
    def generate_reset_token(email, secret_key):
        """Generate a timed, signed reset token (per D-17, D-18)."""
        s = URLSafeTimedSerializer(secret_key)
        return s.dumps({'email': email}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, secret_key, max_age=3600):
        """Verify reset token. Returns email if valid, None otherwise.
        max_age defaults to 3600 seconds (1 hour) per D-18."""
        s = URLSafeTimedSerializer(secret_key)
        try:
            data = s.loads(token, salt='password-reset-salt', max_age=max_age)
            return data['email']
        except (SignatureExpired, BadSignature):
            return None


class Listing(db.Model):
    __tablename__ = 'listing'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    meetup_spot = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('listings', lazy='dynamic'))
