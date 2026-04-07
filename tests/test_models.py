"""Unit tests for User model: password hashing, OTP, and reset tokens."""

import time

import pytest
from datetime import datetime, timedelta

from app import db
from app.models import User


def _create_user(app, name, email, password='Password1'):
    """Helper to create and commit a user with password set."""
    user = User(display_name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


class TestPasswordHashing:
    """Tests for password hashing and verification (VALIDATION: 01-05-01)."""

    def test_password_hashing(self, app):
        """Password is stored as salted hash, not plaintext."""
        with app.app_context():
            user = _create_user(app, 'Test', 'test@student.uwa.edu.au', 'SecurePass1')

            # Hash is not plaintext
            assert user.password_hash != 'SecurePass1'
            # werkzeug uses scrypt or pbkdf2 depending on version
            assert 'scrypt:' in user.password_hash or 'pbkdf2:' in user.password_hash

            # Correct password passes
            assert user.check_password('SecurePass1') is True

            # Wrong password fails
            assert user.check_password('WrongPassword1') is False

    def test_password_salting(self, app):
        """Two users with same password get different hashes (unique salts)."""
        with app.app_context():
            user1 = User(display_name='User1', email='user1@student.uwa.edu.au')
            user1.set_password('SamePass123')

            user2 = User(display_name='User2', email='user2@student.uwa.edu.au')
            user2.set_password('SamePass123')

            db.session.add_all([user1, user2])
            db.session.commit()

            # Same password, different hashes due to unique salts
            assert user1.password_hash != user2.password_hash


class TestOTPGeneration:
    """Tests for OTP generation and validation (VALIDATION: 01-06-01)."""

    def test_otp_generation(self, app):
        """OTP is a 6-digit code and validates correctly."""
        with app.app_context():
            user = _create_user(app, 'OTP User', 'otp@student.uwa.edu.au')

            otp = user.generate_otp()

            # OTP is a 6-digit string
            assert len(otp) == 6
            assert otp.isdigit()
            assert 100000 <= int(otp) <= 999999

            # Correct code is valid
            assert user.is_otp_valid(otp) is True

            # Wrong code is invalid
            assert user.is_otp_valid('000000') is False

    def test_otp_expiry(self, app):
        """OTP expires after 5 minutes."""
        with app.app_context():
            user = _create_user(app, 'Expiry User', 'expiry@student.uwa.edu.au')

            otp = user.generate_otp()

            # Manually set creation time to 6 minutes ago (naive UTC)
            user.otp_created_at = datetime.utcnow() - timedelta(minutes=6)
            db.session.commit()

            # Expired OTP is invalid
            assert user.is_otp_valid(otp) is False

    def test_otp_resend_cooldown(self, app):
        """OTP resend enforces 60-second cooldown."""
        with app.app_context():
            user = _create_user(app, 'Cooldown', 'cooldown@student.uwa.edu.au')

            user.generate_otp()

            # Cannot resend immediately
            assert user.can_resend_otp() is False

            # Manually set creation time to 61 seconds ago (naive UTC)
            user.otp_created_at = datetime.utcnow() - timedelta(seconds=61)
            db.session.commit()

            # Can resend after cooldown
            assert user.can_resend_otp() is True

    def test_otp_no_previous_code(self, app):
        """can_resend_otp returns True when no OTP has been generated yet."""
        with app.app_context():
            user = _create_user(app, 'No OTP', 'nootp@student.uwa.edu.au')

            assert user.can_resend_otp() is True

    def test_otp_null_fields_invalid(self, app):
        """is_otp_valid returns False when no OTP has been generated."""
        with app.app_context():
            user = _create_user(app, 'Null OTP', 'null@student.uwa.edu.au')

            assert user.is_otp_valid('123456') is False


class TestResetToken:
    """Tests for password reset token generation and verification (VALIDATION: 01-07-01)."""

    def test_reset_token_generation_and_verification(self, app):
        """Reset token can be generated and verified with correct secret key."""
        with app.app_context():
            email = 'reset@student.uwa.edu.au'
            secret_key = app.config['SECRET_KEY']

            token = User.generate_reset_token(email, secret_key)
            assert token is not None

            # Verify with correct key
            result = User.verify_reset_token(token, secret_key)
            assert result == email

    def test_reset_token_wrong_secret(self, app):
        """Reset token verification fails with wrong secret key."""
        with app.app_context():
            email = 'wrong@student.uwa.edu.au'
            secret_key = app.config['SECRET_KEY']

            token = User.generate_reset_token(email, secret_key)
            result = User.verify_reset_token(token, 'wrong-secret-key')
            assert result is None

    def test_reset_token_expiry(self, app):
        """Reset token expires after max_age seconds."""
        with app.app_context():
            email = 'expired@student.uwa.edu.au'
            secret_key = app.config['SECRET_KEY']

            token = User.generate_reset_token(email, secret_key)
            # Wait briefly then verify with max_age=1 (1 second)
            # The token was created ~0s ago, so max_age=1 should still work
            # We test expiry by using a very small max_age and adding a delay
            result = User.verify_reset_token(token, secret_key, max_age=1)
            assert result == email  # Should still be valid within 1 second

            # Now wait for expiry
            time.sleep(2)
            result = User.verify_reset_token(token, secret_key, max_age=1)
            assert result is None  # Now expired

    def test_reset_token_tampered(self, app):
        """Tampered reset token returns None."""
        with app.app_context():
            secret_key = app.config['SECRET_KEY']
            tampered_token = 'this.is.not.valid'

            result = User.verify_reset_token(tampered_token, secret_key)
            assert result is None


class TestUserDefaultFields:
    """Tests for User model default field values."""

    def test_user_default_fields(self, app):
        """User has correct default values after creation."""
        with app.app_context():
            user = User(display_name='Default', email='default@student.uwa.edu.au')
            user.set_password('Password1')
            db.session.add(user)
            db.session.commit()

            # email_verified defaults to False
            assert user.email_verified is False

            # created_at is set automatically
            assert user.created_at is not None

            # OTP fields are None by default
            assert user.otp_code is None
            assert user.otp_created_at is None

    def test_user_uniqueness_constraint(self, app):
        """Duplicate email raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            user1 = User(display_name='First', email='unique@student.uwa.edu.au')
            user1.set_password('Password1')
            db.session.add(user1)
            db.session.commit()

            user2 = User(display_name='Second', email='unique@student.uwa.edu.au')
            user2.set_password('Password2')
            db.session.add(user2)

            with pytest.raises(IntegrityError):
                db.session.commit()
