# Phase 1: Flask Foundation & Authentication - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 01-flask-foundation-authentication
**Areas discussed:** Project Structure, Auth Page Integration, Session & Auth Flow, Registration Details, Forgot Password

---

## Project Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Single-package | app/ with routes.py, models.py, forms.py — straightforward for Flask course project | ✓ |
| Blueprint-based | App factory with blueprints — more modular, adds complexity | |

**User's choice:** Single-package
**Notes:** Matches the codebase maps already describing this pattern

### Static Files Migration

| Option | Description | Selected |
|--------|-------------|----------|
| Migrate into Flask | Move index.html, css/, js/, images/ into app/ structure | ✓ |
| Keep at root | Flask references root-level static files | |

**User's choice:** Migrate into Flask

### Tailwind CSS

| Option | Description | Selected |
|--------|-------------|----------|
| Tailwind CDN | No build step, matches current approach | ✓ |
| Tailwind build step | npm dependency, more control | |

**User's choice:** Tailwind CDN

### Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| .env file | python-dotenv with .env for secrets — standard Flask pattern | ✓ |
| Config classes | Development/production class hierarchy | |

**User's choice:** .env file

---

## Auth Page Integration

| Option | Description | Selected |
|--------|-------------|----------|
| Convert existing auth.html | Reuse tab-switching UI, convert to Jinja2 | ✓ |
| Separate pages from DESIGN.md | Build new login.html + register.html | |

**User's choice:** Convert existing

### OTP Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Separate OTP page | After registration, show verification page with OTP input | ✓ |
| Inline OTP on auth page | Replace signup form with OTP input on same page | |

**User's choice:** Separate OTP page

### Email Sending

| Option | Description | Selected |
|--------|-------------|----------|
| SMTP (Gmail/similar) | Flask-Mail with Gmail SMTP, requires app-specific password | ✓ |
| UWA SMTP | Use UWA student email SMTP if available | |
| Console-only for now | Print OTP to console, add real email in Phase 6 | |

**User's choice:** SMTP (Gmail/similar)

### OTP Expiry

| Option | Description | Selected |
|--------|-------------|----------|
| 5 minutes | Standard security practice | ✓ |
| 10 minutes | More forgiving for slow delivery | |

**User's choice:** 5 minutes

---

## Session & Auth Flow

### Session Duration

| Option | Description | Selected |
|--------|-------------|----------|
| 30 minutes inactivity | Standard for student marketplace | |
| Browser session only | Session lasts until browser closes | ✓ |

**User's choice:** Browser session only

### Post-Login Redirect

| Option | Description | Selected |
|--------|-------------|----------|
| Marketplace home | Redirect to main index page | ✓ |
| User dashboard | Redirect to profile/dashboard | |

**User's choice:** Marketplace home

### Post-Logout

| Option | Description | Selected |
|--------|-------------|----------|
| Redirect to login | Clear session, go to login page | ✓ |
| Redirect to landing page | Clear session, go to public index | |

**User's choice:** Redirect to login

### Unverified Users

| Option | Description | Selected |
|--------|-------------|----------|
| Block until verified | Unverified users see only verification page | ✓ |
| Browse-only access | Can browse but not create listings or message | |

**User's choice:** Block until verified

---

## Registration Details

### Form Fields

| Option | Description | Selected |
|--------|-------------|----------|
| Email + password only | Minimal fields | |
| Email + password + display name | More personal, adds slight friction | ✓ |
| Email + password + optional student ID | Includes student ID as originally spec'd | |

**User's choice:** Email + password + display name
**Notes:** User also specified email must match @student.uwa.edu.au pattern and OTP verification is required

### Password Rules

| Option | Description | Selected |
|--------|-------------|----------|
| 8+ chars with number | Standard balance of security and usability | ✓ |
| 8+ chars with uppercase+lowercase+number+special | Strong but may frustrate | |

**User's choice:** 8+ chars with number

### Duplicate Email

| Option | Description | Selected |
|--------|-------------|----------|
| Clear error message | "An account with this email already exists" | ✓ |
| Generic error | "Registration failed" without revealing if email exists | |

**User's choice:** Clear error message

### OTP Resend

| Option | Description | Selected |
|--------|-------------|----------|
| Resend with cooldown (60s) | Standard UX pattern | ✓ |
| No resend (re-register) | Simpler but poor UX | |

**User's choice:** Resend with cooldown

---

## Forgot Password

| Option | Description | Selected |
|--------|-------------|----------|
| OTP-based reset | Reuse OTP infrastructure from registration | |
| Reset link via email | Traditional email with unique reset link | ✓ |

**User's choice:** Reset link via email

---

## Claude's Discretion

- Exact OTP generation method (length, character set)
- Reset token implementation details
- Error message styling and flash message patterns
- Flask extension versions
- CSRF implementation details
- Database model field specifics

## Deferred Ideas

- "Remember me" (persistent sessions) — marked P2 in requirements, deferred to v2
- Password reset via email — added to THIS phase per user request
