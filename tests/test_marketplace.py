"""Unit tests for marketplace routes: gallery, CRUD, ownership, uploads."""

import io
import os

import pytest
from werkzeug.datastructures import FileStorage

from app import db
from app.models import User, Listing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_image(filename='test.jpg', size_bytes=100):
    """Create a minimal test image file for upload testing.

    Writes magic bytes matching the filename extension so the upload
    handler's content-type validation accepts the payload."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.png':
        header = b'\x89PNG\r\n\x1a\n'
        content_type = 'image/png'
    else:  # default to JPEG for .jpg / .jpeg / unknown
        header = b'\xff\xd8\xff\xe0'
        content_type = 'image/jpeg'
    data = header + b'\x00' * max(0, size_bytes - len(header))
    return FileStorage(
        stream=io.BytesIO(data),
        filename=filename,
        content_type=content_type,
    )


def create_listing_data(**overrides):
    """Return valid listing form data with optional overrides."""
    data = {
        'title': 'Used Textbook for CITS3403',
        'description': 'A well-maintained textbook for the Agile Web Development course.',
        'price': '25.00',
        'category': 'Textbooks',
        'condition': 'Good',
        'meetup_spot': 'Reid Library',
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def verified_client(app):
    """Create a verified user and return an authenticated client."""
    with app.app_context():
        user = User(display_name='Test User', email='test@student.uwa.edu.au')
        user.set_password('Password1')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        uid = user.id
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = uid
    return client


@pytest.fixture
def second_user_client(app):
    """Create a second verified user for ownership violation tests."""
    with app.app_context():
        user = User(display_name='Second User', email='second@student.uwa.edu.au')
        user.set_password('Password2')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        uid = user.id
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = uid
    return client


@pytest.fixture
def listing_data():
    """Default valid listing form data."""
    return create_listing_data()


# ---------------------------------------------------------------------------
# Gallery tests (MARKET-01)
# ---------------------------------------------------------------------------

def test_gallery_shows_active_listings(verified_client, app):
    """Active listings appear on the public gallery."""
    with app.app_context():
        user = User.query.first()
        listing = Listing(
            user_id=user.id,
            title='Visible Textbook',
            description='A great textbook for sale.',
            price=30.0,
            category='Textbooks',
            condition='Good',
            meetup_spot='Reid Library',
            status='active',
        )
        db.session.add(listing)
        db.session.commit()

    response = verified_client.get('/', follow_redirects=True)
    assert response.status_code == 200, f"GET / should render the gallery; got {response.status_code}"
    assert b'Visible Textbook' in response.data, (
        "active listing title 'Visible Textbook' was not rendered in the gallery -- "
        "the gallery route may have filtered out active listings, the template may "
        "have stopped iterating over 'listings', or the listing was not committed"
    )


def test_gallery_no_auth_required(client, app):
    """Gallery is accessible without login."""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200


def test_gallery_shows_sold_with_badge(verified_client, app):
    """Sold listings remain visible in the gallery with 'sold' status shown."""
    with app.app_context():
        user = User.query.first()
        listing = Listing(
            user_id=user.id,
            title='Sold Item',
            description='This item has been sold.',
            price=10.0,
            category='Electronics',
            condition='Fair',
            meetup_spot='Student Guild',
            status='sold',
        )
        db.session.add(listing)
        db.session.commit()

    response = verified_client.get('/', follow_redirects=True)
    assert response.status_code == 200, f"GET / should render; got {response.status_code}"
    assert b'Sold Item' in response.data, (
        "sold listing title 'Sold Item' was not rendered in the gallery -- "
        "sold listings should still appear (with a badge) per D-11; the gallery "
        "route may have started filtering them out"
    )


# ---------------------------------------------------------------------------
# Create listing tests (MARKET-02)
# ---------------------------------------------------------------------------

def test_create_listing(verified_client, app):
    """POST valid data creates a listing and redirects to dashboard."""
    response = verified_client.post(
        '/create-listing',
        data=create_listing_data(),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']

    with app.app_context():
        assert Listing.query.count() == 1
        listing = Listing.query.first()
        assert listing.title == 'Used Textbook for CITS3403'
        assert listing.price == 25.0
        assert listing.status == 'active'


def test_create_listing_requires_auth(client, app):
    """POST /create-listing without login redirects to /auth."""
    response = client.post(
        '/create-listing',
        data=create_listing_data(),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert '/auth' in response.headers['Location']

    with app.app_context():
        assert Listing.query.count() == 0


def test_create_listing_with_image(verified_client, app):
    """Image upload saves the file and stores the filename in the database."""
    data = create_listing_data()
    data['image'] = make_test_image('photo.jpg')

    response = verified_client.post(
        '/create-listing',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        listing = Listing.query.first()
        assert listing is not None, (
            "no Listing row was created -- the form likely failed validation; "
            "check the flash messages or form.errors"
        )
        assert listing.image_path is not None, (
            "Listing was created but image_path is NULL -- save_upload returned "
            "None (extension or magic-byte rejection) or the form did not bind the file"
        )
        assert listing.image_path.endswith('.jpg'), (
            f"expected the saved filename to keep the .jpg extension; "
            f"got image_path={listing.image_path!r}"
        )
        # Verify file exists on disk
        upload_dir = app.config['UPLOAD_FOLDER']
        full_path = os.path.join(upload_dir, listing.image_path)
        assert os.path.exists(full_path), (
            f"image_path {listing.image_path!r} is recorded in the DB but the file "
            f"is missing on disk at {full_path!r} -- save_upload may have raised "
            f"after the rename or the upload folder was cleared between save and check"
        )


def test_reject_oversized_upload(verified_client, app):
    """Files larger than 5MB are rejected with 413 Request Entity Too Large."""
    # Flask's MAX_CONTENT_LENGTH triggers 413 before the route handler runs.
    # We send a request with Content-Length > 5MB.
    data = create_listing_data()
    # Create a large dummy body by overriding content length
    big_data = b'x' * (6 * 1024 * 1024)
    response = verified_client.post(
        '/create-listing',
        data=big_data,
        content_type='multipart/form-data',
        headers={'Content-Length': str(6 * 1024 * 1024)},
        follow_redirects=False,
    )
    assert response.status_code == 413


def _make_bogus_upload(filename, body):
    """Build a FileStorage with arbitrary bytes, used by the magic-byte tests."""
    return FileStorage(
        stream=io.BytesIO(body),
        filename=filename,
        content_type='image/jpeg',
    )


def test_upload_rejected_when_bytes_are_not_an_image(verified_client, app):
    """An .jpg upload whose content is plain text must be saved with no image_path."""
    data = create_listing_data()
    data['image'] = _make_bogus_upload('text.jpg', b'This is just plain text not a JPEG')
    verified_client.post(
        '/create-listing',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    with app.app_context():
        listing = Listing.query.first()
        assert listing is not None  # listing itself is still created
        assert listing.image_path is None  # but the bogus file was rejected


def test_upload_rejected_when_disguised_as_executable(verified_client, app):
    """A Windows PE binary (MZ header) renamed to .jpg must be rejected."""
    data = create_listing_data()
    # MZ\x90\x00 is the magic for a Windows executable
    data['image'] = _make_bogus_upload('malware.jpg', b'MZ\x90\x00' + b'\x00' * 100)
    verified_client.post(
        '/create-listing',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    with app.app_context():
        listing = Listing.query.first()
        assert listing is not None
        assert listing.image_path is None


def test_upload_rejected_when_extension_contradicts_real_content(verified_client, app):
    """A .png filename containing JPEG bytes (or vice versa) is rejected."""
    data = create_listing_data()
    # JPEG magic bytes but filename claims PNG
    data['image'] = _make_bogus_upload('disguised.png', b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    verified_client.post(
        '/create-listing',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    with app.app_context():
        listing = Listing.query.first()
        assert listing is not None
        assert listing.image_path is None


# ---------------------------------------------------------------------------
# Edit listing tests (MARKET-03)
# ---------------------------------------------------------------------------

def test_edit_own_listing(verified_client, app):
    """Owner can edit their own listing."""
    with app.app_context():
        user = User.query.first()
        listing = Listing(
            user_id=user.id,
            title='Original Title',
            description='Original description here.',
            price=20.0,
            category='Textbooks',
            condition='Good',
            meetup_spot='Reid Library',
        )
        db.session.add(listing)
        db.session.commit()
        lid = listing.id

    response = verified_client.post(
        f'/edit-listing/{lid}',
        data=create_listing_data(title='Updated Title'),
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        listing = db.session.get(Listing, lid)
        assert listing.title == 'Updated Title'


def test_edit_other_user_listing_forbidden(verified_client, second_user_client, app):
    """Non-owner attempting to edit another user's listing gets 403."""
    # verified_client creates a listing
    response = verified_client.post(
        '/create-listing',
        data=create_listing_data(),
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        listing = Listing.query.first()
        assert listing is not None
        lid = listing.id

    # second_user_client tries to edit it
    response = second_user_client.post(
        f'/edit-listing/{lid}',
        data=create_listing_data(title='Hacked Title'),
        follow_redirects=False,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Delete listing tests (MARKET-04)
# ---------------------------------------------------------------------------

def test_delete_own_listing(verified_client, app):
    """Owner can delete their own listing."""
    with app.app_context():
        user = User.query.first()
        listing = Listing(
            user_id=user.id,
            title='To Be Deleted',
            description='This will be deleted.',
            price=5.0,
            category='Supplies',
            condition='Fair',
            meetup_spot='Oak Lawn',
        )
        db.session.add(listing)
        db.session.commit()
        lid = listing.id

    response = verified_client.post(
        f'/delete-listing/{lid}',
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        listing = db.session.get(Listing, lid)
        assert listing is not None
        assert listing.status == 'deleted'


def test_delete_removes_image(verified_client, app):
    """Deleting a listing removes the image file from disk."""
    data = create_listing_data()
    data['image'] = make_test_image('delete_test.png')

    verified_client.post(
        '/create-listing',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=False,
    )

    with app.app_context():
        listing = Listing.query.first()
        assert listing is not None
        lid = listing.id
        image_path = listing.image_path
        assert image_path is not None
        upload_dir = app.config['UPLOAD_FOLDER']
        full_path = os.path.join(upload_dir, image_path)
        assert os.path.exists(full_path)

    # Delete the listing
    verified_client.post(f'/delete-listing/{lid}', follow_redirects=False)

    # Image should be removed from disk
    assert not os.path.exists(full_path)


def test_delete_other_user_listing_forbidden(verified_client, second_user_client, app):
    """Non-owner attempting to delete another user's listing gets 403."""
    # verified_client creates a listing
    verified_client.post(
        '/create-listing',
        data=create_listing_data(),
        follow_redirects=False,
    )

    with app.app_context():
        listing = Listing.query.first()
        lid = listing.id

    # second_user_client tries to delete it
    response = second_user_client.post(
        f'/delete-listing/{lid}',
        follow_redirects=False,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Mark sold tests (MARKET-05)
# ---------------------------------------------------------------------------

def test_mark_sold(verified_client, app):
    """Owner can mark their listing as sold."""
    with app.app_context():
        user = User.query.first()
        listing = Listing(
            user_id=user.id,
            title='Active Item',
            description='Will be marked sold.',
            price=15.0,
            category='Electronics',
            condition='Like New',
            meetup_spot='Winthrop Hall',
        )
        db.session.add(listing)
        db.session.commit()
        lid = listing.id

    response = verified_client.post(
        f'/mark-sold/{lid}',
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        listing = db.session.get(Listing, lid)
        assert listing.status == 'sold'
