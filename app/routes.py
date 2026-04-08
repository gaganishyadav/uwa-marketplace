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
            if not app.config.get('MAIL_SUPPRESS_SEND'):
                try:
                    msg = Message(
                        'Your UWA Swap-Meet Verification Code',
                        recipients=[user.email],
                        body=f'Your verification code is: {otp}'
                    )
                    mail.send(msg)
                except Exception:
                    app.logger.warning('Failed to send OTP email')
            else:
                app.logger.warning(f'DEV MODE — OTP for {user.email}: {otp}')

            session.permanent = True
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
                session.permanent = True
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
        if user is None:
            session.clear()
            return redirect(url_for('auth'))
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
        if user is None:
            session.clear()
            return redirect(url_for('auth'))
        if user.can_resend_otp():
            otp = user.generate_otp()
            db.session.commit()
            if not current_app.config.get('MAIL_SUPPRESS_SEND'):
                try:
                    msg = Message(
                        'Your UWA Swap-Meet Verification Code',
                        recipients=[user.email],
                        body=f'Your verification code is: {otp}'
                    )
                    mail.send(msg)
                except Exception:
                    app.logger.warning('Failed to send OTP email')
            else:
                app.logger.warning(f'DEV MODE — OTP for {user.email}: {otp}')
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

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        session.clear()
        return redirect(url_for('auth'))
