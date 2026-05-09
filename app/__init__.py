import os
from datetime import timedelta, timezone
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from markupsafe import Markup, escape

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()

PERTH_TZ = timezone(timedelta(hours=8))


def create_app(config=None):
    app = Flask(__name__)

    # Configuration from .env (per D-04)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    secret_key = os.environ.get('SECRET_KEY') or (config or {}).get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            'SECRET_KEY is not set. Add it to your .env file '
            '(see .env.example) or pass it via the create_app(config=...) argument.'
        )
    app.config['SECRET_KEY'] = secret_key
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
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

    # Upload config (per D-06)
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

    # Override config for testing
    if config:
        app.config.update(config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

    # Render naive UTC datetimes as Perth local time (UTC+8, no DST).
    # Use this filter only inside HTML attributes (aria-label, title, etc.)
    # where embedded markup would break the surrounding string.
    @app.template_filter('perth')
    def perth_time(dt, fmt='%d %b %H:%M'):
        if dt is None:
            return ''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(PERTH_TZ).strftime(fmt)

    # Render naive UTC datetimes as a <time> element. Server emits Perth time
    # as the visible fallback; client-side local_time.js re-renders the text
    # in the viewer's browser timezone via Intl.DateTimeFormat.
    @app.template_filter('local_time')
    def local_time(dt, fmt='%d %b %H:%M'):
        if dt is None:
            return ''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        perth_str = dt.astimezone(PERTH_TZ).strftime(fmt)
        iso = dt.astimezone(timezone.utc).isoformat()
        return Markup(
            f'<time class="local-time" datetime="{escape(iso)}" '
            f'data-format="{escape(fmt)}">{escape(perth_str)}</time>'
        )

    # Make current user available in all templates
    @app.context_processor
    def inject_user():
        from app.models import User
        from flask import session as flask_session
        user = None
        if flask_session.get('user_id'):
            user = db.session.get(User, flask_session['user_id'])
        return {'user': user}

    # Import routes
    from app.routes import init_routes
    init_routes(app)

    # Seed command for development data (per D-13)
    @app.cli.command('seed')
    def seed_command():
        """Seed the database with mock listings for development (idempotent, per D-13)."""
        from app.models import User, Listing
        import click

        if Listing.query.first() is not None:
            click.echo('Database already contains listings. Skipping seed.')
            return

        # Create seed users
        users_data = [
            ('Alice Chen', 'alice.seed@student.uwa.edu.au'),
            ('Bob Martinez', 'bob.seed@student.uwa.edu.au'),
            ('Charlie Kim', 'charlie.seed@student.uwa.edu.au'),
            ('Diana Patel', 'diana.seed@student.uwa.edu.au'),
        ]
        users = []
        for name, email in users_data:
            user = User(display_name=name, email=email)
            user.set_password('Password1')
            user.email_verified = True
            db.session.add(user)
            users.append(user)
        db.session.commit()

        # Create listings
        listings_data = [
            # Textbooks (5)
            {'title': 'Calculus Textbook', 'description': 'Used for MATH1002. Covers single and multivariable calculus. Great textbook for first-year students.', 'price': 45.0, 'category': 'Textbooks', 'condition': 'Good', 'meetup_spot': 'Reid Library', 'status': 'active'},
            {'title': 'Physics Textbook', 'description': 'University physics textbook for PHYS1001. Slightly worn but perfectly usable. A core textbook for science students.', 'price': 35.0, 'category': 'Textbooks', 'condition': 'Fair', 'meetup_spot': 'Reid Library', 'status': 'active'},
            {'title': 'Linear Algebra Textbook', 'description': 'Clean copy, no annotations. Used textbook for MATH1001 linear algebra module.', 'price': 40.0, 'category': 'Textbooks', 'condition': 'Like New', 'meetup_spot': 'Barry J. Marshall Library', 'status': 'active'},
            {'title': 'Chemistry Textbook', 'description': 'General chemistry textbook with periodic table insert. Used for CHEM1002.', 'price': 30.0, 'category': 'Textbooks', 'condition': 'Good', 'meetup_spot': 'Student Guild', 'status': 'sold'},
            {'title': 'Used textbook for MATH1002', 'description': 'Alternative calculus textbook recommended by the lecturer. Used by previous student.', 'price': 25.0, 'category': 'Textbooks', 'condition': 'Fair', 'meetup_spot': 'Oak Lawn', 'status': 'active'},

            # Electronics (4)
            {'title': 'Laptop Stand', 'description': 'Aluminum laptop stand, adjustable height. Perfect for student desk setup.', 'price': 25.0, 'category': 'Electronics', 'condition': 'Like New', 'meetup_spot': 'Student Guild', 'status': 'active'},
            {'title': 'Wireless Mouse', 'description': 'Logitech wireless mouse with USB receiver. Used for one semester.', 'price': 15.0, 'category': 'Electronics', 'condition': 'Good', 'meetup_spot': 'Winthrop Hall', 'status': 'active'},
            {'title': 'USB-C Hub', 'description': '7-in-1 USB-C hub with HDMI, USB 3.0, SD card reader. Great for laptop users.', 'price': 50.0, 'category': 'Electronics', 'condition': 'New', 'meetup_spot': 'Student Guild', 'status': 'sold'},
            {'title': 'Scientific Calculator', 'description': 'Casio fx-82 calculator. Required for many science and engineering units.', 'price': 20.0, 'category': 'Electronics', 'condition': 'Good', 'meetup_spot': 'Reid Library', 'status': 'active'},

            # Furniture (4)
            {'title': 'Ergonomic Office Chair', 'description': 'Mesh back office chair with lumbar support. Ideal for long study sessions. Keep your textbook collection nearby.', 'price': 120.0, 'category': 'Furniture', 'condition': 'Good', 'meetup_spot': 'Oak Lawn', 'status': 'active'},
            {'title': 'Standing Desk', 'description': 'Adjustable height standing desk. Used by student for 6 months. Minor wear.', 'price': 150.0, 'category': 'Furniture', 'condition': 'Good', 'meetup_spot': 'Oak Lawn', 'status': 'sold'},
            {'title': 'Bookshelf', 'description': 'Tall wooden bookshelf with 5 shelves. Great for organizing your textbook collection and study materials.', 'price': 80.0, 'category': 'Furniture', 'condition': 'Fair', 'meetup_spot': 'Winthrop Hall', 'status': 'active'},
            {'title': 'Desk Lamp', 'description': 'LED desk lamp with adjustable brightness. Perfect companion for late-night study sessions.', 'price': 30.0, 'category': 'Furniture', 'condition': 'Like New', 'meetup_spot': 'Reid Library', 'status': 'active'},

            # Supplies (4)
            {'title': 'Highlighters Pack', 'description': 'Pack of 8 assorted color highlighters. Essential student supply for marking up textbooks and notes.', 'price': 8.0, 'category': 'Supplies', 'condition': 'New', 'meetup_spot': 'Oak Lawn', 'status': 'active'},
            {'title': 'Notebook Bundle', 'description': 'Set of 5 A4 notebooks, lined. Used by student for lecture notes across multiple units.', 'price': 12.0, 'category': 'Supplies', 'condition': 'New', 'meetup_spot': 'Student Guild', 'status': 'active'},
            {'title': 'Stationery Set', 'description': 'Pens, pencils, erasers, and ruler. Comprehensive student stationery kit.', 'price': 10.0, 'category': 'Supplies', 'condition': 'New', 'meetup_spot': 'Barry J. Marshall Library', 'status': 'active'},
            {'title': 'Binder Clips Set', 'description': 'Assorted binder clips for organizing handouts and textbook chapter printouts.', 'price': 5.0, 'category': 'Supplies', 'condition': 'New', 'meetup_spot': 'Oak Lawn', 'status': 'active'},

            # Sports (4)
            {'title': 'Yoga Mat', 'description': '6mm thick yoga mat, purple. Used a few times, excellent condition.', 'price': 18.0, 'category': 'Sports', 'condition': 'Like New', 'meetup_spot': 'Winthrop Hall', 'status': 'active'},
            {'title': 'Running Shoes', 'description': 'Nike running shoes, size 10. Used for UWA gym and running around campus.', 'price': 65.0, 'category': 'Sports', 'condition': 'Good', 'meetup_spot': 'Oak Lawn', 'status': 'active'},
            {'title': 'Tennis Racket', 'description': 'Wilson tennis racket with cover. Used for UWA tennis club sessions.', 'price': 55.0, 'category': 'Sports', 'condition': 'Good', 'meetup_spot': 'Student Guild', 'status': 'active'},
            {'title': 'Sports Water Bottle', 'description': '1L insulated water bottle. Keeps drinks cold during sports and gym sessions.', 'price': 22.0, 'category': 'Sports', 'condition': 'New', 'meetup_spot': 'Reid Library', 'status': 'active'},

            # Clothing (4)
            {'title': 'Lab Coat', 'description': 'Chemistry lab coat, size M. Required for lab units. Worn once, washed, selling as I switched majors.', 'price': 15.0, 'category': 'Clothing', 'condition': 'New', 'meetup_spot': 'Winthrop Hall', 'status': 'active'},
            {'title': 'UWA Hoodie', 'description': 'Official UWA hoodie, size L. Warm and comfortable for winter lectures.', 'price': 40.0, 'category': 'Clothing', 'condition': 'Like New', 'meetup_spot': 'Student Guild', 'status': 'active'},
            {'title': 'Graduation Gown', 'description': 'Standard graduation gown. Used for one ceremony. Save money renting if you are graduating soon.', 'price': 60.0, 'category': 'Clothing', 'condition': 'Good', 'meetup_spot': 'Winthrop Hall', 'status': 'sold'},
            {'title': 'Running Shorts', 'description': 'Lightweight running shorts, size M. Perfect for UWA gym or Oak Lawn workouts.', 'price': 10.0, 'category': 'Clothing', 'condition': 'Good', 'meetup_spot': 'Oak Lawn', 'status': 'active'},
        ]

        for i, data in enumerate(listings_data):
            user = users[i % len(users)]
            listing = Listing(
                user_id=user.id,
                title=data['title'],
                description=data['description'],
                price=data['price'],
                category=data['category'],
                condition=data['condition'],
                meetup_spot=data['meetup_spot'],
                image_path=None,
                status=data['status'],
            )
            db.session.add(listing)

        db.session.commit()
        click.echo(f'Seeded {len(listings_data)} mock listings from {len(users)} users.')

    # Seed admin account from .env credentials (per D-05, D-06)
    @app.cli.command('seed-admin')
    def seed_admin_command():
        """Create admin account from .env credentials (per D-05, D-06)."""
        from app.models import User
        import click

        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_email or not admin_password:
            click.echo('ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env')
            return
        existing = User.query.filter_by(email=admin_email).first()
        if existing:
            click.echo(f'Admin account already exists: {admin_email}')
            return
        admin = User(display_name='Admin', email=admin_email, is_admin=True, email_verified=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Admin account created: {admin_email}')

    return app
