import pytest
from app import create_app, db as _db


@pytest.fixture
def app(tmp_path):
    """Create application for testing with in-memory SQLite."""
    upload_dir = tmp_path / 'uploads'
    upload_dir.mkdir()
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for simpler test POSTs
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_DEFAULT_SENDER': 'test@example.com',
        'UPLOAD_FOLDER': str(upload_dir),
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


@pytest.fixture
def admin_client(app):
    """Create an admin user and return an authenticated client."""
    with app.app_context():
        from app.models import User
        user = User(display_name='Admin', email='admin@test.com')
        user.set_password('AdminPass1')
        user.email_verified = True
        user.is_admin = True
        _db.session.add(user)
        _db.session.commit()
        uid = user.id
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = uid
    return client
