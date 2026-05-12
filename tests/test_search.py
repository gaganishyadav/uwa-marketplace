"""Unit tests for /api/search endpoint: keyword, category, price filters, ordering."""

import pytest

from app import db
from app.models import User, Listing


def _assert_listings(response, expected=(), forbidden=(), query_label=''):
    """Assert each title in `expected` appears in the response body and each
    title in `forbidden` does not. On failure, report exactly which titles
    were missing or unexpectedly present so the cause is visible at a glance.
    """
    body = response.data
    missing = [t for t in expected if t.encode() not in body]
    leaked = [t for t in forbidden if t.encode() in body]
    if missing or leaked:
        ctx = f' for {query_label}' if query_label else ''
        raise AssertionError(
            f"/api/search result set mismatch{ctx}:\n"
            f"  expected but missing: {missing}\n"
            f"  forbidden but present: {leaked}"
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def search_client(app):
    """Create authenticated client with seeded listings for search tests."""
    with app.app_context():
        user = User(display_name='Search Tester', email='searcher@student.uwa.edu.au')
        user.set_password('Password1')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        uid = user.id

        listings = [
            Listing(user_id=uid, title='Calculus Textbook',
                    description='Used for MATH1002', price=45.0,
                    category='Textbooks', condition='Good',
                    meetup_spot='Reid Library', status='active'),
            Listing(user_id=uid, title='Physics Textbook',
                    description='University physics textbook', price=35.0,
                    category='Textbooks', condition='Fair',
                    meetup_spot='Reid Library', status='active'),
            Listing(user_id=uid, title='Laptop Stand',
                    description='Aluminum laptop stand, like new', price=25.0,
                    category='Electronics', condition='Like New',
                    meetup_spot='Student Guild', status='active'),
            Listing(user_id=uid, title='Office Chair',
                    description='Ergonomic office chair', price=120.0,
                    category='Furniture', condition='Good',
                    meetup_spot='Oak Lawn', status='active'),
            Listing(user_id=uid, title='Lab Coat',
                    description='Chemistry lab coat size M', price=15.0,
                    category='Clothing', condition='New',
                    meetup_spot='Winthrop Hall', status='active'),
            Listing(user_id=uid, title='Scientific Calculator',
                    description='Casio fx-82 calculator', price=20.0,
                    category='Electronics', condition='Good',
                    meetup_spot='Student Guild', status='sold'),
            Listing(user_id=uid, title='Desk Lamp',
                    description='LED desk lamp', price=30.0,
                    category='Furniture', condition='Like New',
                    meetup_spot='Reid Library', status='active'),
            Listing(user_id=uid, title='Highlighters Pack',
                    description='Pack of 8 highlighters', price=8.0,
                    category='Supplies', condition='New',
                    meetup_spot='Oak Lawn', status='active'),
        ]
        for l in listings:
            db.session.add(l)
        db.session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = uid
    return client


# ---------------------------------------------------------------------------
# Search tests (MARKET-06, MARKET-07, MARKET-08)
# ---------------------------------------------------------------------------

def test_search_no_params_returns_all(search_client):
    """GET /api/search with no params returns all listings (status 200)."""
    response = search_client.get('/api/search')
    assert response.status_code == 200, f"GET /api/search should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Calculus Textbook', 'Physics Textbook', 'Laptop Stand',
                  'Office Chair', 'Lab Coat', 'Scientific Calculator',
                  'Desk Lamp', 'Highlighters Pack'],
        query_label='no filters')


def test_search_by_keyword(search_client):
    """GET /api/search?q=textbook returns listings with 'textbook' in title or description."""
    response = search_client.get('/api/search?q=textbook')
    assert response.status_code == 200, f"keyword search should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Calculus Textbook', 'Physics Textbook'],
        forbidden=['Laptop Stand', 'Office Chair', 'Lab Coat'],
        query_label='q=textbook')


def test_search_case_insensitive(search_client):
    """GET /api/search?q=TEXTBOOK returns matches regardless of case."""
    response = search_client.get('/api/search?q=TEXTBOOK')
    assert response.status_code == 200, f"uppercase search should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Calculus Textbook', 'Physics Textbook'],
        query_label='q=TEXTBOOK (case-insensitivity check -- ilike may have become like)')


def test_search_by_category(search_client):
    """GET /api/search?category=Textbooks returns only Textbooks listings."""
    response = search_client.get('/api/search?category=Textbooks')
    assert response.status_code == 200, f"category filter should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Calculus Textbook', 'Physics Textbook'],
        forbidden=['Laptop Stand', 'Office Chair', 'Lab Coat'],
        query_label='category=Textbooks')


def test_filter_min_price(search_client):
    """GET /api/search?min_price=50 returns only listings with price >= 50."""
    response = search_client.get('/api/search?min_price=50')
    assert response.status_code == 200, f"min_price filter should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Office Chair'],  # $120
        forbidden=['Calculus Textbook',   # $45
                   'Physics Textbook',    # $35
                   'Laptop Stand',        # $25
                   'Highlighters Pack'],  # $8
        query_label='min_price=50 (boundary -- ">=" vs ">" mismatch shows here)')


