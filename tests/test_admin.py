"""Unit tests for admin routes: decorator, listing management, user moderation,
featured sorting, banned user interception, and admin seeding."""

import pytest

from app import db
from app.models import User, Listing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_listing_data(**overrides):
    """Return valid listing form data with optional overrides."""
    data = {
        'title': 'Used Textbook for CITS3403',
        'description': 'A well-maintained textbook.',
        'price': '25.00',
        'category': 'Textbooks',
        'condition': 'Good',
        'meetup_spot': 'Reid Library',
    }
    data.update(overrides)
    return data


def make_user(app, display_name='Test User', email='test@student.uwa.edu.au',
              is_admin=False, ban_status='active'):
    """Create and return a user in the database."""
    with app.app_context():
        user = User(display_name=display_name, email=email)
        user.set_password('Password1')
        user.email_verified = True
        user.is_admin = is_admin
        user.ban_status = ban_status
        db.session.add(user)
        db.session.commit()
        uid = user.id
    return uid


def make_listing(app, user_id, **overrides):
    """Create and return a listing in the database."""
    data = {
        'user_id': user_id,
        'title': 'Test Listing',
        'description': 'Test description.',
        'price': 10.0,
        'category': 'Textbooks',
        'condition': 'Good',
        'meetup_spot': 'Reid Library',
        'status': 'active',
    }
    data.update(overrides)
    with app.app_context():
        listing = Listing(**data)
        db.session.add(listing)
        db.session.commit()
        lid = listing.id
    return lid


