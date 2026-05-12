"""Selenium WebDriver system test (F4): end-to-end messaging flow.

Verifies the complete user story:
    Bob (buyer) logs in -> opens Alice's listing -> sends a message ->
    Bob logs out -> Alice logs in -> Alice sees the message in her inbox.

The fixtures spin up a real Flask + SocketIO server in a background thread
backed by a file-based SQLite (NOT :memory:, which is per-connection and
invisible to the server thread). Each test gets a fresh database and a
fresh Chrome browser instance.

Run:
    python -m pytest tests/test_selenium_message_display.py -v             # headed (default)
    HEADLESS=1 python -m pytest tests/test_selenium_message_display.py -v  # bash/zsh
    $env:HEADLESS="1"; python -m pytest tests/test_selenium_message_display.py -v  # PowerShell

Demo / screen-recording mode (slows each UI step to ~3s so viewers can follow):
    $env:DEMO_PAUSE="3"; python -m pytest tests/test_selenium_message_display.py -v
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
PORT = 5555
BASE_URL = f'http://{HOST}:{PORT}'
HEADLESS = os.environ.get('HEADLESS', '0') == '1'

# Seconds to pause between major UI steps when DEMO_PAUSE is set. Default 0
# keeps regular test runs fast; set to ~3 when screen-recording the flow so
# viewers can follow each step. Has no effect on assertions.
DEMO_PAUSE = float(os.environ.get('DEMO_PAUSE', '0'))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def selenium_app(tmp_path_factory):
    """Build a Flask app backed by a file-based SQLite, start it in a daemon
    thread, and yield the app. The daemon thread terminates when the test
    process exits; no explicit teardown is needed.
    """
    db_dir = tmp_path_factory.mktemp('selenium-db')
    upload_dir = tmp_path_factory.mktemp('selenium-uploads')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_dir / "test.db"}',
        'SECRET_KEY': 'selenium-secret-key',
        # CSRF must be ON because we're driving real form submissions through
        # a real browser; the unit-test conftest disables it for raw POST
        # convenience, but that path doesn't apply here.
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
            # Flask-SocketIO 5.x refuses to run on werkzeug's dev server
            # without this opt-in. Acceptable for tests.
            'allow_unsafe_werkzeug': True,
        },
        daemon=True,
    )
    server.start()

    _wait_for_server(f'{BASE_URL}/auth', timeout=10)

    yield app


@pytest.fixture
def fresh_db(selenium_app):
    """Drop and recreate all tables before each test so tests don't bleed
    state into one another."""
    with selenium_app.app_context():
        db.drop_all()
        db.create_all()
    yield


@pytest.fixture
def seeded_users(selenium_app, fresh_db):
    """Insert Alice (seller) + Bob (buyer), both verified, and one active
    listing owned by Alice. Yields the three IDs for use in the test."""
    with selenium_app.app_context():
        alice = User(
            display_name='Alice Chen',
            email='alice@student.uwa.edu.au',
            email_verified=True,
        )
        alice.set_password('Password1')

        bob = User(
            display_name='Bob Martinez',
            email='bob@student.uwa.edu.au',
            email_verified=True,
        )
        bob.set_password('Password1')

        db.session.add_all([alice, bob])
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

        yield {
            'alice_id': alice.id,
            'bob_id': bob.id,
            'listing_id': listing.id,
        }


@pytest.fixture
def driver():
    """Fresh Chrome browser per test. Closes on teardown."""
    options = Options()
    if HEADLESS:
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,900')
    # The next two flags reduce surprises in restricted environments.
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    drv = webdriver.Chrome(options=options)
    # We rely on explicit WebDriverWait everywhere; implicit waits would
    # interleave with explicit ones and cause confusing timeouts.
    drv.implicitly_wait(0)
    yield drv
    drv.quit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pause():
    """Sleep between UI steps if DEMO_PAUSE is set. No-op in normal test runs."""
    if DEMO_PAUSE > 0:
        time.sleep(DEMO_PAUSE)


def _wait_for_server(url, timeout=10):
    """Poll `url` until it responds with HTTP 200, or raise after `timeout`."""
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


def _login(driver, email, password):
    """Log in through the /auth form. Waits until the redirect navigates
    away from /auth (i.e. successful login)."""
    driver.get(f'{BASE_URL}/auth')

    wait = WebDriverWait(driver, 5)
    wait.until(EC.visibility_of_element_located(
        (By.ID, 'login-email'))).send_keys(email)
    driver.find_element(By.ID, 'login-password').send_keys(password)
    driver.find_element(By.ID, 'btn-login-submit').click()

    # On success we redirect to /gallery (path '/'). On failure the form
    # re-renders at /auth with an error.
    wait.until(
        lambda d: '/auth' not in d.current_url,
        message=f'Login as {email} did not redirect away from /auth -- '
                f'credentials wrong, user not verified, or form rejected.'
    )


def _logout(driver):
    """Open the avatar dropdown and click Log Out."""
    wait = WebDriverWait(driver, 5)
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'nav-avatar-btn'))).click()
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'btn-logout'))).click()
    # After logout the server redirects somewhere public (gallery or /auth).
    wait.until(
        lambda d: '/dashboard' not in d.current_url
                  and '/inbox' not in d.current_url,
        message='Logout did not navigate away from authenticated pages.'
    )


# ---------------------------------------------------------------------------
# F4: end-to-end messaging
# ---------------------------------------------------------------------------

def test_buyer_sends_message_and_seller_sees_it_in_inbox(driver, seeded_users):
    """F4: Bob messages Alice's listing -> Alice sees it in her inbox.

    This is a system-level (Selenium) test, complementary to the existing
    unit tests in test_messaging.py. The unit tests exercise the routes
    via Flask's test client; this test exercises the full UI path including
    JavaScript (modal open, AJAX submit, redirect) and the inbox render."""
    listing_id = seeded_users['listing_id']
    wait = WebDriverWait(driver, 5)

    # --- Bob (buyer) logs in ----------------------------------------------
    _login(driver, 'bob@student.uwa.edu.au', 'Password1')
    _pause()

    # --- Bob opens Alice's listing ----------------------------------------
    driver.get(f'{BASE_URL}/listing/{listing_id}')
    _pause()

    # --- Bob opens the "Message Seller" modal -----------------------------
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'btn-message-seller'))).click()
    _pause()

    # --- Bob types and sends the message ----------------------------------
    msg_text = 'Hi Alice, is this textbook still available?'
    textarea = wait.until(EC.visibility_of_element_located(
        (By.ID, 'message-content')))
    textarea.send_keys(msg_text)
    _pause()
    driver.find_element(By.ID, 'btn-send-message').click()

    # The send endpoint returns JSON {redirect: '/inbox?thread=...'} and
    # inbox.js navigates window.location to it. We wait for the URL change
    # as proof the AJAX call succeeded.
    wait.until(
        EC.url_contains('/inbox'),
        message='Send did not trigger a redirect to /inbox -- the AJAX call '
                'probably returned a 4xx (CSRF? auth? validation?).'
    )
    _pause()

    # --- Bob logs out -----------------------------------------------------
    _logout(driver)
    _pause()

    # --- Alice (seller) logs in ------------------------------------------
    _login(driver, 'alice@student.uwa.edu.au', 'Password1')
    _pause()

    # --- Alice opens her inbox -------------------------------------------
    driver.get(f'{BASE_URL}/inbox')
    _pause()

    # --- Assert: Alice sees the conversation -----------------------------
    inbox_rows = driver.find_elements(By.CSS_SELECTOR, '.inbox-row')
    assert len(inbox_rows) >= 1, (
        f"Alice's inbox should show at least one conversation after Bob's "
        f'message; found {len(inbox_rows)}. The message was either not '
        f'persisted, or the inbox query is filtering it out.'
    )

    combined_text = ' '.join(row.text for row in inbox_rows)

    assert 'Bob' in combined_text, (
        f"Alice's inbox should list 'Bob' (Bob Martinez) as the "
        f'conversation partner; rendered text was:\n{combined_text}'
    )

    # The conversation preview truncates content to 80 chars in inbox.html
    # (`conv.content[:80]`). Our message is ~46 chars, so the full text
    # fits. We still assert on a substring to be resilient to punctuation
    # changes.
    assert 'still available' in combined_text.lower(), (
        f"Alice's inbox should show Bob's message preview "
        f"(sent: {msg_text!r}); rendered text was:\n{combined_text}"
    )
