"""Selenium WebDriver system test (F2): create-listing-with-image flow.

Verifies the complete user story:
    Alice logs in -> opens the "List an Item" modal from the nav ->
    fills the form (title, category, condition, price, description,
    meetup spot, image) -> submits -> the new listing (with its image)
    appears in the gallery.

Complements the route-level tests in test_marketplace.py by exercising
the real UI: modal open via JS, file upload through the browser's
file picker, form validation, multipart POST, and gallery re-render.

The map widget (MazeMap) that normally sets the hidden #ad-location
field is bypassed by injecting the value via execute_script -- driving
a third-party map through Selenium is brittle and tests nothing useful.

Run:
    python -m pytest tests/test_selenium_listing_display.py -v
    $env:HEADLESS="1"; python -m pytest tests/test_selenium_listing_display.py -v  # PowerShell
    $env:DEMO_PAUSE="3"; python -m pytest tests/test_selenium_listing_display.py -v # slow / record
"""

import os
import threading
import time
import urllib.error
import urllib.request

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from app import create_app, db, socketio
from app.models import Listing, User


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = '127.0.0.1'
# Different port from test_selenium_message_display.py (5555) so both files
# can run in the same pytest session without binding-collision.
PORT = 5556
BASE_URL = f'http://{HOST}:{PORT}'
HEADLESS = os.environ.get('HEADLESS', '0') == '1'
DEMO_PAUSE = float(os.environ.get('DEMO_PAUSE', '0'))

# Minimal valid JPEG: SOI + APP0 (JFIF) + EOI. ~20 bytes. Passes both the
# extension whitelist and the magic-byte sniff in save_upload (PR #52).
_MINIMAL_JPEG = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
    b'\xff\xd9'
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def selenium_app(tmp_path_factory):
    """Build a Flask app on file-based SQLite and start it in a daemon
    thread. File DB is required because :memory: is per-connection and
    would be invisible to the server thread."""
    db_dir = tmp_path_factory.mktemp('selenium-listing-db')
    upload_dir = tmp_path_factory.mktemp('selenium-listing-uploads')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_dir / "test.db"}',
        'SECRET_KEY': 'selenium-listing-secret',
        'WTF_CSRF_ENABLED': True,
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_DEFAULT_SENDER': 'test@example.com',
        'UPLOAD_FOLDER': str(upload_dir),
    })

    with app.app_context():
        db.create_all()

    server = threading.Thread(
        target=socketio.run,
        kwargs={
            'app': app,
            'host': HOST,
            'port': PORT,
            'allow_unsafe_werkzeug': True,
        },
        daemon=True,
    )
    server.start()
    _wait_for_server(f'{BASE_URL}/auth', timeout=10)

    yield app


@pytest.fixture
def fresh_db(selenium_app):
    """Drop and recreate all tables before each test."""
    with selenium_app.app_context():
        db.drop_all()
        db.create_all()
    yield


@pytest.fixture
def seeded_alice(selenium_app, fresh_db):
    """Insert Alice (verified seller). Returns her id."""
    with selenium_app.app_context():
        alice = User(
            display_name='Alice Chen',
            email='alice@student.uwa.edu.au',
            email_verified=True,
        )
        alice.set_password('Password1')
        db.session.add(alice)
        db.session.commit()
        yield alice.id


@pytest.fixture
def test_image_path(tmp_path):
    """Write a minimal valid JPEG to a temp file. Yields its absolute path
    as a string suitable for send_keys() on the file input."""
    path = tmp_path / 'selenium-test.jpg'
    path.write_bytes(_MINIMAL_JPEG)
    yield str(path.resolve())


@pytest.fixture
def driver():
    """Fresh Chrome browser per test."""
    options = Options()
    if HEADLESS:
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,900')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(0)
    yield drv
    drv.quit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_server(url, timeout=10):
    """Poll `url` until it returns 200, or raise after `timeout` seconds."""
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionResetError, OSError) as e:
            last_err = e
        time.sleep(0.2)
    raise RuntimeError(
        f'Selenium test server did not become ready at {url} within {timeout}s. '
        f'Last error: {last_err!r}'
    )


def _pause():
    """Sleep between UI steps if DEMO_PAUSE is set. No-op in normal runs."""
    if DEMO_PAUSE > 0:
        time.sleep(DEMO_PAUSE)


def _login(driver, email, password):
    """Log in through the /auth form. Waits until redirect off /auth."""
    driver.get(f'{BASE_URL}/auth')
    wait = WebDriverWait(driver, 5)
    wait.until(EC.visibility_of_element_located(
        (By.ID, 'login-email'))).send_keys(email)
    driver.find_element(By.ID, 'login-password').send_keys(password)
    driver.find_element(By.ID, 'btn-login-submit').click()
    wait.until(
        lambda d: '/auth' not in d.current_url,
        message=f'Login as {email} did not redirect away from /auth.'
    )


# ---------------------------------------------------------------------------
# F2: create-listing-with-image
# ---------------------------------------------------------------------------

