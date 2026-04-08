---
phase: 01-flask-foundation-authentication
plan: 02
type: execute
wave: 2
depends_on: ["01"]
files_modified:
  - app/__init__.py
  - app/routes.py
  - app/templates/base.html
  - app/templates/auth.html
  - app/templates/verify_otp.html
  - app/templates/forgot_password.html
  - app/templates/reset_password.html
  - app/templates/dashboard.html
  - app/static/css/styles.css
  - app/static/js/auth.js
  - app/static/images/winthrop-hall.jpg
  - tests/test_auth.py
autonomous: false
requirements:
  - AUTH-01
  - AUTH-02
  - AUTH-04
  - SEC-06

must_haves:
  truths:
    - "User can register with email, password, display name and is redirected to OTP verification page"
    - "User can log in with correct credentials and is redirected to marketplace dashboard"
    - "User can log out and is redirected to login page"
    - "Unverified users see only the verification page after login"
    - "User can request a password reset and receives a link"
    - "User can set a new password via valid reset link"
    - "CSRF tokens are present on all forms"
    - "All existing static files are migrated into Flask app structure"
  artifacts:
    - path: "app/routes.py"
      provides: "All auth route handlers via init_routes(app) function: register, login, logout, verify_otp, forgot_password, reset_password"
      exports: ["init_routes"]
    - path: "app/templates/base.html"
      provides: "Base Jinja2 layout with head, flash messages, CSRF meta tag, Tailwind CDN"
    - path: "app/templates/auth.html"
      provides: "Login/signup page converted from existing auth.html with Jinja2 + CSRF"
    - path: "app/templates/verify_otp.html"
      provides: "OTP verification page with resend button"
    - path: "app/templates/forgot_password.html"
      provides: "Email entry form for password reset"
    - path: "app/templates/reset_password.html"
      provides: "New password entry form for reset flow"
    - path: "app/templates/dashboard.html"
      provides: "Minimal placeholder page shown after login"
    - path: "tests/test_auth.py"
      provides: "Integration tests for all auth routes"
      contains: "test_register_success"
  key_links:
    - from: "app/templates/auth.html"
      to: "app/routes.py"
      via: "form action=url_for routes"
      pattern: "url_for\\('login'\\)"
    - from: "app/routes.py"
      to: "app/models.py"
      via: "User.query and user.set_password / check_password"
      pattern: "User\\.query\\.filter_by"
    - from: "app/routes.py"
      to: "app/__init__.py"
      via: "db.session.add, mail.send"
      pattern: "db\\.session\\.(add|commit)"
    - from: "app/templates/base.html"
      to: "Flask-WTF"
      via: "csrf_token() in meta tag"
      pattern: "csrf_token\\(\\)"
---

<objective>
Wire the Flask backend to HTTP routes and Jinja2 templates. Migrate existing static files (auth.html, styles.css, auth.js, campus image) into Flask's app/ structure. Convert the existing auth page from static HTML to dynamic Jinja2 templates. Implement all auth routes (register, login, logout, OTP verification, forgot/reset password). Create integration tests for all auth flows.

Purpose: Deliver a working end-to-end authentication system where users can register, verify email, log in, log out, and reset their password -- all through the browser with the existing design system.
Output: Fully functional auth system with passing route tests, ready for manual browser verification.
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
@.planning/phases/01-flask-foundation-authentication/01-SUMMARY.md
@DESIGN.md
@.planning/codebase/ARCHITECTURE.md
@.planning/codebase/STRUCTURE.md
</context>

<interfaces>
<!-- Key types and contracts the executor needs. Created in Plan 01. -->

From app/__init__.py:
```python
db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()

def create_app(config=None) -> Flask:
    # Returns configured Flask app with db, csrf, mail initialized
```

From app/models.py:
```python
class User(db.Model):
    id: int  # primary key
    display_name: str  # max 50
    email: str  # max 120, unique
    password_hash: str  # max 256
    email_verified: bool  # default False
    otp_code: str  # max 6, nullable
    otp_created_at: datetime  # nullable
    created_at: datetime

    def set_password(self, password: str) -> None
    def check_password(self, password: str) -> bool
    def generate_otp(self) -> str  # returns 6-digit code
    def is_otp_valid(self, code: str) -> bool  # 5-min window
    def can_resend_otp(self) -> bool  # 60-sec cooldown

    @staticmethod
    def generate_reset_token(email: str, secret_key: str) -> str

    @staticmethod
    def verify_reset_token(token: str, secret_key: str, max_age: int = 3600) -> str | None
```

