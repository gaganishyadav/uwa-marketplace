# Codebase Structure

**Analysis Date:** 2026-03-25

## Directory Layout

```
uwa-marketplace/
├── app/                    # Flask application package (planned)
│   ├── static/             # Client-side assets (CSS, JS, images)
│   ├── templates/          # Jinja2 templates
│   ├── models.py           # SQLAlchemy database models
│   ├── routes.py           # Flask route handlers
│   └── __init__.py         # App factory and configuration
├── tests/                  # Test suite (planned)
│   ├── test_unit.py        # Backend unit tests
│   └── test_selenium.py    # Frontend integration tests
├── css/                    # Landing page styles (current)
│   └── styles.css          # Design system CSS
├── .planning/              # Project planning documents
│   └── codebase/           # Codebase analysis documents
├── brief.md                # Project specification
├── index.html              # Static landing page (current)
├── README.md               # Project overview
├── requirements.txt        # Python dependencies (planned)
├── run.py                  # Application entry point (planned)
└── .env                    # Environment configuration (planned, gitignored)
```

## Directory Purposes

**app/:**
- Purpose: Flask application package containing all backend logic
- Contains: Python modules for models, routes, configuration, and app factory
- Key files: `__init__.py` (app factory), `models.py` (ORM models), `routes.py` (request handlers)

**app/static/:**
- Purpose: Static assets served directly to clients
- Contains: CSS files, JavaScript files, images, fonts
- Key files: Tailwind CSS builds, custom JS, Leaflet.js integration code

**app/templates/:**
- Purpose: Jinja2 HTML templates for server-side rendering
- Contains: Base layout template, page templates, component partials
- Key files: `base.html` (layout skeleton), `index.html` (homepage), `login.html`, `listing.html`

**tests/:**
- Purpose: Automated test suite covering unit and integration tests
- Contains: Python test files using pytest/unittest and Selenium
- Key files: `test_unit.py` (model/route tests), `test_selenium.py` (browser automation)

**css/:**
- Purpose: Landing page stylesheets (transitional, will move to app/static/)
- Contains: Design system CSS with custom properties and component styles
- Key files: `styles.css` (560 lines, complete design system)

**.planning/codebase/:**
- Purpose: Codebase analysis documents for GSD workflow
- Contains: Architecture, structure, conventions, testing patterns
- Generated: Yes (by GSD mapping commands)

## Key File Locations

**Entry Points:**
- `run.py`: Application entry point (planned) - starts Flask development server
- `index.html`: Current static landing page at root - will become `app/templates/index.html`

**Configuration:**
- `app/__init__.py`: Flask app factory - configures extensions, database, secret keys
- `.env`: Environment variables (SECRET_KEY, DATABASE_URL) - excluded from git
- `requirements.txt`: Python dependencies (Flask, Flask-SQLAlchemy, Flask-WTF, python-dotenv)

**Core Logic:**
- `app/models.py`: Database models (User, Listing) with SQLAlchemy ORM
- `app/routes.py`: All HTTP route handlers and business logic

**Testing:**
- `tests/test_unit.py`: Unit tests for models and routes
- `tests/test_selenium.py`: E2E tests for user flows

**Documentation:**
- `brief.md`: Complete project specification with requirements
- `README.md`: Project overview and setup instructions

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `routes.py`, `models.py`)
- Templates: `snake_case.html` (e.g., `base.html`, `login.html`)
- Test files: `test_*.py` prefix (e.g., `test_unit.py`)
- CSS: `kebab-case.css` or `snake_case.css` (e.g., `styles.css`)

**Directories:**
- All lowercase: `app/`, `static/`, `templates/`, `tests/`
- Plural for collections: `templates/`, `tests/`

**Python:**
- Classes: `PascalCase` (e.g., `User`, `Listing`)
- Functions: `snake_case` (e.g., `get_listing`, `create_user`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `SECRET_KEY`)

## Where to Add New Code

**New Feature (Backend):**
- Route handler: `app/routes.py` - add new `@app.route()` decorated function
- Model changes: `app/models.py` - add/modify SQLAlchemy class
- Templates: `app/templates/` - create new `.html` file extending `base.html`

**New Feature (Frontend):**
- Page template: `app/templates/[feature].html`
- JavaScript: `app/static/js/[feature].js`
- CSS: Use Tailwind utility classes or add to `app/static/css/custom.css`

**Database Migration:**
- Schema changes: `app/models.py`
- Migration script: Create in project root or use Flask-Migrate (if added)

**New Test:**
- Unit test: `tests/test_unit.py` - add test class or function
- Selenium test: `tests/test_selenium.py` - add test class for user flow

**Utilities:**
- Shared helpers: `app/utils.py` (create new file for utility functions)
- Common forms: `app/forms.py` (create new file for Flask-WTF form classes)

## Special Directories

**app/static/:**
- Purpose: Static assets served at `/static/` URL path
- Generated: No (manual commits)
- Committed: Yes

**app/templates/:**
- Purpose: Jinja2 templates for server-side rendering
- Generated: No
- Committed: Yes

**tests/:**
- Purpose: Automated test suite
- Generated: No
- Committed: Yes

**.planning/:**
- Purpose: GSD workflow planning documents
- Generated: Yes (by GSD commands)
- Committed: Yes (tracks project evolution)

**.env:**
- Purpose: Environment configuration and secrets
- Generated: No (manual setup)
- Committed: No (in .gitignore)

---

*Structure analysis: 2026-03-25*
