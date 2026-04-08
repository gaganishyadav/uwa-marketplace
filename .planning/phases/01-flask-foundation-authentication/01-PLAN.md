---
phase: 01-flask-foundation-authentication
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - .env.example
  - .gitignore
  - run.py
  - app/__init__.py
  - app/models.py
  - app/forms.py
  - tests/conftest.py
  - tests/test_models.py
autonomous: true
requirements:
  - AUTH-01
  - SEC-06

must_haves:
  truths:
    - "Application starts and responds to HTTP requests without errors"
    - "User model stores password as salted hash, never plaintext"
    - "OTP codes are 6-digit cryptographically secure random numbers with 5-minute expiry"
    - "Password reset tokens are signed, tamper-proof, and expire after 1 hour"
    - "Registration form validates UWA student email suffix and password complexity"
    - "All tests pass with pytest against in-memory SQLite database"
  artifacts:
    - path: "app/__init__.py"
      provides: "Flask app factory with db, csrf, mail extensions"
      exports: ["create_app", "db", "csrf", "mail"]
    - path: "app/models.py"
      provides: "User model with password hashing, OTP, and reset token methods"
      exports: ["User"]
    - path: "app/forms.py"
      provides: "WTForms classes for registration, login, OTP, forgot/reset password"
      exports: ["RegistrationForm", "LoginForm", "OTPForm", "ForgotPasswordForm", "ResetPasswordForm"]
    - path: "tests/conftest.py"
      provides: "pytest fixtures for Flask test client and test database"
      exports: ["app", "client"]
    - path: "tests/test_models.py"
      provides: "Unit tests for password hashing, OTP generation, and reset tokens"
  key_links:
    - from: "app/models.py"
      to: "app/__init__.py"
      via: "from app import db"
      pattern: "from app import db"
    - from: "app/forms.py"
      to: "app/models.py"
      via: "User.query.filter_by for duplicate email check"
      pattern: "User\\.query\\.filter_by"
    - from: "tests/conftest.py"
      to: "app/__init__.py"
      via: "create_app with test config"
      pattern: "create_app"
---

<objective>
Create the Flask application foundation with app factory, User model with authentication methods, WTForms validation classes, and the test infrastructure. This is the backend skeleton that Plan 02 will wire up with routes and templates.

Purpose: Establish all data contracts (model), validation rules (forms), and security primitives (hashing, OTP, reset tokens) before building routes. Tests prove the backend logic works independently of HTTP.
Output: Runnable Flask app factory, User model, form classes, passing test suite for model-level logic.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-flask-foundation-authentication/01-CONTEXT.md
@.planning/phases/01-flask-foundation-authentication/01-RESEARCH.md
@.planning/phases/01-flask-foundation-authentication/01-VALIDATION.md
@DESIGN.md
@.planning/codebase/ARCHITECTURE.md
@.planning/codebase/STRUCTURE.md
@.planning/codebase/CONVENTIONS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Flask app factory, configuration, and dependencies</name>
  <files>requirements.txt, .env.example, .gitignore, run.py, app/__init__.py</files>
  <read_first>
    DESIGN.md (for understanding project context)
    .planning/phases/01-flask-foundation-authentication/01-CONTEXT.md (for locked decisions D-01, D-03, D-04)
    .planning/phases/01-flask-foundation-authentication/01-RESEARCH.md (for standard stack versions and app factory pattern)
  </read_first>
  <action>
Create the Flask application foundation from scratch. The entire app/ directory does not exist yet.

**1. Create `requirements.txt`** with pinned versions:
```
Flask==3.1.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
Flask-Mail==0.10.0
WTForms==3.2.1
python-dotenv==1.1.0
itsdangerous==2.2.0
email-validator==2.3.0
werkzeug==3.1.3
pytest==8.3.4
```

**2. Create `.env.example`** (committed template, NOT .env itself):
```
SECRET_KEY=change-this-to-a-random-string
DATABASE_URL=sqlite:///marketplace.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
MAIL_SUPPRESS_SEND=true
```

**3. Update `.gitignore`** -- read the existing .gitignore first, then append these entries if not present:
```
# Flask
instance/
*.db
.env
__pycache__/
*.pyc
```

**4. Create `run.py`** at project root:
```python
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

**5. Create `app/__init__.py`** with app factory (per D-01 single package, no blueprints):
```python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()

