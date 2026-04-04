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
    """Logout clears session and redirects to auth page."""
    create_verified_user(app)
    login_user(client)

    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']

    # Subsequent access to protected route redirects to /auth
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']


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
