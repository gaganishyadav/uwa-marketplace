"""Selenium WebDriver system test (F3): search / filter the gallery.

Verifies the complete buyer-discovery story:
    Anonymous visitor opens the gallery -> sees all listings ->
    types a keyword (debounced AJAX) -> sees filtered results ->
    clicks a category pill -> sees re-filtered results ->
    sets a price range -> sees re-filtered results ->
    clears everything -> sees all listings again.

Complements the route-level tests in test_search.py by exercising the
real UI: the 300ms debounce, the AJAX GET /api/search, the
jQuery-driven DOM swap of #gallery-grid, and the visual #result-count.

Run:
    python -m pytest tests/test_selenium_search_display.py -v
    $env:DEMO_PAUSE="3"; python -m pytest tests/test_selenium_search_display.py -v
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
# Distinct port from the other selenium test files (5555, 5556) so all three
# can run in the same pytest session without binding-collision.
PORT = 5557
BASE_URL = f'http://{HOST}:{PORT}'
HEADLESS = os.environ.get('HEADLESS', '0') == '1'
DEMO_PAUSE = float(os.environ.get('DEMO_PAUSE', '0'))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def selenium_app(tmp_path_factory):
    """Build a Flask app on file-based SQLite and start it in a daemon thread."""
    db_dir = tmp_path_factory.mktemp('selenium-search-db')
    upload_dir = tmp_path_factory.mktemp('selenium-search-uploads')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_dir / "test.db"}',
        'SECRET_KEY': 'selenium-search-secret',
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
def seeded_listings(selenium_app, fresh_db):
    """Seed a small, varied catalog covering multiple categories and prices
    so the search/filter scenarios have distinct expected outcomes."""
    with selenium_app.app_context():
        seller = User(
            display_name='Seed Seller',
            email='seed@student.uwa.edu.au',
            email_verified=True,
        )
        seller.set_password('Password1')
        db.session.add(seller)
        db.session.flush()

        # Each (title, category, price) tuple is chosen so the test
        # assertions can unambiguously match a single listing.
        rows = [
            ('Calculus Textbook',  'Textbooks',   45.0),
            ('Physics Textbook',   'Textbooks',   35.0),
            ('Laptop Stand',       'Electronics', 25.0),
            ('Office Chair',       'Furniture',  120.0),
        ]
        for title, category, price in rows:
            db.session.add(Listing(
                user_id=seller.id,
                title=title,
                description=f'Test listing for {title}. ' * 3,
                price=price,
                category=category,
                condition='Good',
                meetup_spot='Reid Library',
                status='active',
            ))
        db.session.commit()


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


def _wait_for_filtered_results(driver, present=(), absent=(), timeout=5):
    """Wait until #gallery-grid contains every title in `present` and none
    of the titles in `absent`. This is how we wait for the 300ms debounce
    + AJAX round-trip + jQuery DOM swap to settle.

    Reports both missing and unexpectedly-leaked titles on failure, so a
    regression points straight at the broken filter."""
    def check(d):
        grid = d.find_element(By.ID, 'gallery-grid')
        body = grid.text
        missing = [t for t in present if t not in body]
        leaked = [t for t in absent if t in body]
        return not missing and not leaked

    try:
        WebDriverWait(driver, timeout).until(check)
    except Exception:
        # Re-evaluate at failure time to produce a useful error.
        body = driver.find_element(By.ID, 'gallery-grid').text
        missing = [t for t in present if t not in body]
        leaked = [t for t in absent if t in body]
        raise AssertionError(
            f"Gallery filter result mismatch after {timeout}s:\n"
            f"  expected but missing: {missing}\n"
            f"  forbidden but present: {leaked}\n"
            f"Rendered grid text:\n{body[:500]}"
        )


# ---------------------------------------------------------------------------
# F3: search and filter the gallery
# ---------------------------------------------------------------------------

def test_anonymous_buyer_searches_and_filters_the_gallery(driver, seeded_listings):
    """F3: An anonymous visitor narrows the gallery by keyword, category,
    and price -- each interaction triggers a debounced AJAX call that
    swaps #gallery-grid in place. Verifies the full client-side UX, which
    test_search.py exercises only at the route level."""
    wait = WebDriverWait(driver, 5)
    all_titles = ['Calculus Textbook', 'Physics Textbook', 'Laptop Stand', 'Office Chair']

    # --- 1. Open the gallery anonymously ---------------------------------
    driver.get(f'{BASE_URL}/')
    wait.until(EC.presence_of_element_located((By.ID, 'search-input')))
    _wait_for_filtered_results(driver, present=all_titles)
    _pause()

    # --- 2. Search by keyword ('textbook') -------------------------------
    # Typing fires the debounced /api/search call. We expect both textbooks
    # to remain and the non-textbook listings to disappear.
    search_input = driver.find_element(By.ID, 'search-input')
    search_input.send_keys('textbook')
    _wait_for_filtered_results(
        driver,
        present=['Calculus Textbook', 'Physics Textbook'],
        absent=['Laptop Stand', 'Office Chair'],
    )
    _pause()

    # --- 3. Clear search and switch to category filter -------------------
    # Clear the search box, then click the Electronics filter pill.
    driver.find_element(By.ID, 'search-clear').click()
    _wait_for_filtered_results(driver, present=all_titles)
    _pause()

    driver.find_element(
        By.CSS_SELECTOR, '.filter-pill[data-category="Electronics"]'
    ).click()
    _wait_for_filtered_results(
        driver,
        present=['Laptop Stand'],
        absent=['Calculus Textbook', 'Physics Textbook', 'Office Chair'],
    )
    _pause()

    # --- 4. Reset to 'All', then apply a price-range filter --------------
    driver.find_element(By.ID, 'filter-all').click()
    _wait_for_filtered_results(driver, present=all_titles)
    _pause()

    # min_price=100 should leave only Office Chair ($120). Others are $25-$45.
    driver.find_element(By.ID, 'min-price').send_keys('100')
    _wait_for_filtered_results(
        driver,
        present=['Office Chair'],
        absent=['Calculus Textbook', 'Physics Textbook', 'Laptop Stand'],
    )
    _pause()

    # --- 5. Add a max_price that excludes Office Chair --------------------
    # Now min=100 AND max=110 -> no listings match (Office Chair is $120).
    # Verifies the empty-state path.
    driver.find_element(By.ID, 'max-price').send_keys('110')
    _wait_for_filtered_results(
        driver,
        absent=all_titles,  # all four listings must be filtered out
    )
    # Empty state copy from gallery.html should appear.
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'No listings found') or "
                       "contains(text(), 'No listings yet')]")
        ),
        message=(
            "Expected an empty-state message after applying a price range "
            "with no matches, but no 'No listings' copy appeared. The "
            "empty-state branch in _search_results.html may have regressed."
        ),
    )
    _pause()

    # --- 6. Verify the result-count text reflects filter changes ---------
    # After the impossible filter (min=100, max=110), result count should
    # be 0. Use a wait because the DOM swap is asynchronous.
    wait.until(
        lambda d: '0' in d.find_element(By.ID, 'result-count').text.lower()
                  or 'no listings' in d.find_element(By.ID, 'result-count').text.lower(),
        message=(
            "Expected #result-count to read '0' or 'No listings' after the "
            "impossible filter, but got: "
            f"{driver.find_element(By.ID, 'result-count').text!r}"
        ),
    )
