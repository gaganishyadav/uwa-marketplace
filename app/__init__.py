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
