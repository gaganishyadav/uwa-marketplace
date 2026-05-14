"""Selenium WebDriver system test (F6): admin bans user, banned user blocked.

Verifies the complete admin-governance story across two user sessions:
    Admin logs in -> opens /admin/user/<bob_id> -> sees Bob as Active ->
    clicks "Ban User" -> sees Bob's status flip to Banned -> logs out.
    Bob then logs in with correct credentials -> the @before_request
    check_ban_status hook intercepts and redirects him to /banned.

Covers what route-level tests in test_admin.py cannot:
- The full UI navigation through the admin user page
- A cross-user effect (admin's action changes another user's experience)
- The ban-enforcement before_request hook firing during real navigation

Run:
    python -m pytest tests/test_selenium_admin_display.py -v
    $env:DEMO_PAUSE="3"; python -m pytest tests/test_selenium_admin_display.py -v
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
from app.models import User


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = '127.0.0.1'
# Distinct port from the other selenium test files (5555, 5556, 5557, 5558)
# so all five can run in the same pytest session without binding-collision.
PORT = 5559
BASE_URL = f'http://{HOST}:{PORT}'
HEADLESS = os.environ.get('HEADLESS', '0') == '1'
DEMO_PAUSE = float(os.environ.get('DEMO_PAUSE', '0'))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def selenium_app(tmp_path_factory):
    """Build a Flask app on file-based SQLite and start it in a daemon thread."""
    db_dir = tmp_path_factory.mktemp('selenium-admin-db')
    upload_dir = tmp_path_factory.mktemp('selenium-admin-uploads')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_dir / "test.db"}',
        'SECRET_KEY': 'selenium-admin-secret',
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
def seeded_admin_and_user(selenium_app, fresh_db):
    """Seed an admin account plus a regular verified user (Bob). Both have
    email_verified=True and matching passwords so login goes straight to
    gallery. Yields the two user IDs."""
    with selenium_app.app_context():
        admin = User(
            display_name='Admin',
            email='admin@student.uwa.edu.au',
            email_verified=True,
            is_admin=True,
        )
        admin.set_password('AdminPass1')

        bob = User(
            display_name='Bob Martinez',
            email='bob@student.uwa.edu.au',
            email_verified=True,
        )
        bob.set_password('Password1')

        db.session.add_all([admin, bob])
        db.session.commit()
        yield {'admin_id': admin.id, 'bob_id': bob.id}


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


def _logout(driver):
    """Open the nav dropdown and click Log Out."""
    wait = WebDriverWait(driver, 5)
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'nav-avatar-btn'))).click()
    wait.until(EC.element_to_be_clickable(
        (By.ID, 'btn-logout'))).click()
    wait.until(
        lambda d: '/dashboard' not in d.current_url
                  and '/inbox' not in d.current_url,
        message='Logout did not navigate away from authenticated pages.'
    )


# ---------------------------------------------------------------------------
# F6: admin bans user, banned user is blocked on next login
# ---------------------------------------------------------------------------

def test_admin_bans_user_and_banned_user_is_blocked(
        driver, seeded_admin_and_user, selenium_app):
    """F6: Admin opens the admin user page for Bob, clicks Ban User, and
    sees Bob's status flip to Banned. After admin logs out, Bob attempts
    to log in with the correct password -- the check_ban_status hook
    intercepts and redirects him to /banned, never letting him reach
    the gallery."""
    bob_id = seeded_admin_and_user['bob_id']
    wait = WebDriverWait(driver, 5)

    # --- 1. Admin logs in -----------------------------------------------
    _login(driver, 'admin@student.uwa.edu.au', 'AdminPass1')
    _pause()

    # --- 2. Admin navigates to Bob's admin user page --------------------
    driver.get(f'{BASE_URL}/admin/user/{bob_id}')

    # Bob should show as Active right now.
    active_badge = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '.admin-user-status--active')))
    assert 'active' in active_badge.text.lower(), (
        f"Bob's status should show 'Active' before banning; got "
        f"{active_badge.text!r}. The status pill may be rendering "
        f"the wrong class."
    )
    _pause()

    # --- 3. Click "Ban User" --------------------------------------------
    driver.find_element(By.ID, 'btn-ban-user').click()

    # The route redirects back to /admin/user/<bob_id>. After reload, the
    # Banned status pill replaces the Active one and the Ban/Permanent
    # buttons disappear in favour of an Unban button.
    banned_badge = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '.admin-user-status--banned')))
    assert 'banned' in banned_badge.text.lower(), (
        f"Bob's status should show 'Banned' after the ban click; got "
        f"{banned_badge.text!r}."
    )
    _pause()

    # --- 4. DB-level sanity check ---------------------------------------
    with selenium_app.app_context():
        bob = db.session.get(User, bob_id)
        assert bob.ban_status == 'banned', (
            f"Expected bob.ban_status == 'banned' after the ban click; "
            f"got {bob.ban_status!r}. The route fired but didn't commit."
        )

    # --- 5. Admin logs out ----------------------------------------------
    _logout(driver)
    _pause()

    # --- 6. Bob tries to log in -----------------------------------------
    # Login itself succeeds at the auth layer (correct credentials).
    # Then the @before_request check_ban_status hook fires on the next
    # navigation and redirects to /banned.
    _login(driver, 'bob@student.uwa.edu.au', 'Password1')
    wait.until(
        EC.url_contains('/banned'),
        message=(
            "Banned user Bob should land on /banned after login, but "
            "the URL didn't include '/banned'. The check_ban_status "
            "before_request hook may not be firing, or the ban_status "
            "column wasn't actually updated."
        ),
    )
    _pause()

    # --- 7. Verify Bob is stuck on /banned -------------------------------
    # Even if Bob tries to navigate to /dashboard (or anywhere
    # authenticated), the hook should bounce him back to /banned.
    driver.get(f'{BASE_URL}/dashboard')
    wait.until(
        EC.url_contains('/banned'),
        message=(
            "Banned user should be redirected back to /banned when "
            "trying to access /dashboard. The check_ban_status hook "
            "isn't intercepting subsequent navigation."
        ),
    )
    _pause()
