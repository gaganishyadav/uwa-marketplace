"""Unit tests for User model: password hashing, OTP, reset tokens, defaults."""

from datetime import datetime, timedelta

from app import db
from app.models import User, _utcnow


def test_password_hashing(app):
    """Password is hashed, not stored as plaintext. Salts produce unique hashes."""
    with app.app_context():
        user1 = User(display_name='User One', email='one@student.uwa.edu.au')
        user1.set_password('Password1')
        db.session.add(user1)

        user2 = User(display_name='User Two', email='two@student.uwa.edu.au')
        user2.set_password('Password1')
        db.session.add(user2)
        db.session.commit()

        # Hash is not plaintext
        assert user1.password_hash != 'Password1'
        # Same password, different hashes (salt)
        assert user1.password_hash != user2.password_hash
        # Correct password verified
        assert user1.check_password('Password1') is True
        # Wrong password rejected
        assert user1.check_password('wrong') is False


def test_otp_generation(app):
    """OTP is a 6-digit string, validates correctly with the right code."""
    with app.app_context():
        user = User(display_name='OTP User', email='otp@student.uwa.edu.au')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()

        otp = user.generate_otp()
        # 6-digit string
        assert len(otp) == 6
        assert otp.isdigit()
        assert 100000 <= int(otp) <= 999999
        # Valid with correct code
        assert user.is_otp_valid(otp) is True
        # Invalid with wrong code
        assert user.is_otp_valid('000000') is False


def test_otp_expiry(app):
    """OTP expires after 5 minutes."""
    with app.app_context():
        user = User(display_name='Expiry User', email='expiry@student.uwa.edu.au')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()

        otp = user.generate_otp()
        # Manually set OTP creation to 6 minutes ago
        user.otp_created_at = _utcnow() - timedelta(minutes=6)
        db.session.commit()
        # Should be expired
        assert user.is_otp_valid(otp) is False


def test_otp_resend_cooldown(app):
    """OTP resend enforces 60-second cooldown."""
    with app.app_context():
        user = User(display_name='Cooldown User', email='cooldown@student.uwa.edu.au')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()

        user.generate_otp()
        db.session.commit()
        # Cannot resend immediately
        assert user.can_resend_otp() is False
        # Set creation time to 61 seconds ago
        user.otp_created_at = _utcnow() - timedelta(seconds=61)
        db.session.commit()
        # Can resend after cooldown
        assert user.can_resend_otp() is True


def test_reset_token_generation_and_verification(app):
    """Reset token round-trips correctly, wrong key returns None."""
    with app.app_context():
        email = 'reset@student.uwa.edu.au'
        token = User.generate_reset_token(email, app.config['SECRET_KEY'])
        verified = User.verify_reset_token(token, app.config['SECRET_KEY'])
        assert verified == email
        # Wrong secret key returns None
        wrong = User.verify_reset_token(token, 'wrong-secret-key')
        assert wrong is None


def test_reset_token_invalid_token(app):
    """Reset token with tampered/invalid data returns None."""
    with app.app_context():
        # Use a completely invalid token string
        result = User.verify_reset_token('invalid-token-data', app.config['SECRET_KEY'])
        assert result is None


def test_reset_token_expiry(app):
    """Reset token rejected when max_age is exceeded."""
    with app.app_context():
        email = 'expiry@student.uwa.edu.au'
        token = User.generate_reset_token(email, app.config['SECRET_KEY'])
        # max_age=-1 means any age exceeds the limit (forces expiry)
        result = User.verify_reset_token(token, app.config['SECRET_KEY'], max_age=-1)
        assert result is None


def test_user_default_fields(app):
    """User model defaults: email_verified=False, created_at is set."""
    with app.app_context():
        user = User(display_name='Default User', email='default@student.uwa.edu.au')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()

        assert user.email_verified is False
        assert user.created_at is not None
        assert user.display_name == 'Default User'
        assert user.email == 'default@student.uwa.edu.au'
