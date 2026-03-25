# Architecture

**Analysis Date:** 2026-03-25

## Pattern Overview

**Overall:** Traditional MVC (Model-View-Controller) with Flask web framework

**Key Characteristics:**
- Server-side rendered pages using Jinja2 templates
- SQLAlchemy ORM for database abstraction
- jQuery for client-side interactivity and AJAX requests
- Session-based authentication with secure password hashing
- Leaflet.js integration for location-based features

## Layers

**Presentation Layer (Templates):**
- Purpose: Render HTML pages with dynamic data using Jinja2 templating
- Location: `app/templates/`
- Contains: Base templates, page templates, partials
- Depends on: Flask context, route handlers pass data to templates
- Used by: User's browser (client-side)

**Business Logic Layer (Routes):**
- Purpose: Handle HTTP requests, process business logic, interact with models
- Location: `app/routes.py`
- Contains: Route handlers, form validation, authentication checks
- Depends on: Models, Flask session, request/response objects
- Used by: Flask application router

**Data Layer (Models):**
- Purpose: Define database schema and provide ORM interface
- Location: `app/models.py`
- Contains: SQLAlchemy model classes (User, Listing)
- Depends on: Flask-SQLAlchemy, SQLite database
- Used by: Route handlers for CRUD operations

**Static Assets Layer:**
- Purpose: Client-side styling and interactivity
- Location: `app/static/`
- Contains: CSS, JavaScript files, images
- Depends on: External CDN resources (Google Fonts, Leaflet.js, jQuery, Tailwind CSS)
- Used by: Browser via template includes

## Data Flow

**Request Lifecycle:**

1. Browser sends HTTP request to Flask application
2. Flask router matches URL pattern to route handler in `app/routes.py`
3. Route handler validates authentication (if required) via session
4. Route handler queries/updates database via SQLAlchemy models in `app/models.py`
5. Route handler renders Jinja2 template with context data
6. Template extends `base.html` and includes static assets
7. HTML response sent to browser
8. jQuery may trigger AJAX requests for filtered content (search, categories)

**Authentication Flow:**

1. User submits login form to `/login` route
2. Route handler verifies credentials against User model
3. On success, session cookie set with user ID
4. Subsequent requests check session for authenticated user
5. Logout clears session data

**State Management:**
- Server-side: SQLite database via SQLAlchemy ORM
- Client-side: Flask sessions (cookies) for authentication state
- No client-side state management library (React/Vue not used)

## Key Abstractions

**User Model:**
- Purpose: Represents authenticated users of the marketplace
- Examples: `app/models.py` (User class)
- Pattern: ActiveRecord-style ORM with Flask-SQLAlchemy
- Fields: id, username, email, password_hash

**Listing Model:**
- Purpose: Represents items for sale in the marketplace
- Examples: `app/models.py` (Listing class)
- Pattern: ActiveRecord-style ORM with foreign key to User
- Fields: id, title, description, price, category, timestamp, latitude, longitude, user_id

**Route Handlers:**
- Purpose: Encapsulate request/response logic for specific endpoints
- Examples: `app/routes.py` (decorated functions with @app.route)
- Pattern: Function-based views with Flask decorators
- Return: HTML responses (redirect or render_template)

## Entry Points

**Application Entry Point:**
- Location: `run.py` (to be created)
- Triggers: Direct Python execution or WSGI server
- Responsibilities: Initialize Flask app, run development server

**Application Factory:**
- Location: `app/__init__.py`
- Triggers: Import by run.py or test suite
- Responsibilities: Configure Flask, initialize extensions (DB, CSRF), register routes

**Landing Page:**
- Location: `index.html` (current static) → `app/templates/index.html` (planned)
- Triggers: Root URL (/)
- Responsibilities: Display marketplace homepage with navigation, hero, features, categories

## Error Handling

**Strategy:** Flask built-in error handlers with custom error pages

**Patterns:**
- HTTP exceptions (404, 500) rendered via custom error templates
- Form validation errors displayed via Flask-WTF
- Database errors caught and logged, user-friendly messages shown
- CSRF protection via Flask-WTF tokens on all POST requests

## Cross-Cutting Concerns

**Authentication:** Flask session-based with `@login_required` decorator pattern on protected routes

**Validation:** Flask-WTF forms for server-side validation, HTML5 attributes for client-side

**Security:** werkzeug.security for password hashing, CSRF tokens on all mutations, .env for secrets

**Logging:** Python logging module (to be implemented)

**Testing:** Unit tests for models/routes, Selenium tests for user flows

---

*Architecture analysis: 2026-03-25*