def create_app(config=None):
    app = Flask(__name__)

    # Configuration from .env (per D-04)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'marketplace.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail config (per D-07)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    app.config['MAIL_SUPPRESS_SEND'] = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() == 'true'

    # Session config (per D-13 -- browser session lifetime)
    app.config['PERMANENT_SESSION_LIFETIME'] = None  # Browser session only

    # Override config for testing
    if config:
        app.config.update(config)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Import routes (will be created in Plan 02)
    # For now, register a simple index route so the app doesn't 404 on /
    @app.route('/')
    def index():
        return '<h1>UWA Swap-Meet</h1><p>App is running. Routes will be added in Plan 02.</p>'

    # Create database tables
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
```

**6. Install dependencies:**
```bash
pip3 install -r requirements.txt
```

**7. Verify Flask app starts:**
```bash
python3 -c "from app import create_app; app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}); print('App factory works:', app.name)"
```
  </action>
  <verify>
    <automated>python3 -c "from app import create_app; app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}); assert app.config['SECRET_KEY']; print('PASS: app factory')" && python3 -c "import flask_sqlalchemy; import flask_wtf; import flask_mail; print('PASS: deps')" && test -f requirements.txt && test -f .env.example && test -f run.py && test -f app/__init__.py</automated>
  </verify>
  <done>
    - requirements.txt exists with all pinned dependencies
    - .env.example exists with all config keys (SECRET_KEY, DATABASE_URL, MAIL_*)
    - .gitignore includes .env, __pycache__/, *.db
    - run.py loads dotenv and creates app
    - app/__init__.py exports create_app, db, csrf, mail
    - All dependencies install successfully
    - App factory creates a working Flask app instance
  </done>
</task>

<task type="auto">
  <name>Task 2: Create User model, form classes, and model-level tests</name>
  <files>app/models.py, app/forms.py, tests/conftest.py, tests/test_models.py</files>
  <read_first>
    app/__init__.py (created in Task 1 -- need db import, app factory pattern)
    .planning/phases/01-flask-foundation-authentication/01-CONTEXT.md (for D-08, D-09, D-10, D-11, D-17, D-18)
    .planning/phases/01-flask-foundation-authentication/01-RESEARCH.md (for User model pattern, OTP generation, reset token pattern, form class pattern)
    .planning/phases/01-flask-foundation-authentication/01-VALIDATION.md (for test IDs and expected test commands)
  </read_first>
  <action>
Create the User model with all auth methods, WTForms classes with validation, pytest fixtures, and model-level unit tests.

**1. Create `app/models.py`:**
```python
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
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
        self.otp_created_at = datetime.now(timezone.utc)
        return self.otp_code

    def is_otp_valid(self, code):
        """Check if provided OTP matches and is within 5-minute window (per D-08)."""
        if not self.otp_code or not self.otp_created_at:
            return False
        if self.otp_code != code:
            return False
        expiry = self.otp_created_at + timedelta(minutes=5)
        return datetime.now(timezone.utc) < expiry

    def can_resend_otp(self):
        """Check if 60-second cooldown has passed since last OTP (per D-08)."""
        if not self.otp_created_at:
            return True
        cooldown = self.otp_created_at + timedelta(seconds=60)
        return datetime.now(timezone.utc) >= cooldown

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
```

**2. Create `app/forms.py`:**
```python
import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
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
```

**3. Create `tests/conftest.py`:**
```python
import pytest
from app import create_app, db as _db


@pytest.fixture
def app():
    """Create application for testing with in-memory SQLite."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for simpler test POSTs
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_DEFAULT_SENDER': 'test@example.com',
    })

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()
```

**4. Create `tests/test_models.py`:**

Write tests covering these behaviors (matching VALIDATION.md test IDs):

- `test_password_hashing`: Create user, set password, verify hash is not plaintext, check_password returns True for correct password and False for wrong password. Verify two users with same password get different hashes (salt).

- `test_otp_generation`: Create user, generate OTP, verify it is a 6-digit string (100000-999999). Verify is_otp_valid returns True with correct code. Verify is_otp_valid returns False with wrong code.

- `test_otp_expiry`: Create user, generate OTP, manually set otp_created_at to 6 minutes ago, verify is_otp_valid returns False.

- `test_otp_resend_cooldown`: Create user, generate OTP, verify can_resend_otp returns False immediately, manually set otp_created_at to 61 seconds ago, verify can_resend_otp returns True.

- `test_reset_token_generation_and_verification`: Generate a reset token for an email, verify it returns the same email. Verify with wrong secret_key returns None.

- `test_reset_token_expiry`: Generate a reset token, verify with max_age=0 returns None (expired).

- `test_user_default_fields`: Create user with display_name and email, verify email_verified defaults to False, created_at is set.

All tests must use the `app` fixture from conftest.py (provides app context for database operations).
  </action>
  <verify>
    <automated>cd /Users/sawetr/Documents/uwa-marketplace && pytest tests/test_models.py -v</automated>
  </verify>
  <done>
    - app/models.py has User class with: id, display_name, email, password_hash, email_verified, otp_code, otp_created_at, created_at fields
    - User.set_password hashes with werkzeug (not plaintext)
    - User.check_password verifies correctly
    - User.generate_otp produces 6-digit code, is_otp_valid checks within 5-min window
    - User.can_resend_otp enforces 60-second cooldown
    - User.generate_reset_token / verify_reset_token use URLSafeTimedSerializer with 1-hour expiry
    - app/forms.py has RegistrationForm (validates @student.uwa.edu.au, password complexity, confirm match), LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm
    - tests/conftest.py provides app and client fixtures with in-memory SQLite
    - tests/test_models.py: all 7 tests pass (password hashing, OTP generation, OTP expiry, OTP cooldown, reset token, reset token expiry, user defaults)
  </done>
</task>

</tasks>

<verification>
1. `python3 -c "from app import create_app; app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}); print('OK')"` -- app factory works
2. `pytest tests/test_models.py -v` -- all model tests pass
3. `pip3 list | grep -i flask` -- Flask, Flask-SQLAlchemy, Flask-WTF, Flask-Mail all installed
</verification>

<success_criteria>
- Flask app initializes without errors
- User model creates, hashes passwords, generates/verifies OTPs, generates/verifies reset tokens
- All form classes validate correctly (unit testable via model tests)
- pytest runs and all 7+ tests in test_models.py pass
- requirements.txt has all 10 pinned dependencies
</success_criteria>

<output>
After completion, create `.planning/phases/01-flask-foundation-authentication/01-SUMMARY.md`
</output>
