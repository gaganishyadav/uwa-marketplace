import os
import uuid
from datetime import timedelta
from functools import wraps

from flask import abort, redirect, url_for, session, render_template, flash, request, current_app, jsonify
from flask_mail import Message
from werkzeug.utils import secure_filename

from app import db, mail
from app.models import User, Listing, Message, _utcnow
from app.forms import (
    RegistrationForm, LoginForm, OTPForm, ForgotPasswordForm, ResetPasswordForm,
    ListingForm, EditProfileForm, MessageForm,
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


def admin_required(f):
    """Abort 403 if current user is not admin (per D-20, D-21)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def init_routes(app):
    """Register all application routes directly on the app (no blueprints, per D-01)."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    # Magic-byte signatures for the image formats we accept. Checked alongside
    # the file extension so a renamed binary (e.g. malware.exe.jpg) is rejected
    # even though its extension passes the whitelist.
    _JPEG_MAGIC = b'\xff\xd8\xff'
    _PNG_MAGIC = b'\x89PNG\r\n\x1a\n'

    def _sniff_image_type(stream):
        """Return 'jpeg', 'png', or None by reading the first 8 bytes.
        Leaves the stream position unchanged."""
        pos = stream.tell()
        head = stream.read(8)
        stream.seek(pos)
        if head.startswith(_JPEG_MAGIC):
            return 'jpeg'
        if head.startswith(_PNG_MAGIC):
            return 'png'
        return None

    def save_upload(file_storage, upload_folder):
        """Save uploaded file with UUID name. Returns filename or None.
        Validates both the file extension and the magic bytes so that a
        file's content must genuinely match its claimed type."""
        if not file_storage or not file_storage.filename:
            return None
        original = secure_filename(file_storage.filename)
        ext = os.path.splitext(original)[1].lower()
        ext_clean = ext.lstrip('.')
        if ext_clean not in {'jpg', 'jpeg', 'png'}:
            return None
        # Sniff magic bytes and require them to match the claimed extension
        detected = _sniff_image_type(file_storage.stream)
        if detected is None:
            return None
        if detected == 'jpeg' and ext_clean not in {'jpg', 'jpeg'}:
            return None
        if detected == 'png' and ext_clean != 'png':
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
    # Before-request hooks & error handlers
    # ------------------------------------------------------------------

    @app.before_request
    def check_ban_status():
        """Redirect banned users to banned page (per D-16)."""
        if 'user_id' in session:
            if request.endpoint in ('banned', 'logout', 'static'):
                return None
            user = db.session.get(User, session['user_id'])
            if user and user.ban_status in ('banned', 'permanent_ban'):
                return redirect(url_for('banned'))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    # ------------------------------------------------------------------
    # Marketplace routes
    # ------------------------------------------------------------------

    @app.route('/')
    def gallery():
        """Public gallery - featured first, then active, then sold (per D-11)."""
        featured_listings = Listing.query.filter_by(status='active', is_featured=True).order_by(
            Listing.created_at.desc()).all()
        active_listings = Listing.query.filter_by(status='active', is_featured=False).order_by(
            Listing.created_at.desc()).all()
        sold_listings = Listing.query.filter_by(status='sold').order_by(
            Listing.created_at.desc()).all()
        listing_form = ListingForm()
        user = db.session.get(User, session['user_id']) if 'user_id' in session else None
        return render_template('gallery.html',
                               listings=featured_listings + active_listings + sold_listings,
                               listing_form=listing_form,
                               user=user)

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

        # Order by newest first, featured before non-featured, active before sold (per D-11)
        featured_listings = active_query.filter_by(is_featured=True).order_by(Listing.created_at.desc()).all()
        non_featured_active = active_query.filter_by(is_featured=False).order_by(Listing.created_at.desc()).all()
        sold_listings = sold_query.order_by(Listing.created_at.desc()).all()
        listings = featured_listings + non_featured_active + sold_listings

        # Build result count text (per D-12)
        count = len(listings)
        if q:
            count_text = f'{count} result{"s" if count != 1 else ""} for \u201c{q}\u201d'
        else:
            count_text = f'Showing {count} listing{"s" if count != 1 else ""}'

        user = db.session.get(User, session['user_id']) if 'user_id' in session else None
        return render_template('_search_results.html',
                               listings=listings,
                               count_text=count_text,
                               search_query=q,
                               user=user)

    @app.route('/api/listings/suggest')
    def api_listings_suggest():
        """Typeahead suggestions: up to 5 distinct active listing titles matching q."""
        q = request.args.get('q', '').strip()
        if len(q) < 3:
            return jsonify([])

        search_term = q.replace('%', r'\%').replace('_', r'\_')
        pattern = f'%{search_term}%'
        rows = (
            db.session.query(Listing.title)
            .filter(Listing.status == 'active', Listing.title.ilike(pattern))
            .distinct()
            .order_by(Listing.title.asc())
            .limit(5)
            .all()
        )
        return jsonify([title for (title,) in rows])

    @app.route('/listing/<int:listing_id>')
    def listing_detail(listing_id):
        listing = db.session.get(Listing, listing_id)
        if not listing or listing.status == 'deleted':
            abort(404)
        user = db.session.get(User, session['user_id']) if 'user_id' in session else None
        listing_form = ListingForm()
        return render_template('listing_detail.html', listing=listing, user=user,
                               listing_form=listing_form)

    @app.route('/user/<int:user_id>')
    def seller_profile(user_id):
        seller = db.session.get(User, user_id)
        if not seller:
            abort(404)
        viewer = db.session.get(User, session['user_id']) if 'user_id' in session else None
        is_banned = seller.ban_status in ('banned', 'permanent_ban')
        if is_banned:
            listings = []
        else:
            listings = Listing.query.filter_by(
                user_id=user_id, status='active'
            ).order_by(
                Listing.is_featured.desc(), Listing.created_at.desc()
            ).all()
        return render_template('seller_profile.html',
                               seller=seller,
                               listings=listings,
                               active_count=len(listings),
                               is_banned=is_banned,
                               user=viewer)

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
        listing.status = 'deleted'
        listing.image_path = None
        db.session.commit()
        flash('Listing deleted.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/mark-sold/<int:listing_id>', methods=['POST'])
    @email_verified_required
    def mark_sold(listing_id):
        listing = get_owned_listing_or_403(listing_id)
        if listing.status != 'sold':
            listing.status = 'sold'
            listing.sold_at = _utcnow()
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
    # Messaging routes
    # ------------------------------------------------------------------

    @app.route('/send-message/<int:listing_id>', methods=['POST'])
    @email_verified_required
    def send_message(listing_id):
        """Send a message to the listing owner (per D-01, D-09, D-10)."""
        listing = db.session.get(Listing, listing_id)
        if not listing:
            return jsonify({'error': 'Listing not found.'}), 404
        # D-09: block self-messaging
        if listing.user_id == session['user_id']:
            abort(403)
        # D-11: block messages on sold listings
        if listing.status == 'sold':
            return jsonify({'error': 'This listing has been sold. Messaging is disabled.'}), 400
        # D-12: block messages on deleted listings
        if listing.status == 'deleted':
            return jsonify({'error': 'Listing not found.'}), 404

        form = MessageForm()
        if form.validate_on_submit():
            msg = Message(
                listing_id=listing_id,
                sender_id=session['user_id'],
                receiver_id=listing.user_id,
                content=form.content.data,
            )
            db.session.add(msg)
            db.session.commit()
            return jsonify({'success': True, 'redirect': url_for('inbox', thread=listing_id, with_user=listing.user_id)})
        # D-10: inline validation errors (return as JSON for AJAX)
        errors = []
        for field_name, field_errors in form.errors.items():
            for error in field_errors:
                errors.append(error)
        return jsonify({'errors': errors}), 400

    @app.route('/inbox')
    @email_verified_required
    def inbox():
        """Inbox view: conversation list or thread view (per D-05, D-06, D-08)."""
        user_id = session['user_id']
        thread_listing_id = request.args.get('thread', type=int)
        thread_with_user = request.args.get('with_user', type=int)

        if thread_listing_id and thread_with_user:
            # D-05: Show thread view in-place
            # Verify user is a participant in this conversation
            messages = Message.query.filter_by(
                listing_id=thread_listing_id
            ).filter(
                db.or_(
                    db.and_(Message.sender_id == user_id, Message.receiver_id == thread_with_user),
                    db.and_(Message.sender_id == thread_with_user, Message.receiver_id == user_id),
                )
            ).order_by(Message.created_at.asc()).all()
            if not messages:
                abort(403)
            listing = db.session.get(Listing, thread_listing_id)
            other_user = db.session.get(User, thread_with_user)
            # D-11: lazy cleanup -- filter out messages from sold listings older than 30 days
            if listing and listing.status == 'sold' and listing.sold_at:
                cutoff = _utcnow() - timedelta(days=30)
                if listing.sold_at < cutoff:
                    # Auto-delete expired messages for this sold listing
                    Message.query.filter_by(listing_id=thread_listing_id).delete()
                    db.session.commit()
                    return redirect(url_for('inbox'))
            return render_template('inbox.html', mode='thread', messages=messages,
                                   thread_listing=listing, other_user=other_user,
                                   other_user_id=thread_with_user,
                                   current_user_id=user_id,
                                   message_form=MessageForm())
        # Default: show conversation list (D-06, D-08)
        from sqlalchemy import func, case, and_
        other_user_expr = case(
            (Message.sender_id == user_id, Message.receiver_id),
            else_=Message.sender_id
        ).label('other_user_id')
        latest = db.session.query(
            Message.listing_id,
            other_user_expr,
            func.max(Message.created_at).label('last_at')
        ).filter(
            db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        ).filter(
            Listing.status.in_(['active', 'sold', 'deleted'])
        ).join(
            Listing, Message.listing_id == Listing.id
        ).group_by(Message.listing_id, other_user_expr).subquery()

        conversations = db.session.query(Message).join(
            latest,
            and_(
                Message.listing_id == latest.c.listing_id,
                Message.created_at == latest.c.last_at
            )
        ).order_by(Message.created_at.desc()).all()

        return render_template('inbox.html', mode='list', conversations=conversations,
                               current_user_id=user_id)

    @app.route('/thread-reply/<int:listing_id>/<int:with_user_id>', methods=['POST'])
    @email_verified_required
    def thread_reply(listing_id, with_user_id):
        """Reply within a message thread (per D-05)."""
        listing = db.session.get(Listing, listing_id)
        if not listing or listing.status == 'deleted':
            abort(404)
        if listing.status == 'sold':
            flash('This listing has been sold. Messaging is disabled.', 'error')
            return redirect(url_for('inbox', thread=listing_id, with_user=with_user_id))
        # Block self-messaging
        if with_user_id == session['user_id']:
            abort(403)
        # Verify user is part of this conversation
        user_id = session['user_id']
        existing = Message.query.filter_by(listing_id=listing_id).filter(
            db.or_(
                db.and_(Message.sender_id == user_id, Message.receiver_id == with_user_id),
                db.and_(Message.sender_id == with_user_id, Message.receiver_id == user_id),
            )
        ).first()
        if not existing:
            abort(403)

        form = MessageForm()
        if form.validate_on_submit():
            msg = Message(
                listing_id=listing_id,
                sender_id=user_id,
                receiver_id=with_user_id,
                content=form.content.data,
            )
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for('inbox', thread=listing_id, with_user=with_user_id))

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
                return render_template('auth.html',
                                       login_form=LoginForm(),
                                       register_form=form,
                                       active_tab='signup',
                                       register_error='An account with this email already exists.')
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
        login_error = None
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                session.permanent = True
                session['user_id'] = user.id
                if not user.email_verified:
                    return redirect(url_for('verify_otp'))
                return redirect(url_for('gallery'))
            login_error = 'Invalid email or password.'
        return render_template('auth.html',
                               login_form=form,
                               register_form=RegistrationForm(),
                               active_tab='login',
                               login_error=login_error)

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

    # ------------------------------------------------------------------
    # Admin routes (per D-20, D-21)
    # ------------------------------------------------------------------

    @app.route('/admin/user/<int:user_id>')
    @admin_required
    def admin_user(user_id):
        """Admin user detail page with ban controls (per D-14)."""
        target_user = db.session.get(User, user_id)
        if not target_user:
            abort(404)
        listing_count = Listing.query.filter_by(user_id=user_id).filter(
            Listing.status.in_(['active', 'sold'])).count()
        return render_template('admin_user.html', target_user=target_user,
                               listing_count=listing_count)

    @app.route('/admin/delete-listing/<int:listing_id>', methods=['POST'])
    @admin_required
    def admin_delete_listing(listing_id):
        """Admin delete any listing (per D-08, D-09)."""
        listing = db.session.get(Listing, listing_id)
        if not listing:
            abort(404)
        if listing.image_path:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], listing.image_path)
            if os.path.exists(img_path):
                os.remove(img_path)
        listing.status = 'deleted'
        listing.image_path = None
        db.session.commit()
        flash('Listing deleted by admin.', 'success')
        return redirect(request.referrer or url_for('gallery'))

    @app.route('/admin/feature-listing/<int:listing_id>', methods=['POST'])
    @admin_required
    def admin_feature_listing(listing_id):
        """Admin toggle featured status on any listing (per D-10, D-13)."""
        listing = db.session.get(Listing, listing_id)
        if not listing or listing.status == 'deleted':
            abort(404)
        listing.is_featured = not listing.is_featured
        db.session.commit()
        status = 'featured' if listing.is_featured else 'unfeatured'
        flash(f'Listing {status}.', 'success')
        return redirect(request.referrer or url_for('gallery'))

    @app.route('/admin/ban-user/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_ban_user(user_id):
        """Admin ban user temporarily (per D-15). Guard against admin self-ban (T-05-07)."""
        target_user = db.session.get(User, user_id)
        if not target_user:
            abort(404)
        if target_user.is_admin:
            flash('Cannot ban admin account.', 'error')
            return redirect(url_for('admin_user', user_id=user_id))
        target_user.ban_status = 'banned'
        db.session.commit()
        flash(f'{target_user.display_name} has been banned.', 'success')
        return redirect(url_for('admin_user', user_id=user_id))

    @app.route('/admin/permanent-ban-user/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_permanent_ban_user(user_id):
        """Admin permanently ban user (per D-15). Guard against admin self-ban (T-05-07)."""
        target_user = db.session.get(User, user_id)
        if not target_user:
            abort(404)
        if target_user.is_admin:
            flash('Cannot ban admin account.', 'error')
            return redirect(url_for('admin_user', user_id=user_id))
        target_user.ban_status = 'permanent_ban'
        db.session.commit()
        flash(f'{target_user.display_name} has been permanently banned.', 'success')
        return redirect(url_for('admin_user', user_id=user_id))

    @app.route('/admin/unban-user/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_unban_user(user_id):
        """Admin unban user (per D-17). Guard against admin self-unban."""
        target_user = db.session.get(User, user_id)
        if not target_user:
            abort(404)
        if target_user.is_admin:
            flash('Cannot modify admin account.', 'error')
            return redirect(url_for('admin_user', user_id=user_id))
        target_user.ban_status = 'active'
        db.session.commit()
        flash(f'{target_user.display_name} has been unbanned.', 'success')
        return redirect(url_for('admin_user', user_id=user_id))

    @app.route('/banned')
    def banned():
        """Banned user landing page (per D-16)."""
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        user = db.session.get(User, session['user_id'])
        if not user or user.ban_status not in ('banned', 'permanent_ban'):
            return redirect(url_for('gallery'))
        return render_template('banned.html')
