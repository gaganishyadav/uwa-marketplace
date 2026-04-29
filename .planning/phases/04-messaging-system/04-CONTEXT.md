# Phase 4: Messaging System - Context

**Gathered:** 2026-04-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Buyer-seller messaging for listings: send messages from listing page, view conversation threads, and browse all conversations in an inbox. This phase activates the "Message Seller" button placeholder already in listing_detail.html.

</domain>

<decisions>
## Implementation Decisions

### Message Initiation Flow
- **D-01:** "Message Seller" button opens a **modal** with a text field on the listing detail page (consistent with existing Edit Listing modal pattern)
- **D-02:** Modal appears for logged-in buyers only; seller sees Edit/Mark Sold/Delete buttons instead (already handled in listing_detail.html conditional)

### Message Thread Layout
- **D-03:** Conversation threads use **chat bubble layout** — buyer messages aligned right, seller messages aligned left (Messenger/WhatsApp style)
- **D-04:** Timestamps shown small below each bubble
- **D-05:** Thread view opens **in-place** in the inbox page (replaces inbox list; back button returns to inbox)

### Inbox Design
- **D-06:** Inbox displays conversations as **list rows** — each row shows: listing image thumbnail, listing title, other user's name, last message preview, timestamp
- **D-07:** Inbox link added to the **nav dropdown** in `_nav.html` (alongside "My Dashboard" and "Browse Listings")
- **D-08:** Conversations ordered by most recent message first

### Validation & Edge Cases
- **D-09:** **Basic validation** — block empty messages, block messaging yourself (seller can't message own listing), max 1000 characters per message
- **D-10:** Validation errors shown inline near the send button (not page-level flash messages)

### Sold/Deleted Listing Behavior
- **D-11:** Sold listings: conversations stay visible for **30 days after marked sold**, then auto-delete. New messages are blocked once sold.
- **D-12:** Deleted listings: conversations remain visible showing "Listing removed" label. No new messages allowed.
- **D-13:** Sold badge visible on conversations in inbox for sold listings

### Read/Unread Tracking
- **D-14:** No read/unread tracking for v1 — keep inbox simple, show all conversations by newest first

### Claude's Discretion
- Message model implementation details (fields, relationships, indexes)
- Thread pagination/scroll behavior for long conversations
- Auto-delete implementation approach (cron-style vs lazy cleanup)
- Modal form styling to match DESIGN.md patterns
- Route structure for inbox and thread endpoints

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design System
- `DESIGN.md` — Design system & UI reference (no-line rule, tonal layering, surface hierarchy, button patterns)

### Data Model & Requirements
- `.planning/REQUIREMENTS.md` Section "Messaging" — MSG-01, MSG-02, MSG-03 requirements and Messages data model definition
- `.planning/ROADMAP.md` Phase 4 section — success criteria and requirements mapping

### Existing Integration Points
- `app/templates/listing_detail.html` — "Message Seller" disabled button placeholder at line 55
- `app/templates/_nav.html` — Nav dropdown where inbox link will be added
- `app/models.py` — Existing User and Listing models; Message model to be added
- `app/routes.py` — Route patterns (init_routes, decorators, form handling)
- `app/forms.py` — Flask-WTF form patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Modal pattern**: Edit Listing modal in `_post_ad_modal.html` — same JS pattern can be reused for message modal
- **CSRF handling**: Every form includes `csrf_token()` hidden input — messaging forms must follow this pattern
- **Context processor**: `inject_user` makes user available globally in templates — use for nav inbox badge if added later
- **Route decorators**: `login_required` and `email_verified_required` — messaging should use `email_verified_required`

### Established Patterns
- **No Blueprints**: All routes attached via `init_routes(app)` with `@app.route()` decorators
- **Naive UTC datetimes**: `_utcnow()` helper in models.py for SQLite compatibility
- **Flash messages**: `flash('msg', 'success'|'error')` pattern for form feedback
- **Template structure**: Base template with `{% block content %}`, partials prefixed with `_`

### Integration Points
- **listing_detail.html:55**: Replace disabled "Message Seller" button with functional modal trigger
- **_nav.html**: Add "Inbox" link to nav dropdown (line 16-17 area, between "My Dashboard" and divider)
- **models.py**: Add `Message` model alongside User and Listing
- **routes.py**: Add messaging routes (send message, view inbox, view thread) inside `init_routes`
- **forms.py**: Add `MessageForm` for message validation

</code_context>

<specifics>
## Specific Ideas

- Chat bubble layout for message threads (Messenger-style, left/right alignment)
- 30-day auto-deletion of messages after listing is marked sold
- Inbox as list rows (email-style, not cards)
- Message modal from listing detail page (not a separate page)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-messaging-system*
*Context gathered: 2026-04-25*