From app/forms.py:
```python
class RegistrationForm(FlaskForm):
    display_name: StringField  # 2-50 chars
    email: StringField  # must end @student.uwa.edu.au
    password: PasswordField  # 8+ chars, 1 letter + 1 number
    confirm_password: PasswordField  # must match password
    def validate_email_duplicate() -> bool  # True if duplicate

class LoginForm(FlaskForm):
    email: StringField
    password: PasswordField

class OTPForm(FlaskForm):
    otp_code: StringField  # exactly 6 chars

class ForgotPasswordForm(FlaskForm):
    email: StringField

class ResetPasswordForm(FlaskForm):
    password: PasswordField  # same rules as RegistrationForm
    confirm_password: PasswordField
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Create auth routes, migrate templates, and wire static files</name>
  <files>app/__init__.py, app/routes.py, app/templates/base.html, app/templates/auth.html, app/templates/verify_otp.html, app/templates/forgot_password.html, app/templates/reset_password.html, app/templates/dashboard.html, app/static/css/styles.css, app/static/js/auth.js, app/static/images/winthrop-hall.jpg</files>
  <read_first>
    app/__init__.py (from Plan 01 -- need to update to call init_routes)
    app/models.py (from Plan 01 -- User model interface)
    app/forms.py (from Plan 01 -- form classes)
    auth.html (existing static auth page -- to convert to Jinja2)
    css/styles.css (existing CSS -- to copy to app/static/)
    js/auth.js (existing JS -- to copy and update)
    DESIGN.md (design system rules for templates)
    .planning/phases/01-flask-foundation-authentication/01-CONTEXT.md (for D-01 through D-18)
    .planning/phases/01-flask-foundation-authentication/01-RESEARCH.md (for route patterns and template examples)
  </read_first>
  <action>
Wire the complete authentication system: routes, templates, and static file migration.

**CRITICAL: No Flask Blueprints (per D-01).** Routes are defined in `app/routes.py` as an `init_routes(app)` function that attaches `@app.route()` decorators directly to the app instance. Do NOT use `Blueprint` anywhere.

**Step A: Migrate static files**

1. Copy `css/styles.css` to `app/static/css/styles.css` (create directory structure first with `mkdir -p app/static/css app/static/js app/static/images`)

2. Copy `images/winthrop-hall.jpg` to `app/static/images/winthrop-hall.jpg`

3. Copy `js/auth.js` to `app/static/js/auth.js` and update it:
   - REMOVE the jQuery form submit handlers entirely (the `$('#form-login').on('submit', ...)` and `$('#form-signup').on('submit', ...)` blocks with their TODO comments)
   - KEEP the tab-switching logic only (the `$('.auth-tab').on('click', ...)` handler)
   - The forms will now submit normally to Flask routes (no AJAX needed for auth forms per RESEARCH.md Pitfall 1)

**Step B: Update `app/__init__.py`**

Read the current file and modify:
- REMOVE the placeholder `@app.route('/')` index function
- ADD after `mail.init_app(app)`:
```python
    from app.routes import init_routes
    init_routes(app)
```

**Step C: Create `app/routes.py`** with an `init_routes(app)` function. All routes use `@app.route()` decorators directly on the passed app instance. No Blueprint import or usage (per D-01).

```python
from functools import wraps
from flask import redirect, url_for, session, render_template, flash, request, current_app
from flask_mail import Message
from app import db, mail
from app.models import User
from app.forms import RegistrationForm, LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm


def login_required(f):
    """Redirect to /auth if user not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated


def email_verified_required(f):
    """Redirect to /verify-otp if user not verified (per D-12, D-16)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.email_verified:
            return redirect(url_for('verify_otp'))
        return f(*args, **kwargs)
    return decorated


