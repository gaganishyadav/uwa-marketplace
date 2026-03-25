# Testing Patterns

**Analysis Date:** 2026-03-25

## Test Framework

**Runner:**
- pytest (recommended) or unittest
- Config: `tests/test_unit.py` for backend unit tests

**Selenium:**
- Selenium WebDriver for browser automation
- Config: `tests/test_selenium.py` for E2E tests

**Assertion Library:**
- Python: built-in `assert` statement or unittest assertions

**Run Commands:**
```bash
# Run all unit tests
pytest tests/test_unit.py

# Run with coverage
pytest --cov=app tests/test_unit.py

# Run Selenium tests
python tests/test_selenium.py

# Run specific test
pytest tests/test_unit.py::test_password_hashing
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root

**Naming:**
- Unit tests: `test_unit.py`
- Selenium tests: `test_selenium.py`

**Structure:**
```
tests/
├── test_unit.py       # Backend unit tests (5+ required)
└── test_selenium.py   # Frontend integration tests (5+ required)
```

## Test Structure

**Suite Organization:**
```python
# Unit test structure
import unittest
from app.models import User, Listing
from app import create_app, db
from werkzeug.security import generate_password_hash, check_password_hash

class TestModels(unittest.TestCase):
    def setUp(self):
        """Create test app and database."""
        self.app = create_app(testing=True)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up database."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        """Test User model can be created."""
        user = User(username='testuser', email='test@uwa.edu.au')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        assert user.id is not None

    def test_password_hashing(self):
        """Test passwords are hashed correctly."""
        user = User(username='testuser')
        user.set_password('password123')
        assert user.check_password('password123') is True
        assert user.check_password('wrongpass') is False
```

**Patterns:**
- Setup: Create test app context and in-memory database
- Teardown: Drop all tables and remove context
- Assertion: Use `assert` statements or unittest methods

## Mocking

**Framework:** unittest.mock

**Patterns:**
```python
from unittest.mock import patch, MagicMock

class TestRoutes(unittest.TestCase):
    @patch('app.routes.login_required')
    def test_protected_route_requires_auth(self, mock_login):
        """Test protected routes redirect without auth."""
        # Test route access control
        pass

    def test_route_access_control(self):
        """Test users can only edit their own listings."""
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        listing = self.create_listing(user1.id)

        # user2 should not be able to edit user1's listing
        response = self.client.post(f'/listings/{listing.id}/edit', data={...})
        assert response.status_code == 403
```

**What to Mock:**
- External API calls (if any)
- Email sending (for notifications)
- File uploads (use temp files)

**What NOT to Mock:**
- Database models (use test database)
- Flask route handlers
- Password hashing functions

## Fixtures and Factories

**Test Data:**
```python
class TestFactories(unittest.TestCase):
    def create_user(self, username, email='test@uwa.edu.au'):
        """Factory for creating test users."""
        user = User(username=username, email=email)
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user

    def create_listing(self, user_id, title='Test Item'):
        """Factory for creating test listings."""
        listing = Listing(
            title=title,
            description='Test description',
            price=10.00,
            category='textbooks',
            user_id=user_id
        )
        db.session.add(listing)
        db.session.commit()
        return listing
```

**Location:**
- Define factory methods within test classes
- Or create `tests/factories.py` for shared fixtures

## Coverage

**Requirements:** 5+ unit tests required (per brief)

**View Coverage:**
```bash
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html
```

## Test Types

**Unit Tests (5+ required):**
- Model validation (User, Listing)
- Password hashing (werkzeug.security)
- Route access control (login_required, ownership checks)
- CRUD operations
- Form validation

**Integration Tests:**
- Database session handling
- CSRF token handling
- Flash messaging

**E2E Tests (5+ Selenium tests required):**
- User registration flow
- Login/logout flow
- Create listing flow
- Browse listings with AJAX filtering
- Edit/delete own listing

## Common Patterns

**Async Testing:**
- Not applicable (Flask is synchronous)

**Error Testing:**
```python
def test_invalid_login(self):
    """Test login with invalid credentials."""
    response = self.client.post('/login', data={
        'username': 'nonexistent',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_duplicate_username(self):
    """Test duplicate usernames are rejected."""
    user1 = self.create_user('testuser')
    user2 = User(username='testuser', email='different@uwa.edu.au')
    db.session.add(user2)
    with self.assertRaises(IntegrityError):
        db.session.commit()
```

## Selenium Test Patterns

**Setup:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestSelenium(unittest.TestCase):
    def setUp(self):
        """Initialize Selenium WebDriver."""
        self.driver = webdriver.Chrome()
        self.driver.get('http://localhost:5000')

    def tearDown(self):
        """Close browser."""
        self.driver.quit()

    def test_login_flow(self):
        """Test complete login user journey."""
        driver = self.driver

        # Navigate to login
        driver.find_element(By.LINK_TEXT, 'Log In').click()

        # Fill form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        driver.find_element(By.NAME, 'username').send_keys('testuser')
        driver.find_element(By.NAME, 'password').send_keys('testpass123')
        driver.find_element(By.BUTTON_TAG_NAME, 'button').click()

        # Verify success
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'flash-success'))
        )
        assert 'Welcome' in driver.page_source

    def test_ajax_filtering(self):
        """Test AJAX category filtering."""
        driver = self.driver

        # Wait for listings to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'listing-card'))
        )

        # Select textbook category
        driver.find_element(By.ID, 'filter-textbooks').click()

        # Wait for AJAX update
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'category-badge'), 'Textbooks')
        )

        # Verify only textbooks shown
        listings = driver.find_elements(By.CLASS_NAME, 'listing-card')
        for listing in listings:
            assert 'Textbooks' in listing.text
```

## Required Test Coverage (per brief)

**Unit Tests (5+):**
1. Model validation (User.email format required)
2. Password hashing (generate_password_hash)
3. Route access control (protected routes)
4. CRUD operations (create, read, update, delete)
5. Form validation (CSRF token presence)

**Selenium Tests (5+):**
1. User registration journey
2. User login/logout journey
3. Create new listing journey
4. AJAX filter functionality
5. Edit own listing journey

---

*Testing analysis: 2026-03-25*
