# External Integrations

**Analysis Date:** 2026-03-25

## APIs & External Services

**Mapping:**
- Leaflet.js - Interactive campus map for meetup spot selection
  - SDK/Client: Leaflet.js JavaScript library
  - Purpose: Allow sellers to drop pins on UWA campus map (Reid Library, Guild Village, etc.)
  - Auth: None required (open-source library)
  - Location: Frontend integration via jQuery

**Third-Party APIs:**
- None specified in brief
- No external API keys currently required

## Data Storage

**Databases:**
- SQLite (file-based)
  - Connection: Local file storage (location to be determined)
  - Client: Flask-SQLAlchemy ORM
  - Schema (from brief):
    - User Table: id, username, email, password_hash
    - Listing Table: id, title, description, price, category, timestamp, latitude, longitude, user_id (FK)

**File Storage:**
- Local filesystem only
  - Static assets: `/Users/sawetr/Documents/uwa-marketplace/app/static/` (planned)
  - User uploads: Not specified in brief
  - Images: Not yet implemented

**Caching:**
- None specified

## Authentication & Identity

**Auth Provider:**
- Custom implementation
  - Password hashing: werkzeug.security (salted hashes)
  - Session management: Flask sessions
  - CSRF protection: Flask-WTF tokens
  - User model: Custom SQLAlchemy model

**Third-Party Auth:**
- None - UWA students only, standalone authentication

## Monitoring & Observability

**Error Tracking:**
- None specified

**Logs:**
- Approach: Not specified in brief
- Likely: Flask built-in logging or Python standard library logging

## CI/CD & Deployment

**Hosting:**
- Not specified in brief
- Development: Werkzeug development server
- Production: Not determined (likely traditional Python hosting)

**CI Pipeline:**
- None specified

## Environment Configuration

**Required env vars (from brief):**
- `SECRET_KEY` - Flask session encryption
- `FLASK_ENV` - Environment mode (development/production)
- `DATABASE_URL` - SQLite database path (optional, Flask-SQLAlchemy default)

**Secrets location:**
- `.env` file (not yet created)
- Accessed via python-dotenv
- Excluded from Git (specified in brief)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## External Dependencies

**CDN Assets (current landing page):**
- Google Fonts - Inter and Manrope typefaces
  - Loaded via: `<link>` tags in `/Users/sawetr/Documents/uwa-marketplace/index.html`
  - Purpose: Typography system

**Planned Dependencies:**
- jQuery - via CDN or local static file
- Leaflet.js - via CDN or local static file
- Tailwind CSS - via CDN or build process (brief mentions, but current implementation uses custom CSS)

---

*Integration audit: 2026-03-25*
