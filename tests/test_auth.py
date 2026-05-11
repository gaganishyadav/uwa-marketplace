"""Integration tests for auth routes: register, login, OTP, logout, password reset."""

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


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

def test_register_success(client, app):
    """Valid registration creates user and redirects to OTP verification."""
    response = register_user(client)
    assert response.status_code == 302
    assert '/verify-otp' in response.headers['Location']

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user is not None
        assert user.email_verified is False
        assert user.display_name == 'Test User'


def test_register_invalid_email(client, app):
    """Rejects non-UWA email domain."""
    response = register_user(client, email='test@gmail.com')
    assert response.status_code == 200  # Re-renders form with errors

    with app.app_context():
        assert User.query.count() == 0


def test_register_duplicate_email(client, app):
    """Shows 'already exists' error for duplicate email."""
    # Create first user
    register_user(client)
    # Try to register again with same email
    response = register_user(client)
    assert response.status_code == 200

    with app.app_context():
        # Flash message is in the rendered page
        assert User.query.count() == 1


def test_register_weak_password(client, app):
    """Rejects password that is too short or lacks complexity."""
    response = register_user(client, password='pass', confirm_password='pass')
    assert response.status_code == 200  # Re-renders form with errors

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


def test_unverified_redirect(client, app):
    """Unverified user is redirected to OTP page after login."""
    # Register user (which leaves them unverified)
    register_user(client)
    # Login with same credentials
    response = client.post('/login', data={
        'email': 'test@student.uwa.edu.au',
        'password': 'Password1',
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/verify-otp' in response.headers['Location']


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

    # Subsequent access to protected route redirects to /auth
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
    """Correct OTP verifies user and redirects to dashboard."""
    with app.app_context():
        register_user(client)
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        otp = user.otp_code

    response = client.post('/verify-otp', data={
        'otp_code': otp,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user.email_verified is True


def test_verify_otp_invalid(client, app):
    """Wrong OTP shows error, user stays unverified."""
    register_user(client)
    response = client.post('/verify-otp', data={
        'otp_code': '000000',
    }, follow_redirects=False)
    assert response.status_code == 200  # Re-renders form with error

    with app.app_context():
        user = User.query.filter_by(email='test@student.uwa.edu.au').first()
        assert user.email_verified is False


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

    # GET renders form
    response = client.get(f'/reset-password/{token}')
    assert response.status_code == 200

    # POST changes password
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


def test_dashboard_unverified_redirects(client, app):
    """Unverified user visiting /dashboard is redirected to /verify-otp."""
    register_user(client)
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/verify-otp' in response.headers['Location']


def test_verify_otp_unauthenticated(client):
    """GET /verify-otp without login redirects to /auth."""
    response = client.get('/verify-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_verify_otp_already_verified(client, app):
    """Verified user visiting /verify-otp is redirected to dashboard."""
    create_verified_user(app)
    login_user(client)
    response = client.get('/verify-otp', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


def test_stale_session_verify_otp(client, app):
    """Session with a deleted user's ID redirects to /auth from /verify-otp."""
    with client.session_transaction() as sess:
        sess['user_id'] = 99999  # non-existent user

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
    assert response.status_code == 200
    assert b'Field must be equal to password' in response.data or b'must match' in response.data or b'Passwords' in response.data

    with app.app_context():
        assert User.query.count() == 0


def test_login_nonexistent_user(client, app):
    """Login with an email that has no account shows error."""
    response = client.post('/login', data={
        'email': 'nobody@student.uwa.edu.au',
        'password': 'Password1',
    }, follow_redirects=False)
    assert response.status_code == 200


def test_resend_otp_unauthenticated(client):
    """POST /resend-otp without login redirects to /auth."""
    response = client.post('/resend-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


def test_resend_otp_cooldown_blocked(client, app):
    """Resend OTP immediately after generation is blocked by cooldown."""
    register_user(client)
    response = client.post('/resend-otp', follow_redirects=False)
    assert response.status_code == 302
    assert '/verify-otp' in response.headers['Location']


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
# Login brute-force lockout tests
# ---------------------------------------------------------------------------

def test_login_lockout_triggers_after_max_attempts(client, app):
    """After 5 wrong-password attempts, the user is locked out."""
    create_verified_user(app)
    for _ in range(User.MAX_LOGIN_ATTEMPTS):
        login_user(client, password='WrongPassword1')

    with app.app_context():
        user = User.query.filter_by(email='verified@student.uwa.edu.au').first()
        assert user.is_locked_out() is True
        assert user.lockout_until is not None
        # Counter is reset to 0 once the lockout is applied
        assert user.failed_login_attempts == 0


def test_login_blocked_during_lockout_even_with_correct_password(client, app):
    """A locked-out account cannot log in even if the correct password is supplied."""
    from datetime import timedelta
    from app.models import _utcnow

    create_verified_user(app)
    with app.app_context():
        user = User.query.filter_by(email='verified@student.uwa.edu.au').first()
        user.lockout_until = _utcnow() + timedelta(minutes=10)
        db.session.commit()

    response = login_user(client)  # correct credentials
    assert response.status_code == 200  # re-renders form, NO redirect
    assert b'temporarily locked' in response.data.lower() or b'locked' in response.data.lower()


def test_login_lockout_expires_naturally(client, app):
    """Once lockout_until is in the past, the user can log in again."""
    from datetime import timedelta
    from app.models import _utcnow

    create_verified_user(app)
    with app.app_context():
        user = User.query.filter_by(email='verified@student.uwa.edu.au').first()
        user.lockout_until = _utcnow() - timedelta(minutes=1)  # already expired
        db.session.commit()

    response = login_user(client)
    assert response.status_code == 302  # successful redirect


def test_successful_login_clears_failure_state(client, app):
    """A correct password resets failed_login_attempts and lockout_until."""
    create_verified_user(app)
    # Pre-load some failed attempts (below threshold so account stays unlocked)
    with app.app_context():
        user = User.query.filter_by(email='verified@student.uwa.edu.au').first()
        user.failed_login_attempts = 3
        db.session.commit()

    login_user(client)  # correct password

    with app.app_context():
        user = User.query.filter_by(email='verified@student.uwa.edu.au').first()
        assert user.failed_login_attempts == 0
        assert user.lockout_until is None


def test_login_nonexistent_email_does_not_persist_anything(client, app):
    """Hitting /login with an unknown email must not create a user or write to DB."""
    response = client.post('/login', data={
        'email': 'nobody@student.uwa.edu.au',
        'password': 'WrongPassword1',
    })
    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email='nobody@student.uwa.edu.au').first() is None
