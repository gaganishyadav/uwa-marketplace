import os
import uuid
from functools import wraps

from flask import abort, redirect, url_for, session, render_template, flash, request, current_app
from flask_mail import Message
from werkzeug.utils import secure_filename

from app import db, mail
from app.models import User, Listing
from app.forms import (
    RegistrationForm, LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm,
    ListingForm, EditProfileForm,
)


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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def save_upload(file_storage, upload_folder):
        """Save uploaded file with UUID name. Returns filename or None."""
        if not file_storage or not file_storage.filename:
            return None
        original = secure_filename(file_storage.filename)
        ext = os.path.splitext(original)[1].lower()
        if ext.lstrip('.') not in {'jpg', 'jpeg', 'png'}:
            return None
        filename = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(upload_folder, exist_ok=True)
        file_storage.save(os.path.join(upload_folder, filename))
        return filename

    def get_owned_listing_or_403(listing_id):
        """Get listing by ID, abort 403 if not owned by current user."""
        listing = db.session.get(Listing, listing_id)
        if not listing or listing.user_id != session.get('user_id'):
            abort(403)
        return listing

    # ------------------------------------------------------------------
    # Marketplace routes
    # ------------------------------------------------------------------

    @app.route('/')
    def gallery():
        """Public gallery - shows all listings, active first, then sold (per D-20)."""
        active_listings = Listing.query.filter_by(status='active').order_by(
            Listing.created_at.desc()).all()
        sold_listings = Listing.query.filter_by(status='sold').order_by(
            Listing.created_at.desc()).all()
        listing_form = ListingForm()
        return render_template('gallery.html',
                               listings=active_listings + sold_listings,
                               listing_form=listing_form)

    @app.route('/api/search')
    def api_search():
        """AJAX search endpoint -- returns rendered HTML cards (per D-02, D-03, D-08)."""
        q = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)

        # Start with active and sold queries separately (per D-11: active first)
        active_query = Listing.query.filter_by(status='active')
        sold_query = Listing.query.filter_by(status='sold')

        # Keyword search on title + description (per D-03: case-insensitive LIKE)
        if q:
            # Escape LIKE special characters (per Pitfall 2 in RESEARCH.md)
            search_term = q.replace('%', r'\%').replace('_', r'\_')
            search_pattern = f'%{search_term}%'
            active_query = active_query.filter(
                db.or_(
                    Listing.title.ilike(search_pattern),
                    Listing.description.ilike(search_pattern),
                )
            )
            sold_query = sold_query.filter(
                db.or_(
                    Listing.title.ilike(search_pattern),
                    Listing.description.ilike(search_pattern),
                )
            )

        # Category filter (per D-05, D-06)
        if category:
            active_query = active_query.filter_by(category=category)
            sold_query = sold_query.filter_by(category=category)

        # Price range filter (per D-07)
        if min_price is not None:
            active_query = active_query.filter(Listing.price >= min_price)
            sold_query = sold_query.filter(Listing.price >= min_price)
        if max_price is not None:
            active_query = active_query.filter(Listing.price <= max_price)
            sold_query = sold_query.filter(Listing.price <= max_price)

        # Order by newest first, active before sold (per D-11)
        active_listings = active_query.order_by(Listing.created_at.desc()).all()
        sold_listings = sold_query.order_by(Listing.created_at.desc()).all()
        listings = active_listings + sold_listings

        # Build result count text (per D-12)
        count = len(listings)
        if q:
            count_text = f'{count} result{"s" if count != 1 else ""} for \u201c{q}\u201d'
        else:
            count_text = f'Showing {count} listing{"s" if count != 1 else ""}'

        return render_template('_search_results.html',
                               listings=listings,
                               count_text=count_text,
                               search_query=q)

    @app.route('/listing/<int:listing_id>')
    def listing_detail(listing_id):
        listing = db.session.get(Listing, listing_id)
        if not listing:
            abort(404)
        user = db.session.get(User, session['user_id']) if 'user_id' in session else None
        return render_template('listing_detail.html', listing=listing, current_user=user)

    @app.route('/dashboard')
    @email_verified_required
    def dashboard():
        user = db.session.get(User, session['user_id'])
        my_listings = Listing.query.filter_by(user_id=user.id).order_by(
            Listing.created_at.desc()).all()
        active_count = sum(1 for l in my_listings if l.status == 'active')
        sold_count = sum(1 for l in my_listings if l.status == 'sold')
        listing_form = ListingForm()
        return render_template('dashboard.html',
                               user=user,
                               listings=my_listings,
                               active_count=active_count,
                               sold_count=sold_count,
                               listing_form=listing_form)

    @app.route('/create-listing', methods=['POST'])
    @email_verified_required
    def create_listing():
        form = ListingForm()
        if form.validate_on_submit():
            filename = None
            if form.image.data:
                filename = save_upload(form.image.data, app.config['UPLOAD_FOLDER'])
            listing = Listing(
                user_id=session['user_id'],
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,
                condition=form.condition.data,
                meetup_spot=form.meetup_spot.data,
                image_path=filename,
            )
            db.session.add(listing)
            db.session.commit()
            flash('Listing created successfully!', 'success')
        else:
            for field_name, errors in form.errors.items():
                label = getattr(form, field_name).label.text
                for error in errors:
                    flash(f'{label}: {error}', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    @app.route('/edit-listing/<int:listing_id>', methods=['POST'])
    @email_verified_required
    def edit_listing(listing_id):
        listing = get_owned_listing_or_403(listing_id)
        if listing.status == 'sold':
            flash('Sold listings cannot be edited.', 'error')
            return redirect(url_for('dashboard'))
        form = ListingForm()
        if form.validate_on_submit():
            listing.title = form.title.data
            listing.description = form.description.data
            listing.price = form.price.data
            listing.category = form.category.data
            listing.condition = form.condition.data
            listing.meetup_spot = form.meetup_spot.data
            if form.image.data:
                # Delete old image if replacing
                if listing.image_path:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], listing.image_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                listing.image_path = save_upload(form.image.data, app.config['UPLOAD_FOLDER'])
            db.session.commit()
            flash('Listing updated!', 'success')
        else:
            for field_name, errors in form.errors.items():
                label = getattr(form, field_name).label.text
                for error in errors:
                    flash(f'{label}: {error}', 'error')
        return redirect(url_for('dashboard'))

    @app.route('/delete-listing/<int:listing_id>', methods=['POST'])
    @email_verified_required
    def delete_listing(listing_id):
        listing = get_owned_listing_or_403(listing_id)
        # Delete image from disk
        if listing.image_path:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], listing.image_path)
            if os.path.exists(img_path):
                os.remove(img_path)
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/mark-sold/<int:listing_id>', methods=['POST'])
    @email_verified_required
    def mark_sold(listing_id):
        listing = get_owned_listing_or_403(listing_id)
        if listing.status != 'sold':
            listing.status = 'sold'
            db.session.commit()
            flash('Listing marked as sold.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/edit-profile', methods=['POST'])
    @email_verified_required
    def edit_profile():
        user = db.session.get(User, session['user_id'])
        form = EditProfileForm()
        if form.validate_on_submit():
            user.display_name = form.display_name.data
            user.bio = form.bio.data
            db.session.commit()
            flash('Profile updated!', 'success')
        return redirect(url_for('dashboard'))

    # ------------------------------------------------------------------
    # Auth routes
    # ------------------------------------------------------------------

    @app.route('/auth')
    def auth():
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user and user.email_verified:
                return redirect(url_for('gallery'))
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
                return redirect(url_for('gallery'))
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
            return redirect(url_for('gallery'))
        form = OTPForm()
        if form.validate_on_submit():
            if user.is_otp_valid(form.otp_code.data):
                user.email_verified = True
                db.session.commit()
                return redirect(url_for('gallery'))
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
