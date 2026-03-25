# Codebase Concerns

**Analysis Date:** 2026-03-25

## Missing Critical Features

**Backend Application:**
- Problem: Flask application not yet implemented - only landing page exists
- Files: `app/__init__.py`, `app/routes.py`, `app/models.py`, `run.py` (all missing)
- Blocks: All functionality including authentication, listings, CRUD operations, database integration
- Impact: Project is at Checkpoint 1 level only; Checkpoints 2 and 3 requirements unimplemented
- Fix approach: Implement Flask app factory pattern, SQLAlchemy models, and route handlers per specification

**Authentication System:**
- Problem: No user registration, login, logout, or session management
- Files: Not yet created
- Blocks: User-specific features (CRUD on own listings, session persistence)
- Impact: Security requirement for salted password hashes not yet addressed
- Fix approach: Implement using werkzeug.security for password hashing, Flask-Login for sessions

**Database Integration:**
- Problem: SQLite database via Flask-SQLAlchemy not configured
- Files: `app/models.py` (missing)
- Blocks: Listing persistence, user data storage, all CRUD operations
- Impact: No data persistence layer exists
- Fix approach: Create User and Listing models with proper relationships and migrations

## Tech Debt

**Static Landing Page Links:**
- Issue: Footer links are placeholder `href="#"` with no actual pages
- Files: `/Users/sawetr/Documents/uwa-marketplace/index.html` (lines 192-194)
- Impact: Terms of Service, Privacy Policy, Contact pages referenced but non-existent
- Fix approach: Create these pages or remove links until implemented

**Missing .gitignore:**
- Issue: No .gitignore file to exclude sensitive files from version control
- Files: Project root
- Impact: Risk of accidentally committing .env, database files, cache
- Fix approach: Create .gitignore with .env, .db, __pycache__, .pyc, *.pyc

**Minimal README:**
- Issue: README.md contains only project name
- Files: `/Users/sawetr/Documents/uwa-marketplace/README.md` (1 line)
- Impact: No setup instructions, dependencies, or documentation for contributors
- Fix approach: Add installation, setup, usage, and project structure documentation

## Security Considerations

**No .env File Created:**
- Risk: Secret keys and sensitive configuration will be needed but no secure storage established
- Files: `.env` (missing, per specification should be created)
- Current mitigation: None - this is an early-stage project
- Recommendations: Create .env file with SECRET_KEY placeholder, add to .gitignore immediately, use python-dotenv for loading

**CSRF Protection Not Implemented:**
- Risk: All form submissions will be vulnerable to CSRF attacks
- Files: All future route handlers
- Current mitigation: None - Flask-WTF with CSRF tokens not yet integrated
- Recommendations: Implement Flask-WTF CSRF protection on all POST/PUT/DELETE routes per specification

**UWA Email Verification:**
- Risk: No mechanism to verify users are actual UWA students
- Files: Future registration system
- Current mitigation: None specified in requirements
- Recommendations: Consider @uwa.edu.au email domain validation during registration

**Meetup Location Safety:**
- Risk: User-designated pins could be placed in unsafe campus locations
- Files: Future Leaflet.js integration
- Current mitigation: Specification mentions "safe meeting locations" but no enforcement
- Recommendations: Pre-define approved meetup spots (Reid Library, Guild Village, etc.) rather than free-form pin placement

## Performance Bottlenecks

**AJAX Filtering Not Implemented:**
- Problem: Real-time search and category filtering specified but not built
- Files: All listing view pages
- Cause: Frontend jQuery/AJAX layer not yet developed
- Improvement path: Implement server-side filter endpoints with jQuery AJAX calls to prevent full page reloads per specification

**No Image Upload Strategy:**
- Problem: Listing images not addressed in specification
- Files: Future listing creation forms
- Cause: Brief does not specify image handling approach
- Improvement path: Decide between: (1) external CDN (Cloudinary/S3), (2) local filesystem storage with serving, or (3) no images (text-only listings)

**SQLite Scaling:**
- Problem: Single SQLite file limits concurrent writes
- Files: Future database layer
- Cause: SQLite chosen per unit constraints
- Improvement path: For student project scale this is acceptable, but consider connection pooling and write limits

## Fragile Areas

**Leaflet.js Integration:**
- Files: Future map components
- Why fragile: External JavaScript library dependency not yet integrated; UWA campus coordinate data not sourced
- Safe modification: Test map rendering with default coordinates before adding pin-drop functionality
- Test coverage: No tests exist yet - Selenium tests should cover map interaction per specification

**Session Persistence:**
- Files: Future authentication system
- Why fragile: Browser restart session persistence requires careful cookie configuration
- Safe modification: Use Flask-Login with remember=True option and secure cookie settings
- Test coverage: Selenium tests should verify session survival across browser restarts per specification

**CRUD Authorization:**
- Files: Future route handlers for listing update/delete
- Why fragile: Must ensure users can only modify their own listings, not others'
- Safe modification: Add @login_required decorator and check listing.user_id == current_user.id before modifications
- Test coverage: Unit tests should verify authorization checks prevent cross-user modifications

## Scaling Limits

**SQLite Write Concurrency:**
- Current capacity: Single write operation at a time
- Limit: Under heavy concurrent listing creation, writes will queue and potentially timeout
- Scaling path: Acceptable for student project scale; would need PostgreSQL/MySQL for production

**No CDN for Static Assets:**
- Current capacity: All static files served by Flask development server
- Limit: No geographic distribution, no caching headers optimized
- Scaling path: Not applicable for student project; production would use nginx + CDN

## Dependencies at Risk

**Forbidden Framework Compliance:**
- Risk: Accidentally introducing React, Vue, Angular, SASS, or MySQL (forbidden per unit requirements)
- Impact: Project may fail unit requirements if forbidden technologies used
- Migration plan: Stick to specified stack: Flask + SQLite + Tailwind + jQuery; lint for forbidden imports

**Leaflet.js CDN:**
- Risk: External JavaScript dependency loaded from CDN
- Impact: Map functionality breaks if CDN is unavailable or changes API
- Migration plan: No migration needed - consider hosting Leaflet locally if CDN reliability becomes concern

## Test Coverage Gaps

**No Unit Tests:**
- What's not tested: Model validation, password hashing, route access control, CRUD authorization
- Files: `tests/test_unit.py` (missing)
- Risk: Backend bugs will go undetected; security vulnerabilities may ship to production
- Priority: High - specification requires 5+ unit tests for CITS3403/CITS5505

**No Selenium Tests:**
- What's not tested: User journey, login flow, item posting, AJAX search functionality
- Files: `tests/test_selenium.py` (missing)
- Risk: Frontend regressions, broken user flows, critical UX issues
- Priority: High - specification requires 5+ Selenium tests

**No Test Database Configuration:**
- What's not tested: All database operations currently untestable
- Files: Test configuration files
- Risk: Tests will interfere with development database or require manual setup
- Priority: Medium - configure separate test database SQLite file

## Known Bugs

**None Identified:**
- Early-stage project with minimal implemented functionality
- Bugs expected to emerge during Flask backend implementation

---

*Concerns audit: 2026-03-25*
