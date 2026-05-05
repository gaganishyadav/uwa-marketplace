# Phase 5: Admin Account & Authority - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-05
**Phase:** 05-admin-account-and-authority
**Areas discussed:** Admin dashboard layout, User moderation actions, Listing moderation actions, Admin seeding & first admin, Admin navigation & featured badge, Side effects of admin actions, Admin route protection

---

## Admin Dashboard Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Stats cards + data tables | Top stats row, Users table, Listings table. Single-page layout. | |
| Tabbed sections | Separate tabs for Overview, Users, Listings. | |
| Sidebar navigation | Left sidebar with admin nav links, main content on right. | |

**User's choice:** User clarified — no separate admin dashboard. Admin browses the same gallery as normal users with extra controls on cards.

**Notes:** User explicitly said "I don't think we need [a dashboard] right now." Admin controls are overlaid on the existing gallery experience.

---

## User Moderation Actions

| Option | Description | Selected |
|--------|-------------|----------|
| Banned = blocked from app entirely | Banned users see suspension page, can't access anything. | ✓ |
| Banned = read-only access | Banned users can browse but not create/message. | |

**User's choice:** Banned = blocked from app entirely

**Notes:** Two ban levels: temporary ban and permanent ban. Both completely block access. Admin can unban from user detail page. No notifications sent to banned users.

---

## Listing Moderation Actions

| Option | Description | Selected |
|--------|-------------|----------|
| Delete only | Admin can delete any listing. | |
| Delete + feature listing | Admin can delete and also feature/pin listings. | ✓ |

**User's choice:** Delete + feature listing

**Notes:** Featured listings appear at top of gallery with a "Featured" badge. Feature is a toggle.

---

## Admin Seeding & First Admin

| Option | Description | Selected |
|--------|-------------|----------|
| CLI seed command | Flask CLI command to create admin. | |
| First registered user = admin | First registrant auto-admin. | |
| Hardcoded in .env | Admin credentials from .env file. | ✓ |

**User's choice:** Hardcoded in .env

**Notes:** Single admin only — no ability to promote other users. .env stores admin email + password.

---

## Admin Navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Click seller name on cards | Admin clicks seller name → user detail page. | ✓ |
| Admin link in nav dropdown | Dedicated admin page listing all users. | |

**User's choice:** Click seller name on cards

---

## Featured Listings Display

| Option | Description | Selected |
|--------|-------------|----------|
| Top of gallery + badge | Featured items sorted first with a badge/ribbon. | ✓ |
| Separate featured section | Dedicated "Featured" section above normal gallery. | |

**User's choice:** Top of gallery + badge

---

## Side Effects of Admin Actions

| Option | Description | Selected |
|--------|-------------|----------|
| Silent, listings kept with label | No notifications. Banned user's listings show "Seller suspended". | ✓ |
| Silent, listings auto-removed | No notifications. Banned user's listings auto-deleted. | |

**User's choice:** Silent, listings kept with label

---

## Admin Route Protection

| Option | Description | Selected |
|--------|-------------|----------|
| Redirect to home + flash error | Non-admins redirected to home page. | |
| 403 Forbidden page | Non-admins get a 403 error page. | ✓ |

**User's choice:** 403 Forbidden page

---

## Claude's Discretion

- User model ban status field implementation details
- Featured listing query ordering approach
- Admin user detail page layout
- 403 Forbidden page template
- Banned user landing page template
- Flash message wording
- Featured badge CSS styling

## Deferred Ideas

None — discussion stayed within phase scope