def test_filter_max_price(search_client):
    """GET /api/search?max_price=30 returns only listings with price <= 30."""
    response = search_client.get('/api/search?max_price=30')
    assert response.status_code == 200, f"max_price filter should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Laptop Stand',          # $25
                  'Scientific Calculator', # $20
                  'Desk Lamp',             # $30 -- boundary
                  'Highlighters Pack',     # $8
                  'Lab Coat'],             # $15
        forbidden=['Office Chair',         # $120
                   'Calculus Textbook',    # $45
                   'Physics Textbook'],    # $35
        query_label='max_price=30 (boundary -- "<=" vs "<" mismatch shows here)')


def test_filter_price_range(search_client):
    """GET /api/search?min_price=20&max_price=50 returns listings with 20 <= price <= 50."""
    response = search_client.get('/api/search?min_price=20&max_price=50')
    assert response.status_code == 200, f"price-range filter should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Calculus Textbook',    # $45
                  'Physics Textbook',     # $35
                  'Laptop Stand',         # $25
                  'Scientific Calculator',# $20 -- boundary
                  'Desk Lamp'],           # $30
        forbidden=['Office Chair',        # $120
                   'Highlighters Pack'],  # $8
        query_label='min_price=20 & max_price=50')


def test_combined_filters(search_client):
    """GET /api/search?q=textbook&category=Textbooks&min_price=10&max_price=100 returns matching listings."""
    response = search_client.get('/api/search?q=textbook&category=Textbooks&min_price=10&max_price=100')
    assert response.status_code == 200, f"combined filter should be 200; got {response.status_code}"
    _assert_listings(response,
        expected=['Calculus Textbook', 'Physics Textbook'],
        forbidden=['Laptop Stand', 'Office Chair'],
        query_label='q=textbook & category=Textbooks & min=10 & max=100')


def test_sold_listings_after_active(search_client):
    """Response HTML shows active listings before sold listings."""
    response = search_client.get('/api/search')
    assert response.status_code == 200, f"unfiltered search should be 200; got {response.status_code}"
    data = response.data.decode('utf-8')
    # Scientific Calculator is sold; Office Chair is active
    active_pos = data.find('Office Chair')
    sold_pos = data.find('Scientific Calculator')
    assert active_pos != -1, 'active listing "Office Chair" not found in response'
    assert sold_pos != -1, 'sold listing "Scientific Calculator" not found in response'
    assert active_pos < sold_pos, (
        f'active listings should render before sold listings (per D-11): '
        f'Office Chair (active) is at offset {active_pos}, '
        f'Scientific Calculator (sold) is at offset {sold_pos} -- '
        f'the sort order in /api/search has regressed'
    )


def test_search_empty_results(search_client):
    """GET /api/search?q=zzzzzzz returns empty state HTML with 'No listings found'."""
    response = search_client.get('/api/search?q=zzzzzzz')
    assert response.status_code == 200, f"empty-results query should be 200; got {response.status_code}"
    assert b'No listings found' in response.data, (
        "expected the empty-state copy 'No listings found' for a query with zero "
        "matches -- the empty-state branch may have been removed from "
        "_search_results.html or 'q=zzzzzzz' is unexpectedly matching something"
    )
    # Accept either button label spelling -- name the expected variants on failure
    has_clear = b'btn-clear-filters' in response.data or b'Clear filters' in response.data
    assert has_clear, (
        "expected the empty state to expose a clear-filters affordance via either "
        "the id 'btn-clear-filters' or the visible label 'Clear filters'; neither "
        "was found in the response body"
    )


def test_result_count_in_response(search_client):
    """Response contains result count text like 'Showing N listings' or 'N results for ...'."""
    response = search_client.get('/api/search')
    assert response.status_code == 200, f"unfiltered search should be 200; got {response.status_code}"
    data = response.data.decode('utf-8')
    # Should contain either "Showing N listing" or "N result"
    assert ('Showing' in data) or ('result' in data), (
        "expected either 'Showing N listings' or 'N result(s)' on the unfiltered "
        "response so the user has feedback on how many results match; neither "
        "appeared -- the count line in _search_results.html may have been removed"
    )

    # Also test with a query for the alternate format
    response_q = search_client.get('/api/search?q=textbook')
    assert response_q.status_code == 200, f"keyword search should be 200; got {response_q.status_code}"
    data_q = response_q.data.decode('utf-8')
    assert 'result' in data_q, (
        "expected the query response to switch to a 'N result(s) for q' phrasing "
        "(per D-12); not finding 'result' suggests the count_text branch for "
        "queried searches was removed"
    )


def test_search_special_like_chars(search_client):
    """GET /api/search?q=% does not act as a LIKE wildcard (escapes special chars)."""
    # Search for % should NOT match all listings
    response = search_client.get('/api/search?q=%25')
    assert response.status_code == 200, f"search with %-escaped query should be 200; got {response.status_code}"
    # The %25 is URL-encoded %. It should not match everything.
    # None of our seed listings have % in their titles, so we expect empty results
    # or at most fewer results than the full set.
    data = response.data.decode('utf-8')
    card_count = data.count('ad-card')
    assert card_count < 8, (
        f"LIKE wildcard escaping is broken: searching for '%' returned {card_count} "
        f"ad-card matches (out of 8 seeded). '%' should be treated as a literal "
        f"character, not a SQL wildcard, so no seed listings should match"
    )
