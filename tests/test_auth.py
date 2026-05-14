"""Integration tests for auth routes: register, login, OTP, logout, password reset."""

from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import db
from app.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_user(client, display_name='Test User', email='test@student.uwa.edu.au',
                  password='Password1', confirm_password='Password1'):
    return client.post('/register', data={
        'display_name': display_name,
        'email': email,
        'password': password,
        'confirm_password': confirm_password,
    }, follow_redirects=False)


def create_verified_user(app, email='verified@student.uwa.edu.au', password='Password1',
                         display_name='Verified User'):
    with app.app_context():
        user = User(display_name=display_name, email=email)
        user.set_password(password)
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        return user.id


def login_user(client, email='verified@student.uwa.edu.au', password='Password1'):
    return client.post('/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=False)


def create_pending_registration(client, display_name='Test User', email='test@student.uwa.edu.au',
                                password='Password1', otp_code='123456'):
    """Set pending_registration in session, simulating state between register and verify."""
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with client.session_transaction() as sess:
        sess['pending_registration'] = {
            'display_name': display_name,
            'email': email,
            'password_hash': generate_password_hash(password),
            'otp_code': otp_code,
            'otp_created_at': now,
            'otp_sent_at': now,
        }


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

def test_register_success(client, app):
    """Valid registration stores pending data in session and redirects to OTP verification."""
    response = register_user(client)
    assert response.status_code == 302
    assert '/verify-otp' in response.headers['Location']

    # No User row should exist yet
    with app.app_context():
        assert User.query.filter_by(email='test@student.uwa.edu.au').first() is None

    # Pending registration should be in session
    with client.session_transaction() as sess:
        pending = sess.get('pending_registration')
        assert pending is not None
        assert pending['display_name'] == 'Test User'
        assert pending['email'] == 'test@student.uwa.edu.au'
        assert 'user_id' not in sess


def test_register_invalid_email(client, app):
    """Rejects non-UWA email domain."""
    response = register_user(client, email='test@gmail.com')
    assert response.status_code == 200

    with app.app_context():
        assert User.query.count() == 0


def test_register_duplicate_email(client, app):
    """Shows 'already exists' error for duplicate verified email."""
    create_verified_user(app, email='test@student.uwa.edu.au')
    response = register_user(client)
    assert response.status_code == 200

    with app.app_context():
        assert User.query.count() == 1


def test_register_weak_password(client, app):
    """Rejects password that is too short or lacks complexity."""
    response = register_user(client, password='pass', confirm_password='pass')
    assert response.status_code == 200

    with app.app_context():
        assert User.query.count() == 0


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

def test_login_success(client, app):
    """Correct credentials redirect to dashboard for verified user."""
    create_verified_user(app)
    response = login_user(client)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


def test_login_wrong_password(client, app):
    """Wrong password shows error and re-renders form."""
    create_verified_user(app)
    response = login_user(client, password='WrongPassword1')
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Logout test
# ---------------------------------------------------------------------------

def test_logout(client, app):
    """Logout via POST clears session and redirects to auth page."""
    create_verified_user(app)
    login_user(client)

    response = client.post('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']

    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_logout_get_not_allowed(client, app):
    """GET /logout is not allowed (405 Method Not Allowed)."""
    create_verified_user(app)
    login_user(client)

    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 405


# ---------------------------------------------------------------------------
# CSRF test
# ---------------------------------------------------------------------------

def test_csrf_required_on_post_routes():
    """POST without CSRF token returns 400 when CSRF is enabled."""
    from app import create_app as _create_app

    csrf_app = _create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': True,
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_DEFAULT_SENDER': 'test@example.com',
    })
    csrf_client = csrf_app.test_client()
    response = csrf_client.post('/register', data={
        'display_name': 'CSRF User',
        'email': 'csrf@student.uwa.edu.au',
        'password': 'Password1',
        'confirm_password': 'Password1',
    })
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# OTP verification tests
# ---------------------------------------------------------------------------

