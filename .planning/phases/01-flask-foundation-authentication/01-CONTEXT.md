# Phase 1: Flask Foundation & Authentication - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the Flask application foundation and implement complete user authentication: registration (with UWA student email verification via OTP), login, logout, forgot password (email reset link), and session management. This includes migrating existing static files into the Flask app structure and connecting the existing auth.html UI to real backend logic.

**Requirements covered:** AUTH-01 (registration), AUTH-02 (login with session), AUTH-04 (logout), SEC-06 (session security)
**Additional scope (user-specified):** OTP email verification on registration, forgot password with email reset link

</domain>

<decisions>
## Implementation Decisions

### Project Structure
- **D-01:** Single `app/` package with `routes.py`, `models.py`, `forms.py`, `templates/`, `static/` — no blueprints
- **D-02:** Migrate existing root static files (`index.html`, `css/`, `js/`, `images/`) into Flask's `app/templates/` and `app/static/` structure
- **D-03:** Tailwind CSS via CDN (no build step) — matches current landing page approach
- **D-04:** Configuration via `.env` file with python-dotenv (SECRET_KEY, DATABASE_PATH, MAIL settings)

### Auth Page Integration
- **D-05:** Convert existing `auth.html` tab-switching login/signup UI into Jinja2 templates — reuse the layout, don't rebuild
- **D-06:** OTP verification on a **separate page** (not inline) after registration
- **D-07:** Email sending via **SMTP** (Gmail or similar) using Flask-Mail
- **D-08:** OTP valid for **5 minutes**, with a **resend button** (60-second cooldown)

### Registration
- **D-09:** Registration fields: **email + password + display name** (email must match `@student.uwa.edu.au`)
- **D-10:** Password rules: minimum 8 characters, must include at least one number and one letter
- **D-11:** Duplicate email registration shows clear error: "An account with this email already exists"
- **D-12:** After registration, user is **blocked from accessing marketplace** until OTP is verified — they see a verification page with resend option

### Session & Auth Flow
- **D-13:** Sessions last **until browser is closed** (no timed session — uses Flask's default session behavior with PERMANENT_SESSION_LIFETIME set to browser session)
- **D-14:** After login, redirect to **marketplace home page**
- **D-15:** After logout, redirect to **login page**
- **D-16:** Unverified users (registered but no OTP) can log in but see only the "verify your email" page — cannot access marketplace

### Forgot Password
- **D-17:** Forgot password flow: user enters email → receives email with unique reset link → clicks link → sets new password
- **D-18:** Reset link should expire (standard practice, similar to OTP — researcher/planner to decide exact duration)

### Claude's Discretion
- Exact OTP generation method (length, character set)
- Reset token implementation details (token format, storage approach)
- Error message styling and flash message patterns
- Flask extension versions and dependency versions
- CSRF implementation details (Flask-WTF setup)
- Database model field specifics (exact column types, lengths)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design System
- `DESIGN.md` — Complete design system with color palette, typography (Inter + Manrope), surface hierarchy, component patterns, "No-Line" rule, button styles, input field styles, elevation principles

### Existing UI (to be converted)
- `auth.html` — Current static auth page with tab-switching login/signup, form fields, and layout
- `js/auth.js` — jQuery form handling with tab switching and validation stubs
- `css/styles.css` — Design system CSS (560 lines) with custom properties and component styles
- `images/winthrop-hall.jpg` — Campus background image for auth page

### Project Specifications
- `.planning/REQUIREMENTS.md` — Full requirements with data model, categories, traceability
- `.planning/codebase/ARCHITECTURE.md` — Planned Flask MVC architecture, data flow, entry points
- `.planning/codebase/STRUCTURE.md` — Planned directory layout with naming conventions

### Landing Page (to be migrated)
- `index.html` — Static landing page with navigation, hero, features, categories, CTA, footer

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `auth.html`: Complete login/signup tab UI with form fields, styling, and responsive layout — can be converted to Jinja2 with minimal structural changes
- `js/auth.js`: jQuery tab-switching and form validation logic — the tab switching can remain; the TODO stubs (`// TODO: Replace with actual AJAX`) need to be replaced with real form submissions to Flask routes
- `css/styles.css`: Full design system CSS with variables matching DESIGN.md — can be served directly from `app/static/`
- `index.html`: Complete landing page — needs migration to `app/templates/`

### Established Patterns
- Tab-switching auth pattern already built (login/signup on one page via jQuery)
- Material Symbols Outlined icons already loaded
- Google Fonts (Inter + Manrope) already configured
- Design system CSS variables defined in `styles.css`

### Integration Points
- Forms in `auth.html` will need `action` attributes pointing to Flask routes and CSRF tokens added
- jQuery form handlers in `auth.js` need to POST to Flask endpoints instead of console.log
- Static file references (`css/styles.css`, `images/`) need to use Flask `url_for('static', ...)`
- Auth pages need to extend a Flask `base.html` template

</code_context>

<specifics>
## Specific Ideas

- UWA student email pattern: `@student.uwa.edu.au` — must validate on registration
- OTP verification is a hard requirement, not optional — accounts are non-functional until verified
- The "Scholarly Curator" design aesthetic from DESIGN.md must be maintained in all new/converted pages
- Winthrop Hall campus photo (`images/winthrop-hall.jpg`) used as auth page background — keep this

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-flask-foundation-authentication*
*Context gathered: 2026-04-03*
