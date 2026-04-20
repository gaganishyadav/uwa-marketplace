"""Unit tests for /api/search endpoint: keyword, category, price filters, ordering."""

import pytest

from app import db
from app.models import User, Listing


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
    assert response.status_code == 200
    # All 8 seeded listings should appear
    assert b'Calculus Textbook' in response.data
    assert b'Physics Textbook' in response.data
    assert b'Laptop Stand' in response.data
    assert b'Office Chair' in response.data
    assert b'Lab Coat' in response.data
    assert b'Scientific Calculator' in response.data
    assert b'Desk Lamp' in response.data
    assert b'Highlighters Pack' in response.data


def test_search_by_keyword(search_client):
    """GET /api/search?q=textbook returns listings with 'textbook' in title or description."""
    response = search_client.get('/api/search?q=textbook')
    assert response.status_code == 200
    assert b'Calculus Textbook' in response.data
    assert b'Physics Textbook' in response.data
    # Non-textbook listings should not appear
    assert b'Laptop Stand' not in response.data
    assert b'Office Chair' not in response.data
    assert b'Lab Coat' not in response.data


def test_search_case_insensitive(search_client):
    """GET /api/search?q=TEXTBOOK returns matches regardless of case."""
    response = search_client.get('/api/search?q=TEXTBOOK')
    assert response.status_code == 200
    assert b'Calculus Textbook' in response.data
    assert b'Physics Textbook' in response.data


def test_search_by_category(search_client):
    """GET /api/search?category=Textbooks returns only Textbooks listings."""
    response = search_client.get('/api/search?category=Textbooks')
    assert response.status_code == 200
    assert b'Calculus Textbook' in response.data
    assert b'Physics Textbook' in response.data
    # Non-textbook items should not appear
    assert b'Laptop Stand' not in response.data
    assert b'Office Chair' not in response.data
    assert b'Lab Coat' not in response.data


def test_filter_min_price(search_client):
    """GET /api/search?min_price=50 returns only listings with price >= 50."""
    response = search_client.get('/api/search?min_price=50')
    assert response.status_code == 200
    assert b'Office Chair' in response.data  # $120
    assert b'Calculus Textbook' in response.data  # $45 -- should NOT appear
    # Only Office Chair ($120) meets min_price=50
    data_str = response.data.decode('utf-8')
    assert data_str.count('ad-card') == 1  # only one card rendered


def test_filter_max_price(search_client):
    """GET /api/search?max_price=30 returns only listings with price <= 30."""
    response = search_client.get('/api/search?max_price=30')
    assert response.status_code == 200
    assert b'Laptop Stand' in response.data  # $25
    assert b'Scientific Calculator' in response.data  # $20
    assert b'Desk Lamp' in response.data  # $30
    assert b'Highlighters Pack' in response.data  # $8
    assert b'Lab Coat' in response.data  # $15
    # Items over $30 should not appear
    assert b'Office Chair' not in response.data  # $120
    assert b'Calculus Textbook' not in response.data  # $45
    assert b'Physics Textbook' not in response.data  # $35


def test_filter_price_range(search_client):
    """GET /api/search?min_price=20&max_price=50 returns listings with 20 <= price <= 50."""
    response = search_client.get('/api/search?min_price=20&max_price=50')
    assert response.status_code == 200
    assert b'Calculus Textbook' in response.data  # $45
    assert b'Physics Textbook' in response.data  # $35
    assert b'Laptop Stand' in response.data  # $25
    assert b'Scientific Calculator' in response.data  # $20
    assert b'Desk Lamp' in response.data  # $30
    # Items outside range
    assert b'Office Chair' not in response.data  # $120
    assert b'Highlighters Pack' not in response.data  # $8


def test_combined_filters(search_client):
    """GET /api/search?q=textbook&category=Textbooks&min_price=10&max_price=100 returns matching listings."""
    response = search_client.get('/api/search?q=textbook&category=Textbooks&min_price=10&max_price=100')
    assert response.status_code == 200
    assert b'Calculus Textbook' in response.data  # $45, Textbooks, title matches
    assert b'Physics Textbook' in response.data  # $35, Textbooks, title matches
    # Non-matching
    assert b'Laptop Stand' not in response.data
    assert b'Office Chair' not in response.data


def test_sold_listings_after_active(search_client):
    """Response HTML shows active listings before sold listings."""
    response = search_client.get('/api/search')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    # Scientific Calculator is sold; Office Chair is active
    active_pos = data.find('Office Chair')
    sold_pos = data.find('Scientific Calculator')
    assert active_pos != -1, 'Active listing "Office Chair" not found in response'
    assert sold_pos != -1, 'Sold listing "Scientific Calculator" not found in response'
    assert active_pos < sold_pos, 'Active listings should appear before sold listings'


def test_search_empty_results(search_client):
    """GET /api/search?q=zzzzzzz returns empty state HTML with 'No listings found'."""
    response = search_client.get('/api/search?q=zzzzzzz')
    assert response.status_code == 200
    assert b'No listings found' in response.data
    assert b'btn-clear-filters' in response.data or b'Clear filters' in response.data


def test_result_count_in_response(search_client):
    """Response contains result count text like 'Showing N listings' or 'N results for ...'."""
    response = search_client.get('/api/search')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    # Should contain either "Showing N listing" or "N result"
    assert 'Showing' in data or 'result' in data

    # Also test with a query for the alternate format
    response_q = search_client.get('/api/search?q=textbook')
    assert response_q.status_code == 200
    data_q = response_q.data.decode('utf-8')
    assert 'result' in data_q


def test_search_special_like_chars(search_client):
    """GET /api/search?q=% does not act as a LIKE wildcard (escapes special chars)."""
    # Search for % should NOT match all listings
    response = search_client.get('/api/search?q=%25')
    assert response.status_code == 200
    # The %25 is URL-encoded %. It should not match everything.
    # None of our seed listings have % in their titles, so we expect empty results
    # or at most fewer results than the full set.
    data = response.data.decode('utf-8')
    # If no listings contain literal %, this should show empty state or very few matches
    # The key assertion: it should NOT return all 8 listings
    assert data.count('ad-card') < 8, 'LIKE wildcard should be escaped, not treated as wildcard'
