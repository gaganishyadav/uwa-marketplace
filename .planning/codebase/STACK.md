# Technology Stack

**Analysis Date:** 2026-03-25

## Languages

**Primary:**
- Python 3.x - Backend application logic per `/Users/sawetr/Documents/uwa-marketplace/brief.md`

**Secondary:**
- HTML5 - Frontend markup (landing page at `/Users/sawetr/Documents/uwa-marketplace/index.html`)
- CSS3 - Frontend styling (custom design system at `/Users/sawetr/Documents/uwa-marketplace/css/styles.css`)
- JavaScript (jQuery) - Frontend interactivity and AJAX (specified in brief)

## Runtime

**Environment:**
- Python 3.x

**Package Manager:**
- pip (Python)
- Lockfile: `requirements.txt` - specified in brief but not yet created

## Frameworks

**Core:**
- Flask - Web framework for backend routing and application logic
- Jinja2 - Server-side templating for dynamic page generation

**Testing:**
- Not yet implemented - brief specifies 5+ unit tests and 5+ Selenium tests

**Build/Dev:**
- Not applicable - pure Python/HTML/CSS stack with no build pipeline

## Key Dependencies

**Critical (specified in brief):**
- Flask - Web framework
- Flask-SQLAlchemy - ORM for database management
- Flask-WTF - CSRF protection and form handling
- python-dotenv - Environment variable management
- werkzeug.security - Password hashing with salt

**Infrastructure (specified in brief):**
- SQLite - Database (via Flask-SQLAlchemy)
- Tailwind CSS - CSS utility framework (Note: Current landing page uses custom CSS at `/Users/sawetr/Documents/uwa-marketplace/css/styles.css`)

**Frontend Libraries (specified in brief):**
- jQuery - DOM manipulation and AJAX
- Leaflet.js - Interactive mapping for campus meetup locations

## Configuration

**Environment:**
- `.env` file - Environment variables (not yet created, specified in brief)
- Required: SECRET_KEY for Flask session management, API keys if needed

**Build:**
- No build configuration - static files served directly
- Planned structure: `/Users/sawetr/Documents/uwa-marketplace/app/static/` for CSS/JS/assets

## Platform Requirements

**Development:**
- Python 3.x runtime
- pip for dependency management
- Web browser for frontend testing

**Production:**
- Not specified - likely traditional hosting (Werkzeug dev server for development, Gunicorn/uWSGI for production)

---

*Stack analysis: 2026-03-25*
