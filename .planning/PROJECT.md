# UWA Campus Swap-Meet

## What This Is

A hyper-local, student-centric marketplace web application for the University of Western Australia community. Students can buy, sell, and swap academic materials (textbooks), furniture, electronics, and campus essentials with fellow students, using safe campus locations for meetups.

## Core Value

Enable UWA students to trade goods securely within the campus community — safe meetups, student-only access, and zero platform fees.

## Requirements

### Validated

- ✓ Landing page with navigation, hero section, features, categories, CTA, and footer — existing (Phase 0)

### Active

- [ ] User accounts with secure registration, login, logout, and session persistence
- [ ] Public marketplace gallery with grid-based view of all active listings
- [ ] Real-time AJAX search and category filtering (no page reloads)
- [ ] Listing CRUD operations (create, read, update, delete with ownership)
- [ ] Interactive Leaflet.js map of UWA campus with meetup spot selection
- [ ] Secure messaging between buyers and sellers
- [ ] Salted password hashing and CSRF protection
- [ ] Unit tests (5+) for models, password hashing, and route access control
- [ ] Selenium tests (5+) for user journeys including login, posting, and AJAX search

### Out of Scope

- Payment processing through the platform — Students arrange payment directly during meetups
- Shipping/delivery options — Campus-only, in-person transactions
- Mobile apps (iOS/Android) — Web-only for CITS3403/CITS5505 requirements
- Real-time chat (WebSocket) — Async messaging sufficient for v1
- User ratings/reputation system — Deferred to post-course delivery
- Image hosting/cloud storage — Local file storage acceptable for MVP

## Context

**Academic Project**: Built for CITS3403/CITS5505 Agile Web Development course at UWA. Three checkpoint milestones demonstrate iterative delivery of core functionality.

**Target Users**: UWA students who need affordable textbooks and furniture, or want to sell items they no longer need. The hyper-local focus (campus-only) enables safe, convenient meetups at trusted locations like Reid Library and Guild Village.

**Existing Work**: Static landing page already implemented with modern CSS (Inter + Manrope fonts, glassmorphism effects, gradients). This provides the visual foundation for the dynamic application.

## Constraints

- **Tech Stack**: Flask (Python 3.x), SQLite via Flask-SQLAlchemy, HTML5/CSS/Tailwind/jQuery, Jinja2 templating — Course requirement
- **Forbidden Technologies**: React, Angular, Vue, SASS, MySQL — Not allowed per course specs
- **Security**: Passwords must use salted hashes (werkzeug.security), CSRF tokens (Flask-WTF), secrets in .env (python-dotenv)
- **Testing Requirements**: Minimum 5 unit tests + 5 Selenium tests
- **Deployment**: Must run on standard Python environment, no external cloud services required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flask over Django | Lightweight framework sufficient for course scope, easier to demonstrate ORM patterns | — Pending |
| SQLite over PostgreSQL | File-based database simplifies setup for course submission and local development | — Pending |
| Tailwind CSS | Rapid UI development with utility classes; forbidden from using SASS so Tailwind fills the gap | — Pending |
| Leaflet.js for mapping | Free, lightweight library sufficient for campus map with pinned meetup spots | — Pending |
| Campus-only transactions | Hyper-local focus enables safe meetups, avoids shipping complexity, aligns with student community | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2025-03-25 after initialization*
