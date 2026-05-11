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
        assert user1.password_hash != 'Password1', (
            "password is being stored in plaintext -- set_password is not hashing"
        )
        # Same password, different hashes (salt)
        assert user1.password_hash != user2.password_hash, (
            "two users with the same password got identical hashes -- "
            "set_password is not using a per-user salt (pbkdf2:sha256 should)"
        )
        # Correct password verified
        assert user1.check_password('Password1') is True, (
            "check_password rejected the correct password -- the hash/verify "
            "pair is mismatched"
        )
        # Wrong password rejected
        assert user1.check_password('wrong') is False, (
            "check_password accepted an obviously wrong password -- "
            "verification logic is bypassed"
        )


def test_otp_generation(app):
    """OTP is a 6-digit string, validates correctly with the right code."""
    with app.app_context():
        user = User(display_name='OTP User', email='otp@student.uwa.edu.au')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()

        otp = user.generate_otp()
        # 6-digit string
        assert len(otp) == 6, f"OTP should be exactly 6 chars; got {len(otp)} ({otp!r})"
        assert otp.isdigit(), f"OTP should be all digits; got {otp!r}"
        otp_int = int(otp)
        assert 100000 <= otp_int <= 999999, (
            f"OTP should fall in [100000, 999999]; got {otp_int} -- "
            f"the leading-zero handling in generate_otp may be wrong"
        )
        # Valid with correct code
        assert user.is_otp_valid(otp) is True, (
            f"is_otp_valid rejected the just-generated OTP {otp!r} -- "
            f"otp_created_at may not be set or the comparison window is wrong"
        )
        # Invalid with wrong code
        assert user.is_otp_valid('000000') is False, (
            "is_otp_valid accepted '000000' which was not the generated code -- "
            "the code comparison is bypassed"
        )


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
        assert user.is_otp_valid(otp) is False, (
            "is_otp_valid accepted an OTP created 6 minutes ago; "
            "the 5-minute expiry window (per D-08) is not being enforced"
        )


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
        assert user.can_resend_otp() is False, (
            "can_resend_otp returned True immediately after generation; "
            "the 60-second cooldown is not being applied"
        )
        # Set creation time to 61 seconds ago
        user.otp_created_at = _utcnow() - timedelta(seconds=61)
        db.session.commit()
        # Can resend after cooldown
        assert user.can_resend_otp() is True, (
            "can_resend_otp returned False 61s after generation; "
            "the cooldown calculation may be using > instead of >= or the wrong base time"
        )


def test_reset_token_generation_and_verification(app):
    """Reset token round-trips correctly, wrong key returns None."""
    with app.app_context():
        email = 'reset@student.uwa.edu.au'
        token = User.generate_reset_token(email, app.config['SECRET_KEY'])
        verified = User.verify_reset_token(token, app.config['SECRET_KEY'])
        assert verified == email, (
            f"reset token did not round-trip the email: encoded={email!r}, "
            f"decoded={verified!r}"
        )
        # Wrong secret key returns None
        wrong = User.verify_reset_token(token, 'wrong-secret-key')
        assert wrong is None, (
            f"verify_reset_token returned {wrong!r} for a token signed with a "
            f"different secret -- signature verification is bypassed"
        )


def test_reset_token_invalid_token(app):
    """Reset token with tampered/invalid data returns None."""
    with app.app_context():
        # Use a completely invalid token string
        result = User.verify_reset_token('invalid-token-data', app.config['SECRET_KEY'])
        assert result is None, (
            f"verify_reset_token returned {result!r} for an unsigned junk string; "
            f"BadSignature is not being caught"
        )


def test_reset_token_expiry(app):
    """Reset token rejected when max_age is exceeded."""
    with app.app_context():
        email = 'expiry@student.uwa.edu.au'
        token = User.generate_reset_token(email, app.config['SECRET_KEY'])
        # max_age=-1 means any age exceeds the limit (forces expiry)
        result = User.verify_reset_token(token, app.config['SECRET_KEY'], max_age=-1)
        assert result is None, (
            f"verify_reset_token returned {result!r} when max_age=-1 should have "
            f"forced expiry; SignatureExpired is not being caught"
        )


def test_user_default_fields(app):
    """User model defaults: email_verified=False, created_at is set."""
    with app.app_context():
        user = User(display_name='Default User', email='default@student.uwa.edu.au')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()

        assert user.email_verified is False, (
            f"new users should default to email_verified=False; "
            f"got {user.email_verified!r}"
        )
        assert user.created_at is not None, (
            "created_at default was not applied -- the column default factory may "
            "have been removed"
        )
        assert user.display_name == 'Default User', (
            f"display_name was not persisted as supplied; got {user.display_name!r}"
        )
        assert user.email == 'default@student.uwa.edu.au', (
            f"email was not persisted as supplied; got {user.email!r}"
        )