def make_client_with_user(app, uid):
    """Return a test client authenticated as the given user."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = uid
    return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def regular_client(app):
    """Create a regular (non-admin) verified user and return authenticated client."""
    uid = make_user(app)
    return make_client_with_user(app, uid)


# ---------------------------------------------------------------------------
# ADMIN-01: User model is_admin default (unit test)
# ---------------------------------------------------------------------------

def test_user_is_admin_default_false(app):
    """New User has is_admin=False by default (per D-04)."""
    with app.app_context():
        user = User(display_name='Normal', email='normal@test.com')
        user.set_password('Password1')
        db.session.add(user)
        db.session.commit()
        assert user.is_admin is False
        assert user.ban_status == 'active'


# ---------------------------------------------------------------------------
# ADMIN-02: Admin can delete any listing
# ---------------------------------------------------------------------------

def test_admin_delete_listing(admin_client, app):
    """Admin can delete any user's listing (per D-08, D-09)."""
    uid = make_user(app, display_name='Seller', email='seller@test.com')
    lid = make_listing(app, user_id=uid, title='Admin Target')

    response = admin_client.post(f'/admin/delete-listing/{lid}', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        listing = db.session.get(Listing, lid)
        assert listing.status == 'deleted'


def test_admin_delete_nonexistent_listing(admin_client, app):
    """Admin deleting a nonexistent listing gets 404."""
    response = admin_client.post('/admin/delete-listing/9999', follow_redirects=False)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# ADMIN-03: Admin can feature/unfeature listing
# ---------------------------------------------------------------------------

def test_admin_feature_listing(admin_client, app):
    """Admin can feature a listing (per D-10)."""
    uid = make_user(app, display_name='Seller', email='seller@test.com')
    lid = make_listing(app, user_id=uid)

    response = admin_client.post(f'/admin/feature-listing/{lid}', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        listing = db.session.get(Listing, lid)
        assert listing.is_featured is True


def test_admin_unfeature_listing(admin_client, app):
    """Admin can unfeature a previously featured listing (per D-13)."""
    uid = make_user(app, display_name='Seller', email='seller@test.com')
    lid = make_listing(app, user_id=uid)
    # Feature it first
    with app.app_context():
        listing = db.session.get(Listing, lid)
        listing.is_featured = True
        db.session.commit()

    response = admin_client.post(f'/admin/feature-listing/{lid}', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        listing = db.session.get(Listing, lid)
        assert listing.is_featured is False


# ---------------------------------------------------------------------------
# ADMIN-04: Admin can ban user
# ---------------------------------------------------------------------------

def test_admin_ban_user(admin_client, app):
    """Admin can ban a user (per D-15)."""
    uid = make_user(app, display_name='Bad Actor', email='bad@test.com')

    response = admin_client.post(f'/admin/ban-user/{uid}', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        user = db.session.get(User, uid)
        assert user.ban_status == 'banned'


def test_admin_permanent_ban_user(admin_client, app):
    """Admin can permanently ban a user (per D-15)."""
    uid = make_user(app, display_name='Worse Actor', email='worse@test.com')

    response = admin_client.post(f'/admin/permanent-ban-user/{uid}', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        user = db.session.get(User, uid)
        assert user.ban_status == 'permanent_ban'


# ---------------------------------------------------------------------------
# ADMIN-05: Admin can unban user
# ---------------------------------------------------------------------------

def test_admin_unban_user(admin_client, app):
    """Admin can unban a previously banned user (per D-17)."""
    uid = make_user(app, display_name='Reformed', email='reformed@test.com', ban_status='banned')

    response = admin_client.post(f'/admin/unban-user/{uid}', follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        user = db.session.get(User, uid)
        assert user.ban_status == 'active'


# ---------------------------------------------------------------------------
# ADMIN-06: Regular user gets 403 on admin routes
# ---------------------------------------------------------------------------

def test_non_admin_gets_403_on_admin_routes(regular_client, app):
    """Non-admin users receive 403 on all /admin/* routes (per D-20, D-21)."""
    uid = make_user(app, display_name='Seller2', email='seller2@test.com')
    lid = make_listing(app, user_id=uid)

    # Admin user page
    resp = regular_client.get(f'/admin/user/{uid}', follow_redirects=False)
    assert resp.status_code == 403

    # Admin delete listing
    resp = regular_client.post(f'/admin/delete-listing/{lid}', follow_redirects=False)
    assert resp.status_code == 403

    # Admin feature listing
    resp = regular_client.post(f'/admin/feature-listing/{lid}', follow_redirects=False)
    assert resp.status_code == 403

    # Admin ban user
    resp = regular_client.post(f'/admin/ban-user/{uid}', follow_redirects=False)
    assert resp.status_code == 403

    # Admin unban user
    resp = regular_client.post(f'/admin/unban-user/{uid}', follow_redirects=False)
    assert resp.status_code == 403


def test_unauthenticated_gets_redirect_on_admin_routes(client, app):
    """Unauthenticated users are redirected to /auth on admin routes."""
    resp = client.get('/admin/user/1', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth' in resp.headers['Location']


# ---------------------------------------------------------------------------
# ADMIN-07: Banned user cannot access app
# ---------------------------------------------------------------------------

def test_banned_user_redirected_to_banned_page(app):
    """Banned user is redirected to /banned on any authenticated request (per D-16)."""
    uid = make_user(app, ban_status='banned')
    client = make_client_with_user(app, uid)

    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/banned' in response.headers['Location']


def test_permanently_banned_user_redirected(app):
    """Permanently banned user is also redirected to /banned."""
    uid = make_user(app, ban_status='permanent_ban')
    client = make_client_with_user(app, uid)

    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/banned' in response.headers['Location']


def test_banned_user_can_still_logout(app):
    """Banned user can access the logout route."""
    uid = make_user(app, ban_status='banned')
    client = make_client_with_user(app, uid)

    response = client.post('/logout', follow_redirects=False)
    assert response.status_code == 302


def test_banned_user_sees_banned_page(app):
    """Banned user requesting /banned gets the banned page, not redirect loop."""
    uid = make_user(app, ban_status='banned')
    client = make_client_with_user(app, uid)

    response = client.get('/banned', follow_redirects=False)
    assert response.status_code == 200
    assert b'suspend' in response.data.lower()


# ---------------------------------------------------------------------------
# ADMIN-08: Featured listings sort to top of gallery
# ---------------------------------------------------------------------------

def test_featured_listings_sort_to_top(admin_client, app):
    """Featured listings appear before non-featured active listings (per D-11)."""
    uid = make_user(app, display_name='Seller', email='seller@test.com')

    # Create non-featured listing first (older)
    lid1 = make_listing(app, user_id=uid, title='Regular Listing')
    # Create featured listing (newer)
    lid2 = make_listing(app, user_id=uid, title='Featured Listing')
    with app.app_context():
        listing = db.session.get(Listing, lid2)
        listing.is_featured = True
        db.session.commit()

    response = admin_client.get('/', follow_redirects=True)
    assert response.status_code == 200
    # Featured listing should appear before regular listing in the HTML
    featured_pos = response.data.find(b'Featured Listing')
    regular_pos = response.data.find(b'Regular Listing')
    assert featured_pos != -1, "Featured listing title is missing from the rendered gallery"
    assert regular_pos != -1, "Regular listing title is missing from the rendered gallery"
    assert featured_pos < regular_pos, (
        f"featured listing should render before regular listing, but featured is at "
        f"byte offset {featured_pos} and regular is at {regular_pos} -- "
        f"sort order in /gallery may have regressed"
    )


def test_featured_badge_visible_on_card(admin_client, app):
    """Featured listings show a 'Featured' badge on their card (per D-12)."""
    uid = make_user(app, display_name='Seller', email='seller@test.com')
    lid = make_listing(app, user_id=uid, title='Badge Test')
    with app.app_context():
        listing = db.session.get(Listing, lid)
        listing.is_featured = True
        db.session.commit()

    response = admin_client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'status-featured' in response.data


# ---------------------------------------------------------------------------
# ADMIN-09: Admin seeding from .env works
# ---------------------------------------------------------------------------

def test_admin_seed_creates_account(app, monkeypatch):
    """flask seed-admin creates an admin account when credentials are set (per D-06)."""
    monkeypatch.setenv('ADMIN_EMAIL', 'seeded@test.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'SeededPass1')

    runner = app.test_cli_runner()
    with app.app_context():
        result = runner.invoke(args=['seed-admin'])
        assert 'created' in result.output.lower(), (
            f"seed-admin should print a 'created' confirmation; got output: {result.output!r}"
        )

        user = User.query.filter_by(email='seeded@test.com').first()
        assert user is not None, "seed-admin did not insert a User row for ADMIN_EMAIL"
        assert user.is_admin is True, (
            f"seeded user should have is_admin=True; got {user.is_admin!r}"
        )
        assert user.email_verified is True, (
            f"seeded admin should be pre-verified; got email_verified={user.email_verified!r}"
        )


# ---------------------------------------------------------------------------
# ADMIN-10: Admin seeding is idempotent
# ---------------------------------------------------------------------------

def test_admin_seed_idempotent(app, monkeypatch):
    """Running seed-admin twice does not create duplicate (per D-06)."""
    monkeypatch.setenv('ADMIN_EMAIL', 'idem@test.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'IdemPass1')

    runner = app.test_cli_runner()
    with app.app_context():
        runner.invoke(args=['seed-admin'])
        result = runner.invoke(args=['seed-admin'])
        assert 'already exists' in result.output.lower()

        count = User.query.filter_by(email='idem@test.com').count()
        assert count == 1
