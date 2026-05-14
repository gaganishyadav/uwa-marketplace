"""Selenium WebDriver system test (F5): seller marks listing as sold.

Verifies the complete seller-lifecycle story:
    Alice logs in -> navigates to her listing detail page (status = active) ->
    clicks "Mark Sold" -> redirects to dashboard -> her listing card now
    shows the Sold badge -> visiting the gallery (visible to all users)
    also shows the Sold badge.

Complements the route-level tests in test_marketplace.py by exercising
the full lifecycle UX: navigation from detail page, form POST with CSRF,
post-redirect dashboard render, and the gallery's status-badge overlay
that's the visual signal buyers actually see.

Run:
    python -m pytest tests/test_selenium_mark_sold_display.py -v
    $env:DEMO_PAUSE="3"; python -m pytest tests/test_selenium_mark_sold_display.py -v
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
from selenium.webdriver.support.ui import WebDriverWait

from app import create_app, db, socketio
from app.models import Listing, User


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = '127.0.0.1'
# Distinct port from the other selenium test files (5555, 5556, 5557) so all
# four can run in the same pytest session without binding-collision.
PORT = 5558
BASE_URL = f'http://{HOST}:{PORT}'
HEADLESS = os.environ.get('HEADLESS', '0') == '1'
DEMO_PAUSE = float(os.environ.get('DEMO_PAUSE', '0'))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def selenium_app(tmp_path_factory):
    """Build a Flask app on file-based SQLite and start it in a daemon thread."""
    db_dir = tmp_path_factory.mktemp('selenium-sold-db')
    upload_dir = tmp_path_factory.mktemp('selenium-sold-uploads')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_dir / "test.db"}',
        'SECRET_KEY': 'selenium-sold-secret',
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
def seeded_alice_with_listing(selenium_app, fresh_db):
    """Seed Alice (verified seller) plus one active listing she owns.
    Yields a dict with alice_id and listing_id."""
    with selenium_app.app_context():
        alice = User(
            display_name='Alice Chen',
            email='alice@student.uwa.edu.au',
            email_verified=True,
        )
        alice.set_password('Password1')
        db.session.add(alice)
        db.session.flush()

        listing = Listing(
            user_id=alice.id,
            title='Calculus Textbook',
            description='Lightly used MATH1002 textbook in good condition.',
            price=45.0,
            category='Textbooks',
            condition='Good',
            meetup_spot='Reid Library',
            status='active',
        )
        db.session.add(listing)
        db.session.commit()

        yield {'alice_id': alice.id, 'listing_id': listing.id}


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
# F5: seller marks listing as sold
# ---------------------------------------------------------------------------

def test_seller_marks_listing_sold_and_badge_appears_everywhere(
        driver, seeded_alice_with_listing, selenium_app):
    """F5: Alice marks her active listing as Sold via the listing detail
    page. After redirect to /dashboard, her listing card shows the Sold
    overlay. The gallery (public, seen by all users) also shows the Sold
    overlay on her card.

    Covers the seller lifecycle state-change UX -- complementing the
    route-level coverage in test_marketplace.py with the actual UI flow:
    form POST with CSRF, post-redirect dashboard render, and the
    `.status-sold` overlay that's the visual signal buyers see."""
    listing_id = seeded_alice_with_listing['listing_id']
    wait = WebDriverWait(driver, 5)

    # --- 1. Alice logs in -----------------------------------------------
    _login(driver, 'alice@student.uwa.edu.au', 'Password1')
    _pause()

    # --- 2. Navigate to her listing detail page -------------------------
    driver.get(f'{BASE_URL}/listing/{listing_id}')

    # Verify the listing is still active by checking the Mark Sold button
    # is present and visible (it's hidden once status='sold').
    mark_sold_btn = wait.until(EC.element_to_be_clickable(
        (By.ID, 'btn-mark-sold')))

    # Belt-and-braces: there should be NO "Sold" status overlay yet on
    # the detail page. Use a presence check that returns False on timeout
    # so we can assert the absence.
    sold_overlays = driver.find_elements(By.CSS_SELECTOR, '.status-sold')
    assert len(sold_overlays) == 0, (
        f"Found {len(sold_overlays)} '.status-sold' element(s) on the "
        f"detail page BEFORE clicking Mark Sold -- the listing was "
        f"seeded with the wrong status, or the template's conditional "
        f"on listing.status has regressed."
    )
    _pause()

    # --- 3. Click "Mark Sold" -------------------------------------------
    mark_sold_btn.click()

    # mark_sold route redirects to /dashboard on success
    wait.until(
        EC.url_contains('/dashboard'),
        message=(
            "After clicking Mark Sold, expected a redirect to /dashboard "
            "but the URL didn't change. The POST likely returned 4xx -- "
            "check CSRF, ownership, or that the listing was active."
        ),
    )
    _pause()

    # --- 4. Verify DB state changed (sanity check) ----------------------
    with selenium_app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.status == 'sold', (
            f"Expected listing.status == 'sold' after Mark Sold; got "
            f"{listing.status!r}. The route fired but didn't commit."
        )
        assert listing.sold_at is not None, (
            "sold_at timestamp should be populated when status flips to "
            "'sold'; got None. The route is updating status without "
            "stamping the time, breaking the D-11 contract."
        )

    # --- 5. Verify the dashboard shows the Sold overlay -----------------
    # Find Alice's listing card on the dashboard by its data-id and
    # check that it carries the Sold status overlay (visible text).
    card = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, f'.ad-card[data-id="{listing_id}"]')))
    status_overlay = card.find_element(By.CSS_SELECTOR, '.ad-card-status')
    # Case-insensitive: the visible text is uppercased by CSS
    # (`text-transform: uppercase`) so .text returns 'SOLD', but the
    # underlying Jinja value is 'Sold'. Match on the meaning, not the
    # styling.
    assert 'sold' in status_overlay.text.lower(), (
        f"Dashboard listing card should display the 'Sold' status "
        f"overlay; got status text {status_overlay.text!r}. The "
        f"template may be rendering the wrong status class."
    )
    _pause()

    # --- 6. Navigate to the gallery (public view) and verify ------------
    # The gallery shows ALL listings including sold ones (per D-11), with
    # the Sold overlay distinguishing them. This is the buyer-facing
    # signal we most want to verify is correct.
    driver.get(f'{BASE_URL}/')
    gallery_card = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, f'.ad-card[data-id="{listing_id}"]')))
    gallery_overlay = gallery_card.find_element(
        By.CSS_SELECTOR, '.ad-card-status')
    assert 'sold' in gallery_overlay.text.lower(), (
        f"Gallery listing card should display the 'Sold' status overlay "
        f"(visible to all users per D-11); got status text "
        f"{gallery_overlay.text!r}."
    )
    _pause()
