import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
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

    return app
