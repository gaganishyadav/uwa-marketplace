---
phase: 05-admin-account-and-authority
plan: 03
subsystem: templates
tags: [jinja2, css, admin, ban, featured, badge, ui]

# Dependency graph
requires:
  - phase: 05-admin-account-and-authority
    plan: 02
    provides: admin_required decorator, admin routes (delete/feature/ban/unban), before_request ban hook, 403 handler, featured sorting
provides:
  - Updated listing_card macro with is_admin parameter, featured badge, seller suspended label, admin action buttons
  - Gallery and search results passing is_admin to card macro
  - Listing detail page with clickable seller name for admin and admin action buttons
  - admin_user.html template for user moderation page
  - banned.html template for suspended user landing page
  - 403.html template for forbidden access page
  - CSS styles for featured badge, admin buttons, seller suspended labels, admin user detail page
affects: [05-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [is_admin parameter propagation from gallery/search to card macro, admin action forms with csrf_token in templates]

key-files:
  created:
    - app/templates/admin_user.html
    - app/templates/banned.html
    - app/templates/403.html
  modified:
    - app/templates/_listing_card.html
    - app/templates/gallery.html
    - app/templates/_search_results.html
    - app/templates/listing_detail.html
    - app/static/css/styles.css

key-decisions:
  - "Featured badge positioned on left of card image (right:auto;left:var(--space-sm)) to coexist with status badge on right"
  - "Admin action buttons on cards use same btn-ad-action style as owner actions for visual consistency"
  - "btn-tertiary class added to CSS per DESIGN.md ghost button pattern (no background, primary text, gold underline on hover)"
  - "Admin user detail page uses ghost border fallback (outline-variant) for sectioning -- acceptable per DESIGN.md section 4 for detail pages"

patterns-established:
  - "is_admin propagation: gallery/search pass (user.is_admin if user else false) to card macro"
  - "Admin action forms: each button in own form with csrf_token, consistent with existing card action pattern"

requirements-completed: [ADMIN-02, ADMIN-03, ADMIN-06, ADMIN-07, ADMIN-08]

# Metrics
duration: 3min
completed: 2026-05-06
---

# Phase 5 Plan 03: Admin UI Templates Summary

**Admin controls on gallery/search/detail cards, featured badge, seller suspended label, plus admin_user/banned/403 page templates with CSS**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-06T05:44:59Z
- **Completed:** 2026-05-06T05:48:37Z
- **Tasks:** 2
- **Files modified:** 5, created: 3

## Accomplishments
- Added is_admin parameter to listing_card macro with conditional admin Delete/Feature buttons
- Added Featured badge (left-positioned) and Seller suspended label on listing cards
- Updated gallery and search results to pass is_admin to card macro
- Made seller name on listing detail page clickable for admin users, linking to admin_user route
- Created admin_user.html with user info display, ban status badge, and moderation action forms
- Created banned.html with suspension message and logout button
- Created 403.html with access denied message and gallery link
- Added CSS for featured badge, admin card footer, seller suspended labels, and admin user detail page
- Added btn-tertiary ghost button style per DESIGN.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Update listing card macro + gallery + search + detail templates** - `d24aa45` (feat)
2. **Task 2: Create admin_user, banned, 403 templates + CSS styles** - `0ddb2da` (feat)

## Files Created/Modified
- `app/templates/_listing_card.html` - Added is_admin parameter, featured badge, seller suspended label, admin action buttons
- `app/templates/gallery.html` - Passes is_admin to listing_card macro
- `app/templates/_search_results.html` - Passes is_admin to listing_card macro
- `app/templates/listing_detail.html` - Clickable seller name for admin, admin action buttons, seller suspended label
- `app/templates/admin_user.html` - New: admin user detail page with ban controls
- `app/templates/banned.html` - New: suspended user landing page
- `app/templates/403.html` - New: forbidden access error page
- `app/static/css/styles.css` - Added btn-tertiary, status-featured, admin card footer, seller suspended, admin user detail styles

## Decisions Made
- Featured badge uses left positioning to coexist with status badge on the right side of card images
- Admin action buttons on cards follow existing btn-ad-action pattern for visual consistency with owner actions
- Admin user detail page uses ghost border fallback (outline-variant) for sectioning dividers, acceptable per DESIGN.md section 4 for detail pages (not listing cards)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added btn-tertiary CSS class**
- **Found during:** Task 2 (admin_user.html creation)
- **Issue:** admin_user.html uses btn-tertiary class for "Back to Gallery" link but the class was not defined in styles.css
- **Fix:** Added .btn-tertiary CSS following DESIGN.md ghost button pattern (transparent background, primary text, gold underline on hover)
- **Files modified:** app/static/css/styles.css
- **Verification:** grep confirms btn-tertiary class defined in CSS
- **Committed in:** 0ddb2da (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Auto-fix necessary for correct rendering. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All admin UI templates complete and rendering correctly
- Admin controls visible on gallery cards, search results, and listing detail page
- Admin user moderation page functional with ban/unban actions
- Banned and 403 error pages ready
- Plan 04 can proceed: admin-specific tests

---
*Phase: 05-admin-account-and-authority*
*Completed: 2026-05-06*

## Self-Check: PASSED

All 8 created/modified files verified present. Both task commit hashes (d24aa45, 0ddb2da) verified in git log.
