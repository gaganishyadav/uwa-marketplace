# Phase 5: Admin Account & Authority - Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin users with elevated privileges can manage users and moderate marketplace listings. The admin browses the same gallery as regular users but sees extra controls on cards (delete, feature listings) and can navigate to a user detail page to ban/permanent-ban users. No separate admin dashboard page — admin controls are integrated into the existing gallery and listing detail views.

**Requirements covered:** Admin account with elevated privileges (is_admin flag), user management (view, ban/unban), listing management (delete, feature), admin-only route protection

</domain>

<decisions>
## Implementation Decisions

### Admin Dashboard & Navigation
- **D-01:** No separate admin dashboard page — admin browses the same gallery as regular users with extra controls overlaid on cards
- **D-02:** Admin accesses user management by clicking seller name on gallery cards or listing detail page → navigates to admin user detail page (`/admin/user/<id>`)
- **D-03:** No "Admin" link in the nav dropdown — admin navigates organically through the marketplace

### User Model & Admin Account
- **D-04:** Add `is_admin` boolean field to User model (default False)
- **D-05:** Single admin only — admin credentials (email + password) stored in `.env` file (e.g., `ADMIN_EMAIL`, `ADMIN_PASSWORD`)
- **D-06:** On app startup/seed, check if admin account exists; if not, create it from .env credentials with `is_admin=True`
- **D-07:** No ability to promote other users to admin — the .env-defined admin is the only admin

### Admin Controls on Gallery Cards
- **D-08:** Admin sees "Delete" and "Feature" buttons on each gallery card (same location where owners see Edit/Sold/Delete)
- **D-09:** "Delete" removes the listing immediately (same behavior as owner delete, no confirmation needed per admin authority)
- **D-10:** "Feature" toggles a listing as featured — featured listings appear at the top of the gallery with a "Featured" badge/ribbon on the card

### Featured Listings
- **D-11:** Featured listings sorted to the top of the gallery (before active listings)
- **D-12:** Featured badge is a small visual indicator (e.g., "Featured" tag/ribbon) on the card — style per DESIGN.md
- **D-13:** Feature is a toggle — admin can feature and unfeature any listing

### User Moderation (Admin User Detail Page)
- **D-14:** Admin user detail page (`/admin/user/<id>`) shows user info (name, email, join date, listing count) and moderation actions
- **D-15:** Two ban actions: "Ban" (temporary) and "Permanent Ban" — both store status on User model
- **D-16:** Banned users are completely blocked from the app — they see a "Your account has been suspended/banned" page when they log in, cannot access any marketplace features
- **D-17:** Admin can "Unban" from the same user detail page
- **D-18:** Banned user's existing listings remain visible in gallery with "Seller suspended" label — not auto-deleted
- **D-19:** Ban actions are silent — no notification to the affected user

### Route Protection
- **D-20:** `admin_required` decorator (same pattern as existing `login_required` and `email_verified_required`) protects all `/admin/*` routes
- **D-21:** Non-admin users accessing `/admin/*` URLs receive a **403 Forbidden** page

### Claude's Discretion
- User model ban status field implementation (single field with enum values: active/banned/permanent_ban)
- Featured listing query ordering (how to sort featured first efficiently)
- Admin user detail page layout and styling (follow DESIGN.md)
- 403 Forbidden page template design
- Banned user landing page template design
- Flash message wording for admin actions
- Whether featured badge styling uses existing badge patterns or new CSS

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design System
- `DESIGN.md` — Complete design system: color palette, typography, surface hierarchy, no-line rule, button styles, badge patterns, card structure

### Data Model & Requirements
- `.planning/REQUIREMENTS.md` — Full requirements with data model (User, Listing, Message)
- `.planning/ROADMAP.md` Phase 5 section — success criteria and requirements mapping

### Existing Integration Points
- `app/models.py` — User model (needs is_admin + ban status fields), Listing model (needs featured field)
- `app/routes.py` — Route patterns (init_routes, login_required, email_verified_required decorators)
- `app/templates/gallery.html` or listing card partial — Where admin buttons will be conditionally rendered
- `app/templates/_nav.html` — Nav structure (no admin link needed, but good reference)
- `app/templates/listing_detail.html` — Detail page where admin can also delete/feature and click seller name
- `app/__init__.py` — App factory where admin seeding logic could go

### Prior Phase Context
- `.planning/phases/01-flask-foundation-authentication/01-CONTEXT.md` — Auth patterns, decorator conventions, session handling
- `.planning/phases/02-marketplace-core/02-CONTEXT.md` — Gallery structure, card patterns, listing CRUD
- `.planning/phases/04-messaging-system/04-CONTEXT.md` — Route decorator patterns, integration conventions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Decorator pattern**: `login_required` and `email_verified_required` in routes.py — `admin_required` follows the same pattern
- **Gallery cards**: Existing card rendering in gallery/listing templates — admin buttons conditionally shown via `{% if user.is_admin %}`
- **Flash messages**: `flash('msg', 'success'|'error')` pattern for all action feedback
- **CSRF handling**: Every form includes `csrf_token()` hidden input — admin action forms must follow this
- **Context processor**: `inject_user` makes user available globally in templates — used for `user.is_admin` checks

### Established Patterns
- **No Blueprints**: All routes attached via `init_routes(app)` with `@app.route()` decorators
- **Naive UTC datetimes**: `_utcnow()` helper in models.py for SQLite compatibility
- **Template inheritance**: All pages extend `base.html`, use `{% block content %}`
- **jQuery for UI**: Modals, form handling via jQuery

### Integration Points
- `app/models.py`: Add `is_admin` (Boolean) and `ban_status` (String: active/banned/permanent_ban) to User model; add `is_featured` (Boolean) to Listing model
- `app/routes.py`: Add `admin_required` decorator + admin routes (`/admin/user/<id>`, `/admin/delete-listing/<id>`, `/admin/feature-listing/<id>`, `/admin/ban-user/<id>`, `/admin/unban-user/<id>`)
- Gallery template: Add conditional admin buttons on cards
- Listing detail template: Add conditional admin buttons
- `app/__init__.py` or a seed CLI: Create admin account from .env on first run

</code_context>

<specifics>
## Specific Ideas

- Admin browses the same gallery — no separate admin UI, controls are overlaid on existing views
- Seller name on cards is clickable for admin → goes to user detail page with ban controls
- Featured listings get a badge and sort to top of gallery
- Banned user's listings stay visible with "Seller suspended" label
- Admin credentials from .env — single admin only, no multi-admin
- 403 page for unauthorized admin route access

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-admin-account-and-authority*
*Context gathered: 2026-05-05*