def test_user_creates_listing_with_image_and_sees_it_in_gallery(
        driver, seeded_alice, test_image_path, selenium_app):
    """F2: Alice opens the post-ad modal, fills the form, uploads an image,
    submits, and her new listing appears in the gallery with its image.

    This system test complements the route-level tests in test_marketplace.py
    which exercise /create-listing via the Flask test client. Here we drive
    the full UI: modal-open via JS, file upload through the file picker,
    multipart submit, redirect, and listing-card render."""
    wait = WebDriverWait(driver, 5)

    # --- Alice logs in ----------------------------------------------------
    _login(driver, 'alice@student.uwa.edu.au', 'Password1')
    _pause()

    # After login Alice is on /gallery (path '/'). The "+ List an Item"
    # button lives in the global nav.
    # --- Open the post-ad modal -------------------------------------------
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'nav-post-btn'))).click()
    _pause()

    # The modal toggles open via JS (dashboard.js: openModal). Wait for
    # the title input to be both present AND interactable.
    wait.until(EC.visibility_of_element_located((By.ID, 'ad-title')))

    # --- Fill in the form fields ------------------------------------------
    # Unique title so we can find it unambiguously in the rendered gallery.
    listing_title = 'Selenium F2 Test Listing 2026-05-14'

    driver.find_element(By.ID, 'ad-title').send_keys(listing_title)
    _pause()

    # Category and Condition are <select> elements -- use Selenium's Select
    # helper rather than send_keys (more reliable across browsers).
    Select(driver.find_element(By.ID, 'ad-category')).select_by_value('Textbooks')
    Select(driver.find_element(By.ID, 'ad-condition')).select_by_value('Good')
    _pause()

    driver.find_element(By.ID, 'ad-price').send_keys('45.00')
    _pause()

    driver.find_element(By.ID, 'ad-description').send_keys(
        'Selenium-driven test listing. Created end-to-end to verify that '
        'the post-ad modal, file upload, and gallery rendering all work '
        'together as expected.'
    )
    _pause()

    # The meetup_spot field is populated by clicking on the MazeMap widget.
    # Driving a third-party interactive map through Selenium is brittle and
    # tests nothing useful, so we inject the value directly via JS. The
    # form's validators only require a non-empty string of length <= 200.
    driver.execute_script(
        "document.getElementById('ad-location').value = 'Reid Library';"
    )
    _pause()

    # Upload the image. Note: send_keys on a file <input> works even when
    # the element is hidden via CSS, because the WebDriver protocol's file
    # upload path bypasses the visibility check.
    driver.find_element(By.ID, 'ad-image').send_keys(test_image_path)
    _pause()

    # --- Submit -----------------------------------------------------------
    driver.find_element(By.ID, 'btn-submit-listing').click()

    # /create-listing commits then redirects back to the referrer (gallery
    # in our case). Wait for the modal to disappear AND the new listing
    # title to be present in the page body.
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(text(), '{listing_title}')]")
        ),
        message=(
            "After submit the new listing title was not found in the page. "
            "The form may have failed validation (check the rendered flash "
            "messages), the redirect may have gone somewhere unexpected, or "
            "the gallery query may have filtered out the new listing."
        ),
    )
    _pause()

    # --- Assert: the listing was persisted with the right values --------
    with selenium_app.app_context():
        listing = Listing.query.filter_by(title=listing_title).first()
        assert listing is not None, (
            f"Expected a Listing row with title {listing_title!r} after submit; "
            f"none found. The form likely failed validation -- check that "
            f"meetup_spot, category, and condition are all set."
        )
        assert listing.category == 'Textbooks'
        assert listing.condition == 'Good'
        assert listing.price == 45.0
        assert listing.meetup_spot == 'Reid Library'
        assert listing.image_path is not None, (
            "image_path is NULL on the new listing -- save_upload returned "
            "None, meaning the magic-byte check rejected the upload. Verify "
            "the test image starts with the JPEG SOI marker (FF D8 FF)."
        )
        assert listing.image_path.endswith('.jpg'), (
            f"Expected the saved filename to keep the .jpg extension; "
            f"got image_path={listing.image_path!r}"
        )

    # --- Assert: the gallery actually renders the image ------------------
    # Find the listing card and confirm it includes an <img> whose src
    # points at /static/uploads/<uuid>.jpg.
    cards = driver.find_elements(By.CSS_SELECTOR, '.ad-card')
    matching = [c for c in cards if listing_title in c.text]
    assert matching, (
        f"Found {len(cards)} listing cards in the gallery but none "
        f"contained the title {listing_title!r}."
    )
    card = matching[0]

    imgs = card.find_elements(By.TAG_NAME, 'img')
    assert imgs, (
        "The listing card contains no <img> element, but we uploaded an "
        "image and the DB has image_path set -- the template may have "
        "stopped rendering the image conditional."
    )
    img_src = imgs[0].get_attribute('src')
    assert '/static/uploads/' in img_src, (
        f"Listing card <img> src is {img_src!r}; expected it to point at "
        f"/static/uploads/<uuid>.jpg under the test app's UPLOAD_FOLDER."
    )


