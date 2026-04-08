# Phase 1: Flask Foundation & Authentication - Research

**Researched:** 2026-04-03
**Domain:** Flask web framework, authentication, email verification, session management
**Confidence:** HIGH

## Summary

Phase 1 sets up the entire Flask application foundation from scratch and implements a complete authentication system with OTP email verification. The project currently has static HTML/CSS/JS files (landing page and auth page) that must be migrated into Flask's project structure. No Flask app, `requirements.txt`, or `app/` directory exists yet -- everything must be created.

The authentication system requires three distinct flows: (1) registration with mandatory UWA email (`@student.uwa.edu.au`) followed by OTP email verification, (2) login/logout with browser-session cookies, and (3) forgot password via email reset link. The existing `auth.html` with its jQuery tab-switching login/signup UI will be converted to Jinja2 templates, preserving the "Scholarly Curator" design system.

**Primary recommendation:** Use Flask 3.1 with Flask-SQLAlchemy 3.1.1, Flask-WTF 1.2.2 for CSRF protection and form validation, Flask-Mail 0.10.0 for SMTP email sending, and `secrets` module for OTP generation. Store OTPs and reset tokens in the database with timestamps -- avoid `itsdangerous` timed serializers for OTPs since OTPs are short numeric codes users type in, not URL tokens.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Single `app/` package with `routes.py`, `models.py`, `forms.py`, `templates/`, `static/` -- no blueprints
- **D-02:** Migrate existing root static files (`index.html`, `css/`, `js/`, `images/`) into Flask's `app/templates/` and `app/static/` structure
- **D-03:** Tailwind CSS via CDN (no build step) -- matches current landing page approach
- **D-04:** Configuration via `.env` file with python-dotenv (SECRET_KEY, DATABASE_PATH, MAIL settings)
- **D-05:** Convert existing `auth.html` tab-switching login/signup UI into Jinja2 templates -- reuse the layout, don't rebuild
- **D-06:** OTP verification on a **separate page** (not inline) after registration
- **D-07:** Email sending via **SMTP** (Gmail or similar) using Flask-Mail
- **D-08:** OTP valid for **5 minutes**, with a **resend button** (60-second cooldown)
- **D-09:** Registration fields: **email + password + display name** (email must match `@student.uwa.edu.au`)
- **D-10:** Password rules: minimum 8 characters, must include at least one number and one letter
- **D-11:** Duplicate email registration shows clear error: "An account with this email already exists"
- **D-12:** After registration, user is **blocked from accessing marketplace** until OTP is verified -- they see a verification page with resend option
- **D-13:** Sessions last **until browser is closed** (no timed session -- uses Flask's default session behavior with PERMANENT_SESSION_LIFETIME set to browser session)
- **D-14:** After login, redirect to **marketplace home page**
- **D-15:** After logout, redirect to **login page**
- **D-16:** Unverified users (registered but no OTP) can log in but see only the "verify your email" page -- cannot access marketplace
- **D-17:** Forgot password flow: user enters email -> receives email with unique reset link -> clicks link -> sets new password
- **D-18:** Reset link should expire (standard practice, similar to OTP -- researcher/planner to decide exact duration)

### Claude's Discretion
- Exact OTP generation method (length, character set)
- Reset token implementation details (token format, storage approach)
- Error message styling and flash message patterns
- Flask extension versions and dependency versions
- CSRF implementation details (Flask-WTF setup)
- Database model field specifics (exact column types, lengths)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User registration (email, password, student ID optional) | D-09 locks fields to email + password + display name. Flask-WTF form with server-side validation. Email regex for `@student.uwa.edu.au`. werkzeug `generate_password_hash` for hashing. |
| AUTH-02 | Secure login with session management | Flask session-based auth. D-13 locks to browser-session cookies. D-14 redirects to marketplace home. D-16 handles unverified user flow. |
| AUTH-04 | Logout | D-15 redirects to login page after logout. `session.clear()` pattern. |
| SEC-06 | Session security (secure cookies, timeout) | Flask `session` with `SECRET_KEY`. D-13 specifies browser-session lifetime. CSRF via Flask-WTF on all POST routes. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Required stack:** Flask (Python 3.x), SQLite (Flask-SQLAlchemy), HTML5/CSS/Tailwind/jQuery, Jinja2
- **Forbidden:** React, Angular, Vue, SASS, MySQL
- **Design authority:** `DESIGN.md` -- "Scholarly Curator" aesthetic, no borders, tonal layering, Inter + Manrope fonts
- **Testing:** pytest for unit tests, pytest for Selenium tests
- **Dev server:** `flask run`

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.1.0 | Web framework | Installed on system, course requirement |
| Flask-SQLAlchemy | 3.1.1 | ORM / database | Course requirement for SQLite, latest stable |
| Flask-WTF | 1.2.2 | Form validation + CSRF | Standard Flask form handling, auto CSRF tokens |
| Flask-Mail | 0.10.0 | SMTP email sending | Standard Flask email extension, supports TLS |
| WTForms | 3.2.1 | Form field definitions | Dependency of Flask-WTF, server-side validation |
| python-dotenv | 1.1.0 | Load `.env` config | Installed on system, standard Flask config pattern |
| itsdangerous | 2.2.0 | URL-safe timed tokens | Installed on system, for password reset links |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| email-validator | 2.3.0 | Email format validation | WTForms EmailField validation backend |
| werkzeug | 3.1.3 | Password hashing | Installed on system, `generate_password_hash` / `check_password_hash` |
| pytest | 8.3.4 | Unit testing | Test runner, installed on system |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flask-Mail | Flask-Mailman | Flask-Mailman is Django-style API wrapper, less idiomatic for Flask; Flask-Mail is simpler and more widely documented |
| itsdangerous for OTP | secrets module for OTP | itsdangerous is for URL tokens (password reset); secrets is correct for numeric OTP codes users type in |
| Flask-Login | Manual session management | Flask-Login adds complexity for minimal benefit -- we only need `session['user_id']` and a `@login_required` decorator, easily hand-rolled |

**Installation:**
```bash
pip3 install Flask-SQLAlchemy==3.1.1 Flask-WTF==1.2.2 Flask-Mail==0.10.0 email-validator==2.3.0
```

Note: Flask 3.1.0, python-dotenv 1.1.0, itsdangerous 2.2.0, werkzeug 3.1.3, and pytest 8.3.4 are already installed.

## Architecture Patterns

### Recommended Project Structure
```
uwa-marketplace/
├── app/                         # Flask application package
│   ├── __init__.py              # App factory, config, extension init
│   ├── models.py                # SQLAlchemy models (User)
│   ├── forms.py                 # WTForms form classes
│   ├── routes.py                # All route handlers
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html            # Base layout (head, nav, footer)
│   │   ├── index.html           # Landing page (migrated from root)
│   │   ├── auth.html            # Login/signup page (converted from static)
│   │   ├── verify_otp.html      # OTP verification page
│   │   ├── forgot_password.html # Forgot password form
│   │   └── reset_password.html  # Reset password form
│   └── static/                  # Static assets
│       ├── css/
│       │   └── styles.css       # Design system CSS (migrated)
│       ├── js/
│       │   └── auth.js          # Auth page JS (migrated, updated)
│       └── images/
│           └── winthrop-hall.jpg # Campus photo (migrated)
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures (app, client, db)
│   ├── test_models.py           # Model unit tests
│   └── test_auth.py             # Auth route tests
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env                         # Secrets (gitignored)
├── .env.example                 # Template for .env (committed)
├── DESIGN.md                    # Design system reference
└── .gitignore                   # Updated with Flask patterns
```

### Pattern 1: App Factory
**What:** Create Flask app in `app/__init__.py` with `create_app()` function
**When to use:** Always -- this is the standard Flask pattern, enables test configuration
**Example:**
```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
import os

db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()

def create_app(config=None):
    app = Flask(__name__)

    # Load config from .env
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///marketplace.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail config
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # Init extensions
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Register routes
    from app.routes import main
    app.register_blueprint(main)

    # Create tables
    with app.app_context():
        from app import models
        db.create_all()

    return app
```

### Pattern 2: Login Required Decorator
**What:** Custom decorator to protect routes requiring authentication
**When to use:** On every route that requires a logged-in user
**Example:**
```python
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        from app.models import User
        user = User.query.get(session['user_id'])
        if not user or not user.email_verified:
            return redirect(url_for('main.verify_otp'))
        return f(*args, **kwargs)
    return decorated_function
```

### Pattern 3: OTP Generation and Verification
**What:** Generate 6-digit numeric OTP using `secrets` module, store in database with expiry
**When to use:** Registration email verification
**Example:**
```python
import secrets
from datetime import datetime, timedelta, timezone

def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return str(secrets.randbelow(900000) + 100000)  # 100000-999999

# In User model:
# otp_code = db.Column(db.String(6), nullable=True)
# otp_created_at = db.Column(db.DateTime, nullable=True)

def is_otp_valid(user):
    """Check if user's OTP is still within 5-minute window."""
    if not user.otp_code or not user.otp_created_at:
        return False
    expiry = user.otp_created_at + timedelta(minutes=5)
    return datetime.now(timezone.utc) < expiry
```

### Pattern 4: Password Reset with Timed Token
**What:** Use `itsdangerous.URLSafeTimedSerializer` for generating password reset links
**When to use:** Forgot password flow
**Example:**
```python
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def generate_reset_token(email, secret_key):
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps({'email': email}, salt='password-reset-salt')

def verify_reset_token(token, secret_key, max_age=3600):
    """Verify reset token. Returns email if valid, None otherwise."""
    s = URLSafeTimedSerializer(secret_key)
    try:
        data = s.loads(token, salt='password-reset-salt', max_age=max_age)
        return data['email']
    except (SignatureExpired, BadSignature):
        return None
```

### Pattern 5: CSRF Token in Templates
**What:** Include CSRF tokens in all forms rendered by Jinja2
**When to use:** Every form that POSTs data
**Example:**
```html
<!-- In any Jinja2 template with a form -->
<form method="POST" action="{{ url_for('main.login') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- form fields -->
</form>
```

### Pattern 6: Flask-WTF Form Classes
**What:** Define form validation logic in `forms.py` using WTForms
**When to use:** All forms that accept user input
**Example:**
```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Regexp, ValidationError
import re

class RegistrationForm(FlaskForm):
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    email = StringField('University Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)', message='Password must contain at least one letter and one number')
    ])

    def validate_email(self, field):
        if not field.data.endswith('@student.uwa.edu.au'):
            raise ValidationError('Please use your UWA student email address')
```

### Anti-Patterns to Avoid
- **Storing plain-text passwords:** Always use `werkzeug.security.generate_password_hash` with `pbkdf2:sha256`
- **Rolling your own crypto:** Never implement custom hashing, token generation, or encryption algorithms
- **CSRF on GET requests:** Only POST/PUT/DELETE need CSRF protection; GET requests should be idempotent
- **Session in URL:** Flask sessions use cookies by default -- never put auth tokens in URL parameters
- **Using `datetime.utcnow()`:** Deprecated in Python 3.12+. Use `datetime.now(timezone.utc)` instead
- **Importing db in routes before app creation:** Use `from app import db` inside functions or use app context properly
- **Hardcoding SMTP credentials:** Always use `.env` with `python-dotenv`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash function | `werkzeug.security.generate_password_hash` / `check_password_hash` | Handles salt generation, uses proven pbkdf2, constant-time comparison |
| CSRF protection | Manual token generation and validation | `Flask-WTF CSRFProtect` | Handles per-session tokens, automatic validation, secure defaults |
| Email validation regex | Custom regex pattern | `WTForms Email()` validator + `email-validator` package | Edge cases in email RFC specs are extremely complex |
| Form validation | Manual request.form parsing | `Flask-WTF FlaskForm.validate_on_submit()` | Combines CSRF check + field validation + error messages in one call |
| Secure random OTP | `random.randint()` | `secrets.randbelow()` | `random` module is not cryptographically secure |
| Reset token generation | Custom token encoding | `itsdangerous.URLSafeTimedSerializer` | Handles signing, tamper-proofing, and time-based expiry |

**Key insight:** Flask-WTF + werkzeug together solve password hashing, CSRF protection, form validation, and email validation. These are the four security fundamentals for authentication.

## Common Pitfalls

### Pitfall 1: Flask-WTF CSRF Blocking AJAX Requests
**What goes wrong:** jQuery form submissions fail with 400 Bad Request because CSRF token is missing
**Why it happens:** AJAX requests don't automatically include CSRF tokens
**How to avoid:** Include CSRF token in a meta tag in base template, and configure jQuery to send it as `X-CSRFToken` header, OR use standard form submissions (no AJAX) for auth forms
**Warning signs:** 400 errors in browser console on form POST

### Pitfall 2: SQLite Database File Location
**What goes wrong:** Database file created in unexpected location or not persisted
**Why it happens:** Relative path in `SQLALCHEMY_DATABASE_URI` resolves relative to current working directory
**How to avoid:** Use `os.path.join` with `basedir` to construct absolute path: `sqlite:///' + os.path.join(basedir, 'marketplace.db')`
**Warning signs:** Tables re-created on every restart, "database is locked" errors

### Pitfall 3: Flask-Mail Connection Errors in Development
**What goes wrong:** App crashes on registration because mail server is unreachable
**Why it happens:** Gmail requires App Passwords (not regular passwords), or dev environment has no SMTP access
**How to avoid:** (1) Use `app.config['MAIL_SUPPRESS_SEND'] = True` in testing, (2) use `app.config['MAIL_DEFAULT_SENDER']` always, (3) wrap `mail.send()` in try/except, (4) provide clear setup docs for App Passwords
**Warning signs:** SMTPAuthenticationError, ConnectionRefusedError during registration

### Pitfall 4: Session Not Persisting Across Requests
**What goes wrong:** User logs in but appears logged out on next request
**Why it happens:** `SECRET_KEY` not set (Flask can't sign cookies), or cookie domain mismatch
**How to avoid:** Always set `SECRET_KEY` from `.env`, never use default or empty value
**Warning signs:** `session` dict is empty on subsequent requests despite being set

### Pitfall 5: Flask-SQLAlchemy 3.x Breaking Changes
**What goes wrong:** Code written for Flask-SQLAlchemy 2.x fails (no `query` property, different `db.create_all()` behavior)
**Why it happens:** Flask-SQLAlchemy 3.x removed deprecated APIs
**How to avoid:** Use `db.Model` base class, use `User.query.filter_by()` (still works in 3.1.x), call `db.create_all()` within `app.app_context()`
**Warning signs:** AttributeError on model classes, "working outside of application context" errors

### Pitfall 6: OTP Resend Rate Limiting
**What goes wrong:** User spams resend button, generating many emails and OTPs
**Why it happens:** No cooldown between resend requests
**How to avoid:** Track `otp_created_at` and only allow resend after 60 seconds. Return same OTP if within 5-minute window (don't regenerate). Show countdown timer on frontend.
**Warning signs:** Excessive email sending, user gets confused by multiple valid OTPs

### Pitfall 7: Password Reset Token Reuse
**What goes wrong:** User clicks reset link twice, token still valid after first use
**Why it happens:** Token is not invalidated after successful password reset
**How to avoid:** After successful password reset, clear the token or mark it as used. Simplest approach: store `password_changed_at` on User model and check that the token was generated AFTER the last password change.
**Warning signs:** Old reset links still work after password was already changed

## Code Examples

Verified patterns from official sources:

### User Model
```python
# app/models.py
from app import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

### Registration Route Pattern
```python
# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from app.forms import RegistrationForm
from app.models import User
from app import db, mail
from flask_mail import Message

main = Blueprint('main', __name__)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # With Flask-WTF form:
        form = RegistrationForm()
        if form.validate_on_submit():
            # Check duplicate email
            existing = User.query.filter_by(email=form.email.data).first()
            if existing:
                flash('An account with this email already exists.', 'error')
                return render_template('auth.html', form=form, active_tab='signup')

            user = User(display_name=form.display_name.data, email=form.email.data)
            user.set_password(form.password.data)
            user.otp_code = generate_otp()
            user.otp_created_at = datetime.now(timezone.utc)
            db.session.add(user)
            db.session.commit()

            # Send OTP email
            send_otp_email(user.email, user.otp_code)

            # Log user in (session) but redirect to verification
            session['user_id'] = user.id
            return redirect(url_for('main.verify_otp'))

    return render_template('auth.html', form=form, active_tab='signup')
```

### Flask-Mail Message Sending
```python
# Source: Flask-Mail 0.10.0 README (github.com/pallets-eco/flask-mail)
def send_otp_email(recipient_email, otp_code):
    msg = Message(
        subject='Your UWA Swap-Meet Verification Code',
        recipients=[recipient_email],
        body=f'Your verification code is: {otp_code}\n\nThis code expires in 5 minutes.'
    )
    mail.send(msg)
```

### CSRF Token in Base Template
```html
<!-- app/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{% block title %}UWA Swap-Meet{% endblock %}</title>
    <!-- Fonts, Tailwind CDN, etc. -->
</head>
<body>
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    {% for category, message in messages %}
    <div class="flash-message flash-{{ category }}">{{ message }}</div>
    {% endfor %}
    {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}
</body>
</html>
```

### Login/Signup Template (Converted from auth.html)
```html
<!-- app/templates/auth.html -->
{% extends "base.html" %}
{% block title %}UWA Swap-Meet | Authentication{% endblock %}

{% block content %}
<!-- Reuse existing auth.html structure, but with Jinja2:
     - Replace css/styles.css with {{ url_for('static', filename='css/styles.css') }}
     - Replace images/winthrop-hall.jpg with {{ url_for('static', filename='images/winthrop-hall.jpg') }}
     - Add csrf_token() hidden input to each form
     - Add action attributes to forms pointing to Flask routes
     - Add flash message display area for errors
-->
<body class="auth-page">
    <div class="auth-background" style="background-image: url('{{ url_for('static', filename='images/winthrop-hall.jpg') }}');"></div>
    <!-- ... rest of auth.html structure ... -->

    <form method="POST" action="{{ url_for('main.login') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <!-- login form fields -->
    </form>
</body>
{% endblock %}
```

### run.py Entry Point
```python
# run.py
from dotenv import load_dotenv
load_dotenv()  # Load .env before importing app

from app import create_app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 deprecated | Use timezone-aware datetimes everywhere |
| Flask-SQLAlchemy 2.x `query` | Flask-SQLAlchemy 3.x `db.Model.query` still works | 3.0 (2022) | 3.1.1 supports both styles, prefer `Model.query.filter_by()` |
| `itsdangerous.TimedJSONWebSignatureSerializer` | `itsdangerous.URLSafeTimedSerializer` | itsdangerous 2.0 (2021) | Old class completely removed, use URLSafeTimedSerializer |
| `random.randint()` for OTP | `secrets.randbelow()` for OTP | Always | `random` is not cryptographically secure |
| Gmail "less secure apps" | Gmail App Passwords | 2022 | Must enable 2FA and generate app-specific password |

**Deprecated/outdated:**
- `datetime.utcnow()`: Deprecated in Python 3.12. Use `datetime.now(timezone.utc)`.
- `itsdangerous.TimedJSONWebSignatureSerializer`: Removed in itsdangerous 2.0. Use `URLSafeTimedSerializer`.
- `Flask-SQLAlchemy` `_ModelCommand`: Removed in 3.0. Use `db.session.add()` + `db.session.commit()`.

## Open Questions

1. **SMTP Provider for Development**
   - What we know: D-07 specifies SMTP (Gmail or similar). Gmail requires App Passwords with 2FA enabled.
   - What's unclear: Whether the developer has a Gmail account with 2FA enabled, or prefers an alternative.
   - Recommendation: Use Gmail App Passwords for production. For local dev, set `MAIL_SUPPRESS_SEND=True` in `.env` and log OTPs to console. Consider providing `MAIL_SUPPRESS_SEND` flag so dev can test without real email.

2. **Marketplace Home Page Content for Phase 1**
   - What we know: D-14 says redirect to marketplace home page after login. The marketplace doesn't exist yet (Phase 2).
   - What's unclear: What should the post-login page show during Phase 1?
   - Recommendation: Create a minimal placeholder `dashboard.html` with a welcome message and logout button. This gets replaced in Phase 2.

3. **Password Reset Token Expiry Duration**
   - What we know: D-18 says standard practice similar to OTP. OTP is 5 minutes.
   - What's unclear: Exact duration for reset link.
   - Recommendation: 1 hour (3600 seconds) for password reset links. This is industry standard (same as Flask's default `max_age` for itsdangerous). 5 minutes is too short for email-based links (user might be on mobile, switching apps).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | Flask runtime | Yes | 3.13.5 | -- |
| Flask | Web framework | Yes | 3.1.0 | -- |
| Werkzeug | Password hashing | Yes | 3.1.3 | -- |
| python-dotenv | Config loading | Yes | 1.1.0 | -- |
| itsdangerous | Reset tokens | Yes | 2.2.0 | -- |
| email-validator | Email validation | Yes | 2.3.0 | -- |
| pytest | Testing | Yes | 8.3.4 | -- |
| pip | Package manager | Yes | 26.0.1 | -- |
| Flask-SQLAlchemy | ORM | No | -- | Install from PyPI (3.1.1) |
| Flask-WTF | Forms + CSRF | No | -- | Install from PyPI (1.2.2) |
| Flask-Mail | Email sending | No | -- | Install from PyPI (0.10.0) |
| SMTP server | Email delivery | No | -- | Use Gmail App Password or MAIL_SUPPRESS_SEND |

**Missing dependencies with no fallback:**
- Flask-SQLAlchemy, Flask-WTF, Flask-Mail: Must install via `pip3 install Flask-SQLAlchemy Flask-WTF Flask-Mail`

**Missing dependencies with fallback:**
- SMTP server: Use `MAIL_SUPPRESS_SEND=True` for development without email sending. Log OTPs to console during dev.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | None -- see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | User registration with valid data creates account | unit | `pytest tests/test_auth.py::test_register_success -x` | No -- Wave 0 |
| AUTH-01 | Registration rejects non-UWA email | unit | `pytest tests/test_auth.py::test_register_invalid_email -x` | No -- Wave 0 |
| AUTH-01 | Registration rejects duplicate email | unit | `pytest tests/test_auth.py::test_register_duplicate_email -x` | No -- Wave 0 |
| AUTH-01 | Registration rejects weak password | unit | `pytest tests/test_auth.py::test_register_weak_password -x` | No -- Wave 0 |
| AUTH-02 | Login with correct credentials succeeds | unit | `pytest tests/test_auth.py::test_login_success -x` | No -- Wave 0 |
| AUTH-02 | Login with wrong password fails | unit | `pytest tests/test_auth.py::test_login_wrong_password -x` | No -- Wave 0 |
| AUTH-02 | Unverified user redirected to verify page | unit | `pytest tests/test_auth.py::test_unverified_redirect -x` | No -- Wave 0 |
| AUTH-04 | Logout clears session | unit | `pytest tests/test_auth.py::test_logout -x` | No -- Wave 0 |
| SEC-06 | CSRF token required on POST routes | unit | `pytest tests/test_auth.py::test_csrf_required -x` | No -- Wave 0 |
| SEC-06 | Password hashing uses salt | unit | `pytest tests/test_models.py::test_password_hashing -x` | No -- Wave 0 |
| AUTH-01 | OTP generation and expiry | unit | `pytest tests/test_models.py::test_otp_generation -x` | No -- Wave 0 |
| AUTH-01 | Password reset token generation and verification | unit | `pytest tests/test_models.py::test_reset_token -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` -- pytest fixtures (Flask app client, test database, test config)
- [ ] `tests/test_auth.py` -- covers AUTH-01, AUTH-02, AUTH-04, SEC-06 route tests
- [ ] `tests/test_models.py` -- covers password hashing, OTP, reset token tests
- [ ] Framework config: No pytest.ini needed (conftest.py handles setup)

## Sources

### Primary (HIGH confidence)
- PyPI registry (pip3 index versions) -- verified package versions: Flask-SQLAlchemy 3.1.1, Flask-WTF 1.2.2, Flask-Mail 0.10.0, WTForms 3.2.1
- Flask-SQLAlchemy quickstart docs (flask-sqlalchemy.readthedocs.io) -- model definition, db.create_all() pattern
- Flask-Mail GitHub README (github.com/pallets-eco/flask-mail) -- configuration and Message class API
- Existing project files: `auth.html`, `css/styles.css`, `js/auth.js`, `index.html`, `DESIGN.md` -- all read and analyzed
- Local environment: Python 3.13.5, Flask 3.1.0, Werkzeug 3.1.3, itsdangerous 2.2.0, python-dotenv 1.1.0 verified installed

### Secondary (MEDIUM confidence)
- Flask-WTF CSRF protection patterns -- well-established, training data consistent with official docs
- itsdangerous URLSafeTimedSerializer -- API documented, consistent across multiple sources
- werkzeug.security password hashing -- documented in Werkzeug docs, stable API

### Tertiary (LOW confidence)
- Gmail App Password configuration -- known requirement but not verified against live Google account settings in 2026

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against PyPI, Flask 3.1.0 confirmed installed locally
- Architecture: HIGH -- patterns from official Flask docs and Flask-SQLAlchemy quickstart
- Pitfalls: HIGH -- well-documented issues with Flask 3.x + SQLAlchemy 3.x migration, CSRF, and SMTP config

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable libraries, low churn expected)
