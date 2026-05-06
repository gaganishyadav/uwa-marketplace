---
phase: 05-admin-account-and-authority
plan: 02
subsystem: routes
tags: [flask, decorator, admin, ban, featured, middleware]

# Dependency graph
requires:
  - phase: 05-admin-account-and-authority
    plan: 01
    provides: is_admin/ban_status on User, is_featured on Listing, seed-admin CLI
provides:
  - admin_required decorator blocking non-admins with 403
  - before_request hook intercepting banned users
  - 403 error handler with custom template
  - Admin action routes (delete listing, feature/unfeature, ban/unban/permanent-ban)
  - Featured-first sorting in gallery and search results
  - /banned landing page for banned users
affects: [05-03, 05-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [admin_required decorator following login_required pattern, before_request for ban enforcement, featured-first query splitting]

key-files:
  created: []
  modified:
    - app/routes.py

key-decisions:
  - "admin_required uses abort(403) instead of redirect to enforce route protection"
  - "before_request allows banned users to access only banned, logout, and static endpoints"
  - "Featured-first sorting uses three separate queries (featured, non-featured active, sold) concatenated"
  - "Admin ban routes guard against admin self-ban with flash message"

patterns-established:
  - "admin_required decorator pattern: same @wraps(f) as login_required but aborts 403"
  - "before_request ban check: whitelist approach (allow banned, logout, static only)"
  - "Admin action routes use request.referrer fallback for listing actions"

requirements-completed: [ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07, ADMIN-08]

# Metrics
duration: 2min
completed: 2026-05-06
---

# Phase 5 Plan 02: Admin Routes & Enforcement Summary

**Admin_required decorator, 6 admin action routes, before_request ban interception hook, 403 error handler, and featured-first gallery/search sorting**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-06T05:39:44Z
- **Completed:** 2026-05-06T05:41:47Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added admin_required decorator that aborts 403 for non-admin users (D-20, D-21)
- Added before_request hook that redirects banned users to /banned page, allowing only logout and static endpoints (D-16)
- Added 403 error handler rendering custom 403.html template
- Modified gallery route to query featured, non-featured active, and sold listings separately, concatenating in featured-first order (D-11)
- Modified search route to split active results into featured and non-featured before sold (D-11)
- Added admin routes: admin_user (GET), admin_delete_listing (POST), admin_feature_listing (POST), admin_ban_user (POST), admin_permanent_ban_user (POST), admin_unban_user (POST), banned (GET)
- All admin routes protected by @admin_required decorator; ban routes guard against admin self-ban (T-05-07)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add admin_required decorator + admin routes + ban check + 403 handler + featured sorting** - `90d9c0f` (feat)

## Files Created/Modified
- `app/routes.py` - Added admin_required decorator, before_request ban check, 403 error handler, featured-first gallery/search sorting, 7 admin/banned routes

## Decisions Made
- admin_required uses abort(403) for non-admins rather than redirect, matching REST semantics for unauthorized access
- before_request whitelist allows banned, logout, and static endpoints only -- banned users can still log out
- Featured-first sorting uses three separate queries rather than SQL ORDER BY CASE for clarity and SQLite compatibility
- Admin self-ban guard prevents accidental admin lockout via direct URL access (T-05-07 mitigation)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All admin backend routes functional and protected by admin_required decorator
- Ban interception hook active, redirecting banned users on every request
- Featured sorting in place for gallery and search
- Plan 03 can proceed: admin UI templates (403.html, banned.html, admin_user.html) and admin buttons on gallery cards
- Plan 04 can proceed: admin-specific tests

## Self-Check: PASSED

All referenced files exist. Task commit hash verified in git log.

---
*Phase: 05-admin-account-and-authority*
*Completed: 2026-05-06*