def init_routes(app):
    """Register all application routes directly on the app (no blueprints, per D-01)."""

    @app.route('/')
    @email_verified_required
    def index():
        user = db.session.get(User, session['user_id'])
        return render_template('dashboard.html', user=user)

    @app.route('/auth')
    def auth():
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user and user.email_verified:
                return redirect(url_for('index'))
        active_tab = request.args.get('tab', 'login')
        return render_template('auth.html',
                               login_form=LoginForm(),
                               register_form=RegistrationForm(),
                               active_tab=active_tab)

    @app.route('/register', methods=['POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            if form.validate_email_duplicate():
                flash('An account with this email already exists.', 'error')
                return render_template('auth.html',
                                       login_form=LoginForm(),
                                       register_form=form,
                                       active_tab='signup')
            user = User(display_name=form.display_name.data, email=form.email.data)
            user.set_password(form.password.data)
            otp = user.generate_otp()
            db.session.add(user)
            db.session.commit()

            # Send OTP email
            try:
                msg = Message(
                    'Your UWA Swap-Meet Verification Code',
                    recipients=[user.email],
                    body=f'Your verification code is: {otp}'
                )
                mail.send(msg)
            except Exception:
                app.logger.warning('Failed to send OTP email')

            if app.config.get('MAIL_SUPPRESS_SEND'):
                app.logger.info(f'OTP for {user.email}: {otp}')

            session['user_id'] = user.id
            return redirect(url_for('verify_otp'))

        return render_template('auth.html',
                               login_form=LoginForm(),
                               register_form=form,
                               active_tab='signup')

    @app.route('/login', methods=['POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                session['user_id'] = user.id
                if not user.email_verified:
                    return redirect(url_for('verify_otp'))
                return redirect(url_for('index'))
            flash('Invalid email or password.', 'error')
        return render_template('auth.html',
                               login_form=form,
                               register_form=RegistrationForm(),
                               active_tab='login')

    @app.route('/verify-otp', methods=['GET', 'POST'])
    @login_required
    def verify_otp():
        user = db.session.get(User, session['user_id'])
        if user.email_verified:
            return redirect(url_for('index'))
        form = OTPForm()
        if form.validate_on_submit():
            if user.is_otp_valid(form.otp_code.data):
                user.email_verified = True
                db.session.commit()
                return redirect(url_for('index'))
            flash('Invalid or expired verification code.', 'error')
        return render_template('verify_otp.html', form=form, user_email=user.email)

    @app.route('/resend-otp', methods=['POST'])
    @login_required
    def resend_otp():
        user = db.session.get(User, session['user_id'])
        if user.can_resend_otp():
            otp = user.generate_otp()
            db.session.commit()
            try:
                msg = Message(
                    'Your UWA Swap-Meet Verification Code',
                    recipients=[user.email],
                    body=f'Your verification code is: {otp}'
                )
                mail.send(msg)
            except Exception:
                app.logger.warning('Failed to send OTP email')
            if app.config.get('MAIL_SUPPRESS_SEND'):
                app.logger.info(f'OTP for {user.email}: {otp}')
            flash('A new verification code has been sent.', 'success')
        else:
            flash('Please wait before requesting a new code.', 'error')
        return redirect(url_for('verify_otp'))

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                token = User.generate_reset_token(user.email, app.secret_key)
                reset_url = url_for('reset_password', token=token, _external=True)
                try:
                    msg = Message(
                        'Reset Your UWA Swap-Meet Password',
                        recipients=[user.email],
                        body=f'Click here to reset your password: {reset_url}'
                    )
                    mail.send(msg)
                except Exception:
                    app.logger.warning('Failed to send reset email')
            flash('If an account exists with that email, a reset link has been sent.', 'info')
        return render_template('forgot_password.html', form=form)

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        email = User.verify_reset_token(token, app.secret_key)
        if not email:
            flash('This reset link is invalid or has expired.', 'error')
            return redirect(url_for('forgot_password'))
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('This reset link is invalid or has expired.', 'error')
            return redirect(url_for('forgot_password'))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.set_password(form.password.data)
            db.session.commit()
            flash('Your password has been reset.', 'success')
            return redirect(url_for('auth'))
        return render_template('reset_password.html', form=form, token=token)

    @app.route('/logout')
    @login_required
    def logout():
        session.clear()
        return redirect(url_for('auth'))
```

**IMPORTANT:** All `url_for()` calls use bare function names (e.g., `url_for('login')`, NOT `url_for('main.login')`). There is no Blueprint prefix because D-01 forbids Blueprints.

**Step D: Create `app/templates/base.html`:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{% block title %}UWA Swap-Meet{% endblock %}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    {% block extra_head %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
    <div class="flash-messages">
        {% for category, message in messages %}
        <div class="flash-message flash-{{ category }}">{{ message }}</div>
        {% endfor %}
    </div>
    {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}

    {% block scripts %}{% endblock %}
</body>
</html>
```

**Step E: Create `app/templates/auth.html`** by converting the existing auth.html:
- Add `{% extends "base.html" %}` at top
- Wrap content in `{% block content %}`
- Replace `<link ...css/styles.css>` with nothing (base.html handles it)
- Replace `background-image: url('images/winthrop-hall.jpg')` with `background-image: url('{{ url_for('static', filename='images/winthrop-hall.jpg') }}')`
- Add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` to BOTH login and signup forms
- Set login form action to `{{ url_for('login') }}" method="POST"`
- Set signup form action to `{{ url_for('register') }}" method="POST"`
- Change signup "Username" label and field to "Display Name" (per D-09 -- it should be display_name, not username). Update the input id from `signup-username` to `signup-display-name`, name to `display_name`
- Add flash message display before the auth card
- Replace `<a class="form-link" href="#">Forgot Password?</a>` with `<a class="form-link" href="{{ url_for('forgot_password') }}">Forgot Password?</a>`
- Replace `<script src="js/auth.js">` with `<script src="{{ url_for('static', filename='js/auth.js') }}">`
- Add `{% block body_class %}auth-page{% endblock %}`
- Keep ALL the existing CSS classes, structure, and styling from auth.html -- just add Jinja2 syntax

**Step F: Create `app/templates/verify_otp.html`:**
- Extends base.html with body_class "auth-page"
- Uses the same auth-background and auth-background-overlay as auth.html
- Shows the brand header (same as auth.html)
- A card with: title "Verify Your Email", subtitle "We sent a verification code to {{ user_email }}"
- Form with POST to url_for('verify_otp'), CSRF token hidden input, OTP code input (6 digits, matching OTPForm), submit button "Verify"
- Below form: a "Resend Code" button that POSTs to url_for('resend_otp') with CSRF token
- Flash messages for errors/success
- Follows DESIGN.md design system: surface colors, rounded corners, Inter/Manrope fonts, no borders

**Step G: Create `app/templates/forgot_password.html`:**
- Extends base.html, same background pattern as auth.html
- Card with: title "Reset Your Password", subtitle "Enter your UWA student email"
- Form with POST to url_for('forgot_password'), CSRF token, email input, submit button
- Link back to login page
- Flash messages

**Step H: Create `app/templates/reset_password.html`:**
- Extends base.html, same background pattern
- Card with: title "Set New Password"
- Form with POST to url_for('reset_password', token=token), CSRF token, new password input, confirm password input, submit button
- Flash messages

**Step I: Create `app/templates/dashboard.html`:**
- Minimal placeholder per RESEARCH.md Open Question 2
- Extends base.html
- Shows: "Welcome, {{ user.display_name }}!" and a "Logout" link to url_for('logout')
- Simple, clean -- this gets replaced in Phase 2 with the actual marketplace

**IMPORTANT IMPLEMENTATION NOTES:**
- Wrap all mail.send() calls in try/except to prevent SMTP errors from crashing the app during development (per RESEARCH.md Pitfall 3)
- Log OTP to app.logger when MAIL_SUPPRESS_SEND is True so developers can see it in console
- Use `datetime.now(timezone.utc)` everywhere, never `datetime.utcnow()` (per RESEARCH.md anti-pattern)
- All url_for calls use bare function names: 'login', 'register', 'verify_otp', 'resend_otp', 'forgot_password', 'reset_password', 'logout', 'index', 'auth' -- NO 'main.' prefix
  </action>
  <verify>
    <automated>cd /Users/sawetr/Documents/uwa-marketplace && python3 -c "from app import create_app; app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'TESTING': True}); routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule != '/static/<path:filename>']; print('Routes:', routes); assert '/auth' in routes; assert '/register' in routes; assert '/login' in routes; assert '/verify-otp' in routes; assert '/logout' in routes; print('PASS: all routes registered')" && test -f app/static/css/styles.css && test -f app/static/js/auth.js && test -f app/static/images/winthrop-hall.jpg && echo "PASS: static files migrated"</automated>
  </verify>
  <done>
    - app/__init__.py calls init_routes(app) from app.routes, no placeholder route
    - app/routes.py defines init_routes(app) function with @app.route() decorators (no Blueprint)
    - Routes: /, /auth, /register, /login, /verify-otp, /resend-otp, /forgot-password, /reset-password/<token>, /logout
    - All url_for() calls use bare names ('login', not 'main.login')
    - app/templates/base.html has csrf_token() meta tag, flash message display, Tailwind CDN, Google Fonts
    - app/templates/auth.html is converted from static auth.html with Jinja2 (CSRF tokens, url_for, flash messages)
    - app/templates/verify_otp.html has OTP form and resend button
    - app/templates/forgot_password.html has email entry form
    - app/templates/reset_password.html has new password form
    - app/templates/dashboard.html has welcome message and logout link
    - app/static/css/styles.css is the migrated design system CSS
    - app/static/js/auth.js has tab-switching only (no TODO stubs)
    - app/static/images/winthrop-hall.jpg is the migrated campus photo
    - Flask app starts and all route URLs are registered
  </done>
</task>

<task type="auto">
  <name>Task 2: Create auth route integration tests</name>
  <files>tests/test_auth.py</files>
  <read_first>
    app/routes.py (created in Task 1 -- need route URLs and behavior)
    tests/conftest.py (from Plan 01 -- need fixture interface)
    app/models.py (from Plan 01 -- User model for creating test users)
    app/forms.py (from Plan 01 -- form field names for POST data)
    .planning/phases/01-flask-foundation-authentication/01-VALIDATION.md (for test IDs)
  </read_first>
  <action>
Create integration tests for all auth routes. These test the full HTTP request/response cycle using Flask's test client.

The conftest.py fixture (from Plan 01) provides `app` and `client`. CSRF is disabled in test config (WTF_CSRF_ENABLED=False), so tests do not need CSRF tokens.

Write these tests in `tests/test_auth.py`:

1. **test_register_success:** POST to /register with display_name='Test User', email='test@student.uwa.edu.au', password='Password1', confirm_password='Password1'. Assert redirect to /verify-otp. Assert User exists in database with email_verified=False.

2. **test_register_invalid_email:** POST with email='test@gmail.com' (non-UWA). Assert 200 (re-renders form with errors). Assert no user created.

3. **test_register_duplicate_email:** Create a user first, then POST register with same email. Assert flash message contains "already exists". Assert only 1 user in database.

4. **test_register_weak_password:** POST with password='pass' (too short, no number). Assert 200 with form errors. Assert no user created.

5. **test_login_success:** Create a verified user (email_verified=True), POST /login with correct credentials. Assert redirect to /.

6. **test_login_wrong_password:** Create a user, POST /login with wrong password. Assert flash contains "Invalid". Assert 200 (re-renders).

7. **test_unverified_redirect:** Create an unverified user, POST /login. Assert redirect to /verify-otp (per D-16).

8. **test_logout:** Login as verified user, GET /logout. Assert redirect to /auth. Assert session cleared (subsequent GET to protected route redirects to /auth).

9. **test_csrf_required_on_post_routes:** Create a new Flask test client WITHOUT CSRF disabled. POST to /register without CSRF token. Assert 400 response. This test creates its own app fixture with WTF_CSRF_ENABLED=True.

10. **test_verify_otp_valid:** Register a user (which generates OTP), then POST to /verify-otp with the correct OTP code. Assert redirect to /. Assert user.email_verified is True.

11. **test_verify_otp_invalid:** Register a user, POST to /verify-otp with wrong code '000000'. Assert flash message. Assert user still not verified.

12. **test_forgot_password_sends_email:** Create a verified user, POST /forgot-password with user's email. Assert flash message contains confirmation. (Mail sending is suppressed in tests, so just verify the route doesn't error.)

13. **test_reset_password_valid_token:** Generate a reset token for a user, GET /reset-password/<token>. Assert 200 (renders form). POST with new password. Assert redirect. Verify password was actually changed (check_password with new password returns True).

14. **test_reset_password_expired_token:** Generate token, wait or use token verification with invalid data. GET /reset-password/invalid-token-string. Assert redirect to /forgot-password with flash error.

Use helper functions to reduce duplication:
```python
def register_user(client, display_name='Test User', email='test@student.uwa.edu.au',
                  password='Password1', confirm_password='Password1'):
    return client.post('/register', data={
        'display_name': display_name,
        'email': email,
        'password': password,
        'confirm_password': confirm_password,
    }, follow_redirects=False)

def create_verified_user(app, email='verified@student.uwa.edu.au', password='Password1'):
    with app.app_context():
        from app.models import User
        user = User(display_name='Verified User', email=email)
        user.set_password(password)
        user.email_verified = True
        from app import db
        db.session.add(user)
        db.session.commit()
        return user.id
```
  </action>
  <verify>
    <automated>cd /Users/sawetr/Documents/uwa-marketplace && pytest tests/test_auth.py -v</automated>
  </verify>
  <done>
    - tests/test_auth.py exists with 14 test functions
    - test_register_success: valid registration creates user and redirects to OTP
    - test_register_invalid_email: rejects non-UWA email
    - test_register_duplicate_email: shows "already exists" error
    - test_register_weak_password: rejects weak password
    - test_login_success: correct credentials redirect to dashboard
    - test_login_wrong_password: shows error, re-renders form
    - test_unverified_redirect: unverified user redirected to OTP page
    - test_logout: clears session, redirects to auth
    - test_csrf_required_on_post_routes: POST without CSRF returns 400
    - test_verify_otp_valid: correct OTP verifies user
    - test_verify_otp_invalid: wrong OTP shows error
    - test_forgot_password_sends_email: route completes without error
    - test_reset_password_valid_token: token works, password changed
    - test_reset_password_expired_token: invalid token redirects with error
    - All 14 tests pass with `pytest tests/test_auth.py -v`
    - Full suite passes: `pytest tests/ -v`
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Manual browser verification of auth system</name>
  <files>none (checkpoint only)</files>
  <action>
Start the Flask development server and manually verify the complete auth flow through the browser: registration, OTP verification, login, logout, forgot password, and visual design consistency.
  </action>
  <what-built>Complete authentication system: register, OTP verification, login, logout, forgot/reset password. All templates follow the Scholarly Curator design system from DESIGN.md using the existing auth.html layout.</what-built>
  <how-to-verify>
    1. Start the Flask server:
       ```bash
       cd /Users/sawetr/Documents/uwa-marketplace
       python3 run.py
       ```

    2. Open browser to http://127.0.0.1:5000/auth

    3. **Test Registration:**
       - Click "Sign Up" tab
       - Enter a display name, a UWA student email (must end in @student.uwa.edu.au), and a password with 8+ chars including a letter and number
       - Click "Create Account"
       - You should be redirected to the OTP verification page
       - Check terminal/console for the OTP code (logged when MAIL_SUPPRESS_SEND=true)
       - Enter the OTP code and click "Verify"
       - You should see the dashboard page

    4. **Test Login:**
       - Click "Logout" on the dashboard
       - On the auth page, enter the same email and password
       - Click "Login to Exchange"
       - You should be redirected to the dashboard

    5. **Test Forgot Password:**
       - Go to /auth, click "Forgot Password?" link
       - Enter your email
       - Submit -- check terminal for confirmation

    6. **Visual checks:**
       - Auth page should show Winthrop Hall campus background
       - Login/Signup tabs should switch between forms
       - Design should match the Scholarly Curator aesthetic (no borders, tonal surfaces, Inter/Manrope fonts)
       - Flash messages should appear for errors
  </how-to-verify>
  <resume-signal>Type "approved" if everything works, or describe specific issues to fix</resume-signal>
  <done>User confirms all auth flows work correctly in the browser and visual design matches expectations.</done>
</task>

</tasks>

<verification>
1. `pytest tests/ -v` -- all tests pass (test_models.py + test_auth.py)
2. `python3 run.py` -- app starts without errors
3. Manual browser verification of full auth flow
</verification>

<success_criteria>
- All 14 auth route tests pass
- All 7 model tests pass (from Plan 01)
- Full test suite green: `pytest tests/ -v` (21+ tests)
- User can register, verify OTP, log in, log out, and reset password through browser
- Templates render with Scholarly Curator design system
- CSRF tokens present on all forms
- Static files served from app/static/ directory
- No Flask Blueprint used anywhere (per D-01)
</success_criteria>

<output>
After completion, create `.planning/phases/01-flask-foundation-authentication/02-SUMMARY.md`
</output>