def test_verify_otp_valid(client, app):
    """Correct OTP creates user in DB and redirects to gallery."""
    create_pending_registration(client, otp_code='654321')

    response = client.post('/verify-otp', data={
        'otp_code': '654321',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user is not None
        assert user.email_verified is True
        assert user.display_name == 'Test User'

    with client.session_transaction() as sess:
        assert 'pending_registration' not in sess
        assert 'user_id' in sess


def test_verify_otp_invalid(client, app):
    """Wrong OTP shows error, no user created."""
    create_pending_registration(client, otp_code='654321')

    response = client.post('/verify-otp', data={
        'otp_code': '000000',
    }, follow_redirects=False)
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user is None


# ---------------------------------------------------------------------------
# Password reset tests
# ---------------------------------------------------------------------------

def test_forgot_password_sends_email(client, app):
    """Forgot password route completes without error."""
    create_verified_user(app)
    response = client.post('/forgot-password', data={
        'email': 'verified@student.uwa.edu.au',
    }, follow_redirects=False)
    assert response.status_code == 200


def test_reset_password_valid_token(client, app):
    """Valid reset token allows password change."""
    with app.app_context():
        uid = create_verified_user(app)
        user = db.session.get(User, uid)
        token = User.generate_reset_token(user.email, app.config['SECRET_KEY'])

    response = client.get(f'/reset-password/{token}')
    assert response.status_code == 200

    response = client.post(f'/reset-password/{token}', data={
        'password': 'NewPassword1',
        'confirm_password': 'NewPassword1',
    }, follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email='verified@student.uwa.edu.au').first()
        assert user.check_password('NewPassword1') is True


def test_reset_password_expired_token(client, app):
    """Invalid/expired token redirects to forgot-password with error."""
    response = client.get('/reset-password/invalid-token-string',
                          follow_redirects=False)
    assert response.status_code == 302
    assert '/forgot-password' in response.headers['Location']


# ---------------------------------------------------------------------------
# Additional route access / edge case tests
# ---------------------------------------------------------------------------

def test_dashboard_unauthenticated(client):
    """GET /dashboard without login redirects to /auth."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_verify_otp_unauthenticated(client):
    """GET /verify-otp without pending registration redirects to /auth."""
    response = client.get('/verify-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_stale_session_verify_otp(client, app):
    """GET /verify-otp with invalid pending_registration data redirects to /auth."""
    with client.session_transaction() as sess:
        sess['pending_registration'] = {'otp_code': None, 'otp_created_at': None}

    response = client.get('/verify-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_auth_redirects_verified_user(client, app):
    """Logged-in verified user visiting /auth is redirected to dashboard."""
    create_verified_user(app)
    login_user(client)
    response = client.get('/auth', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


def test_register_password_mismatch(client, app):
    """Passwords that don't match reject registration and show an error."""
    response = register_user(client, password='Password1', confirm_password='Different1')
    assert response.status_code == 200, (
        f"expected the form to re-render with errors (HTTP 200) on password mismatch; "
        f"got {response.status_code} -- did the form actually accept mismatched passwords?"
    )
    expected_phrases = (b'Field must be equal to password', b'must match', b'Passwords')
    assert any(p in response.data for p in expected_phrases), (
        f"none of the expected mismatch messages {[p.decode() for p in expected_phrases]} "
        f"appeared in the rendered form"
    )

    with app.app_context():
        user_count = User.query.count()
        assert user_count == 0


def test_login_nonexistent_user(client, app):
    """Login with an email that has no account shows error."""
    response = client.post('/login', data={
        'email': 'nobody@student.uwa.edu.au',
        'password': 'Password1',
    }, follow_redirects=False)
    assert response.status_code == 200


def test_resend_otp_unauthenticated(client):
    """POST /resend-otp without pending registration redirects to /auth."""
    response = client.post('/resend-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_resend_otp_cooldown_blocked(client, app):
    """Resend OTP immediately after generation is blocked by cooldown."""
    create_pending_registration(client)
    response = client.post('/resend-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/verify-otp' in response.headers['Location']
    # Should flash cooldown error, not success
    # Follow redirects to check flash message
    response = client.post('/resend-otp', follow_redirects=True)
    assert b'wait before requesting' in response.data


def test_session_permanent_on_login(client, app):
    """Session is marked permanent after a successful login."""
    create_verified_user(app)
    login_user(client)
    with client.session_transaction() as sess:
        assert sess.permanent is True


def test_reset_password_invalid_token_post(client, app):
    """POST to reset-password with invalid token redirects to forgot-password."""
    response = client.post('/reset-password/bad-token', data={
        'password': 'NewPassword1',
        'confirm_password': 'NewPassword1',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/forgot-password' in response.headers['Location']


# ---------------------------------------------------------------------------
# New tests: OTP-first registration flow
# ---------------------------------------------------------------------------

def test_register_no_user_row_before_otp(client, app):
    """After register, no User row exists in DB and pending_registration is in session."""
    register_user(client)
    with app.app_context():
        assert User.query.all() == []
    with client.session_transaction() as sess:
        assert sess.get('pending_registration') is not None
        assert 'user_id' not in sess


def test_verify_otp_creates_user_row(client, app):
    """After valid OTP, User row exists with correct data and email_verified=True."""
    create_pending_registration(client, otp_code='111111')
    client.post('/verify-otp', data={'otp_code': '111111'}, follow_redirects=False)

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user is not None
        assert user.email_verified is True
        assert user.display_name == 'Test User'


def test_verify_otp_password_stored_correctly(client, app):
    """After valid OTP, the password hash from session is preserved."""
    create_pending_registration(client, password='SecretPass1', otp_code='222222')
    client.post('/verify-otp', data={'otp_code': '222222'}, follow_redirects=False)

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user is not None
        assert user.check_password('SecretPass1') is True


def test_verify_otp_clears_pending_registration(client, app):
    """After valid OTP, pending_registration is removed from session."""
    create_pending_registration(client, otp_code='333333')
    client.post('/verify-otp', data={'otp_code': '333333'}, follow_redirects=False)

    with client.session_transaction() as sess:
        assert 'pending_registration' not in sess
        assert 'user_id' in sess


def test_register_clears_old_unverified_row(client, app):
    """Re-registering with an old unverified email deletes the old row."""
    with app.app_context():
        old_user = User(display_name='Old', email='test@student.uwa.edu.au')
        old_user.set_password('OldPass1')
        old_user.email_verified = False
        db.session.add(old_user)
        db.session.commit()
        assert User.query.count() == 1

    register_user(client)

    # Old row deleted, new pending registration in session
    with app.app_context():
        assert User.query.count() == 0
    with client.session_transaction() as sess:
        assert sess.get('pending_registration') is not None


def test_login_deletes_unverified_user(client, app):
    """Logging in with an old unverified account deletes the row and redirects to signup."""
    with app.app_context():
        user = User(display_name='Unverified', email='test@student.uwa.edu.au')
        user.set_password('Password1')
        user.email_verified = False
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'email': 'test@student.uwa.edu.au',
        'password': 'Password1',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']

    with app.app_context():
        assert User.query.filter_by(email='test@student.uwa.edu.au').first() is None


def test_login_does_not_delete_admin(client, app):
    """Admin accounts are never deleted even if unverified."""
    with app.app_context():
        admin = User(display_name='Admin', email='admin@student.uwa.edu.au',
                     is_admin=True)
        admin.set_password('AdminPass1')
        admin.email_verified = False
        db.session.add(admin)
        db.session.commit()

    response = client.post('/login', data={
        'email': 'admin@student.uwa.edu.au',
        'password': 'AdminPass1',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']

    with app.app_context():
        admin = User.query.filter_by(email='admin@student.uwa.edu.au').first()
        assert admin is not None
        assert admin.is_admin is True


def test_pending_registration_required_redirects(client):
    """GET /verify-otp without pending_registration redirects to /auth."""
    response = client.get('/verify-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_resend_otp_updates_session(client, app):
    """Resend OTP generates a new code stored in session."""
    create_pending_registration(client, otp_code='111111')

    # Manually set otp_sent_at to 61 seconds ago to bypass cooldown
    from datetime import timedelta
    past = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=61)).isoformat()
    with client.session_transaction() as sess:
        pending = sess['pending_registration']
        pending['otp_sent_at'] = past
        sess['pending_registration'] = pending  # reassign for Flask mutation detection

    client.post('/resend-otp', follow_redirects=False)

    with client.session_transaction() as sess:
        new_otp = sess['pending_registration']['otp_code']
        assert new_otp != '111111'
        assert len(new_otp) == 6
        assert new_otp.isdigit()
