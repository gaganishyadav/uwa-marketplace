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
