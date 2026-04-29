---
phase: 04-messaging-system
plan: 01
subsystem: database
tags: [sqlalchemy, alembic, migration, wtforms, soft-delete]

# Dependency graph
requires:
  - phase: 02-marketplace-core
    provides: Listing model, routes.py structure, Flask-WTF form patterns
provides:
  - Message model with listing_id, sender_id, receiver_id, content, timestamps
  - MessageForm with DataRequired and Length(max=1000) validation
  - sold_at timestamp on Listing model
  - Soft-delete pattern for listings (status='deleted')
  - Alembic migration for message table and sold_at column
affects: [04-02, 04-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [soft-delete via status column, dual-FK relationships with foreign_keys param]

key-files:
  created:
    - migrations/versions/32ceec45067d_add_message_table_and_sold_at_to_listing.py
  modified:
    - app/models.py
    - app/forms.py
    - app/routes.py

key-decisions:
  - "Used foreign_keys parameter on Message relationships to disambiguate dual User FKs (sender_id, receiver_id)"
  - "Soft-delete via status='deleted' preserves message thread history per D-12"
  - "sold_at set alongside status change in mark_sold for audit trail"

patterns-established:
  - "Soft-delete: set status='deleted' instead of db.session.delete(); clear image_path"
  - "Dual FK relationships: use foreign_keys=[col] parameter for multiple FKs to same table"

requirements-completed: [MSG-01, MSG-02, MSG-03]

# Metrics
duration: 4min
completed: 2026-04-25
---

# Phase 4 Plan 1: Data Layer Summary

**Message model with dual-User FKs, MessageForm validation, Listing soft-delete and sold_at timestamp via Alembic migration**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-25T11:55:02Z
- **Completed:** 2026-04-25T11:59:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Message model with composite indexes on (listing_id, created_at) and (receiver_id, created_at)
- MessageForm with DataRequired and Length(max=1000) validators matching existing form patterns
- Converted hard-delete to soft-delete so message threads referencing deleted listings remain visible
- Added sold_at timestamp to Listing for audit trail when items are marked sold
- Alembic migration generated and applied cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Message model and sold_at field to Listing** - `761439f` (feat)
2. **Task 2: Add MessageForm, soft-delete, sold_at timestamp, and migration** - `ab896c9` (feat)

## Files Created/Modified
- `app/models.py` - Added Message model with relationships, indexes; added sold_at to Listing
- `app/forms.py` - Added MessageForm with validation
- `app/routes.py` - Soft-delete in delete_listing, sold_at in mark_sold, _utcnow import
- `migrations/versions/32ceec45067d_add_message_table_and_sold_at_to_listing.py` - Alembic migration

## Decisions Made
- Used `foreign_keys=[sender_id]` and `foreign_keys=[receiver_id]` on User relationships to disambiguate the two FK columns pointing to the same table (SQLAlchemy pattern for multiple FKs)
- Kept image deletion on disk in soft-delete flow but cleared `image_path` to None to release storage while preserving the listing row
- Gallery and search routes already filter by explicit status values, so deleted listings are excluded without code changes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Message model ready for Plan 02 (message routes and conversation views)
- MessageForm ready for Plan 02 message sending endpoints
- Soft-delete pattern in place so Plan 03 (inbox/notifications) can show thread history for deleted listings
- Gallery and search already exclude deleted listings

## Self-Check: PASSED

All files verified present, all commits verified in git log.

---
*Phase: 04-messaging-system*
*Completed: 2026-04-25*
