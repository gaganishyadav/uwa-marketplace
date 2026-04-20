---
phase: 03-search-discovery
plan: 01
subsystem: api
tags: [flask, sqlalchemy, ilike, ajax, search, html-partial]

# Dependency graph
requires:
  - phase: 02-marketplace-core
    provides: Listing model, listing_card macro, gallery route pattern
provides:
  - /api/search GET endpoint with keyword, category, price range filtering
  - _search_results.html partial for AJAX card rendering
  - 12 unit tests covering all search behaviors
affects: [03-search-discovery, frontend-search-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [server-side-html-partial-for-ajax, separate-active-sold-queries, like-wildcard-escaping]

key-files:
  created:
    - app/templates/_search_results.html
    - tests/test_search.py
  modified:
    - app/routes.py

key-decisions:
  - "No @login_required on /api/search -- gallery is public, search inherits same access policy"
  - "LIKE wildcards (% and _) escaped with backslash before ilike() to prevent wildcard abuse"
  - "Active and sold listings queried separately then concatenated for active-before-sold ordering"

patterns-established:
  - "Server-side HTML partial rendering: endpoint returns rendered HTML cards, not JSON, for AJAX insertion"
  - "Separate active/sold query pattern: two filtered queries concatenated to guarantee active-first ordering"

requirements-completed: [MARKET-06, MARKET-07, MARKET-08]

# Metrics
duration: 4min
completed: 2026-04-20
---

# Phase 3 Plan 01: Search API Endpoint Summary

**Flask /api/search GET endpoint with keyword (ilike), category, price range filtering, active-before-sold ordering, and server-side HTML partial rendering via _search_results.html**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-20T09:40:29Z
- **Completed:** 2026-04-20T09:44:29Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- /api/search endpoint handles keyword search across title+description, category filtering, and min/max price range
- Active listings always appear before sold listings in search results
- LIKE wildcard characters (% and _) properly escaped to prevent abuse (threat T-03-01 mitigated)
- Empty state with "No listings found" and "Clear filters" button rendered when no matches
- Result count text included in every response ("Showing N listings" or "N results for query")
- 12 unit tests passing, 60 total tests with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Write search endpoint unit tests (RED phase)** - `2c61909` (test)
2. **Task 2: Implement /api/search endpoint and _search_results.html partial (GREEN phase)** - `6ab9e46` (feat)

_Note: TDD flow -- RED commit (failing tests) then GREEN commit (all passing)_

## Files Created/Modified
- `app/routes.py` - Added api_search() route with @app.route('/api/search') inside init_routes()
- `app/templates/_search_results.html` - HTML partial importing listing_card macro, rendering cards or empty state
- `tests/test_search.py` - 12 unit tests for search/filter behaviors with seeded fixture

## Decisions Made
- No @login_required on /api/search -- the gallery page is publicly accessible and search inherits the same access model
- Separate active_query and sold_query SQLAlchemy queries concatenated (not UNION) for guaranteed active-first ordering
- LIKE wildcards escaped via `q.replace('%', r'\%').replace('_', r'\_')` before ilike() pattern construction
- db.or_() used for SQLAlchemy OR clauses, consistent with Flask-SQLAlchemy 3.1 patterns in codebase

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect test assertion in test_filter_min_price**
- **Found during:** Task 2 (GREEN phase -- running tests)
- **Issue:** Test asserted `assert b'Calculus Textbook' in response.data` for min_price=50, but Calculus Textbook costs $45 which is below the threshold. The comment said "should NOT appear" but the assertion checked the opposite direction.
- **Fix:** Changed to `assert b'Calculus Textbook' not in response.data` and replaced fragile `ad-card` CSS class count with explicit negative assertions for each excluded listing.
- **Files modified:** tests/test_search.py
- **Verification:** All 12 tests pass, full suite (60 tests) passes
- **Committed in:** 6ab9e46 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test logic correction. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- /api/search endpoint ready for frontend AJAX wiring (Plan 03-02)
- _search_results.html partial ready for jQuery load() or fetch() insertion into gallery page
- Frontend needs search bar, category pills, and price range inputs added to gallery.html

---
*Phase: 03-search-discovery*
*Completed: 2026-04-20*

## Self-Check: PASSED

- FOUND: app/routes.py
- FOUND: app/templates/_search_results.html
- FOUND: tests/test_search.py
- FOUND: commit 2c61909 (Task 1 - RED)
- FOUND: commit 6ab9e46 (Task 2 - GREEN)
