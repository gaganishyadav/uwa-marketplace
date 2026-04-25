# Phase 4: Messaging System - Research

**Researched:** 2026-04-25
**Domain:** Buyer-seller messaging for marketplace listings (Flask/SQLAlchemy/jQuery)
**Confidence:** HIGH

## Summary

This phase adds a messaging layer between buyers and sellers centered on individual listings. The core data model is a single `Message` table linking a sender, a receiver, and a listing -- a denormalized but straightforward approach that avoids the complexity of a separate `Conversation` table. All three requirements (MSG-01: send message, MSG-02: view thread, MSG-03: inbox view) map cleanly to three route handlers added to the existing `init_routes(app)` pattern.

The codebase already provides all the building blocks: modal overlay pattern in `_post_ad_modal.html` and `dashboard.js`, Flask-WTF form validation in `forms.py`, CSRF token handling in every template, and a `listing_detail.html` with a disabled "Message Seller" button placeholder at line 55 ready to be activated. The main work is adding the Message model with a Flask-Migrate migration, three routes (send message, view thread, view inbox), a MessageForm, and three template files (inbox page, thread view within inbox, and message modal partial).

The auto-delete behavior for sold-listing conversations (D-11: 30-day retention) should use lazy cleanup at query time rather than a background job, since this is a SQLite-backed student project with no task queue. The sold_at timestamp needs to be added to the Listing model to support this.

**Primary recommendation:** Add a single `Message` model with `(listing_id, sender_id, receiver_id)` columns, use the existing modal pattern for the "Message Seller" form, and render inbox/thread as a single page with in-place toggle (no SPA routing needed).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** "Message Seller" button opens a **modal** with a text field on the listing detail page (consistent with existing Edit Listing modal pattern)
- **D-02:** Modal appears for logged-in buyers only; seller sees Edit/Mark Sold/Delete buttons instead
- **D-03:** Conversation threads use **chat bubble layout** -- buyer messages aligned right, seller messages aligned left (Messenger/WhatsApp style)
- **D-04:** Timestamps shown small below each bubble
- **D-05:** Thread view opens **in-place** in the inbox page (replaces inbox list; back button returns to inbox)
- **D-06:** Inbox displays conversations as **list rows** -- each row shows: listing image thumbnail, listing title, other user's name, last message preview, timestamp
- **D-07:** Inbox link added to the **nav dropdown** in `_nav.html` (alongside "My Dashboard" and "Browse Listings")
- **D-08:** Conversations ordered by most recent message first
- **D-09:** **Basic validation** -- block empty messages, block messaging yourself (seller can't message own listing), max 1000 characters per message
- **D-10:** Validation errors shown inline near the send button (not page-level flash messages)
- **D-11:** Sold listings: conversations stay visible for **30 days after marked sold**, then auto-delete. New messages are blocked once sold.
- **D-12:** Deleted listings: conversations remain visible showing "Listing removed" label. No new messages allowed.
- **D-13:** Sold badge visible on conversations in inbox for sold listings
- **D-14:** No read/unread tracking for v1 -- keep inbox simple, show all conversations by newest first

### Claude's Discretion
- Message model implementation details (fields, relationships, indexes)
- Thread pagination/scroll behavior for long conversations
- Auto-delete implementation approach (cron-style vs lazy cleanup)
- Modal form styling to match DESIGN.md patterns
- Route structure for inbox and thread endpoints

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MSG-01 | Send message to listing owner | Message model + MessageForm + send_message route + modal in listing_detail.html |
| MSG-02 | View message thread per listing | Conversation query (GROUP BY listing_id, other_user) + thread route + chat bubble template |
| MSG-03 | Inbox view (all conversations) | Inbox route + conversation aggregation query + list-row template in inbox page |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Message persistence | API / Backend (Flask routes) | Database (SQLite) | Messages are server-side records; no client-side storage involved |
| Message form validation | API / Backend (Flask-WTF) | Browser (HTML5 attributes) | Server validates with WTForms; HTML5 maxlength for UX hint only |
| Message sending UX | Browser (jQuery modal) | API / Backend (POST handler) | Modal is browser-side; submission is a standard POST form |
| Inbox rendering | Frontend Server (Jinja2 template) | -- | Server renders full HTML; no AJAX needed for inbox/thread views |
| Auto-delete (sold listings) | API / Backend (query-time cleanup) | Database (WHERE filter) | Lazy cleanup at query time avoids needing a task queue |
| Chat bubble layout | Browser (CSS) | -- | Pure CSS alignment; left/right based on sender |
| Conversation grouping | Database (SQL GROUP BY / subquery) | API / Backend (query construction) | SQL does the heavy lifting; Flask route assembles the query |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.1.0 [VERIFIED: pip show] | Web framework | Already installed; route registration via init_routes |
| Flask-SQLAlchemy | 3.1.1 [VERIFIED: pip show] | ORM / database | Already installed; Message model added alongside User, Listing |
| Flask-WTF | 1.2.2 [VERIFIED: pip show] | Form validation | Already installed; MessageForm follows ListingForm pattern |
| Flask-Migrate | 4.1.0 [VERIFIED: pip show] | Database migrations | Already initialized; new migration for Message table |
| WTForms | 3.2.1 [VERIFIED: pip show] | Form field validators | Already installed; Length validator for message content |
| jQuery | 3.7.1 [VERIFIED: base.html CDN] | DOM manipulation / AJAX | Already loaded on every page; modal helpers already use it |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy (via Flask-SQLAlchemy) | -- | db.func, db.Index for query optimization | Conversation grouping queries, composite index on Message table |
| Alembic (via Flask-Migrate) | -- | Schema migration | `flask db migrate -m "add message and sold_at"` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Separate Conversation table | Denormalized Message-only approach | Conversation table adds complexity (another model, more joins) for a feature that only needs grouping by (listing_id, user pair). A single Message table with a GROUP BY query is simpler and sufficient. |
| WebSocket real-time messages | Polling / page refresh | D-14 explicitly defers notifications. WebSocket is overkill; users refresh to see new messages. |
| AJAX message sending | Full page POST | Could AJAX the send for smoother UX, but the existing pattern uses standard POST + redirect. POST + redirect to the thread is simpler and consistent. |

**Installation:**
No new packages needed -- all dependencies are already installed.

**Version verification:**
```
Flask==3.1.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
Flask-Migrate==4.1.0
WTForms==3.2.1
```

## Architecture Patterns

### System Architecture Diagram

```
[Buyer on listing_detail.html]
        |
        | clicks "Message Seller" button
        v
[Message Modal (jQuery overlay)]
        |
        | POST /send-message/<listing_id>
        v
[send_message route (routes.py)]
        |
        | validates MessageForm, checks ownership
        | creates Message(record) in SQLite
        v
[Redirect to /inbox?thread=<listing_id>&with=<user_id>]
        |
        v
[inbox route (routes.py)]
        |
        | queries conversations (GROUP BY listing + other user)
        | OR queries thread messages (WHERE listing_id + other user)
        v
[inbox.html / thread section]
        |
        | Jinja2 renders chat bubbles or conversation rows
        v
[Browser displays inbox or thread view]

--- Navigation path ---

[_nav.html dropdown]
        |
        | "Inbox" link -> GET /inbox
        v
[inbox route -> inbox.html (conversation list)]
        |
        | click conversation row
        v
[GET /inbox?thread=<listing_id>&with=<user_id>]
        |
        v
[inbox.html (thread view replaces conversation list)]
```

### Recommended Project Structure
```
app/
  models.py            # ADD: Message model, sold_at on Listing
  routes.py            # ADD: send_message, inbox routes inside init_routes
  forms.py             # ADD: MessageForm
  templates/
    _nav.html          # MODIFY: add Inbox link to dropdown
    listing_detail.html # MODIFY: replace disabled button with modal trigger
    _message_modal.html # NEW: message form modal partial
    inbox.html          # NEW: inbox page (conversation list + thread view)
  static/
    css/styles.css      # ADD: chat bubble + inbox row + message modal styles
    js/dashboard.js     # MODIFY: add message modal open handler
    js/inbox.js         # NEW: thread view toggle + message form AJAX (optional)
```

### Pattern 1: Single Message Model (No Conversation Table)
**What:** One `Message` table with `(listing_id, sender_id, receiver_id, content, created_at)`. Conversations are derived at query time by grouping on `(listing_id, the_other_user)` where the current user is either sender or receiver.
**When to use:** When conversations are always 1:1 per listing and don't need independent metadata (title, status, etc.).
**Example:**
```python
# Source: [ASSUMED] based on Flask-SQLAlchemy 3.x patterns verified in codebase
class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    # Relationships
    listing = db.relationship('Listing', backref=db.backref('messages', lazy='dynamic'))
    sender = db.relationship('User', foreign_keys=[sender_id],
                             backref=db.backref('sent_messages', lazy='dynamic'))
    receiver = db.relationship('User', foreign_keys=[receiver_id],
                               backref=db.backref('received_messages', lazy='dynamic'))

    # Composite index for conversation queries
    __table_args__ = (
        db.Index('ix_message_listing_created', 'listing_id', 'created_at'),
        db.Index('ix_message_receiver_created', 'receiver_id', 'created_at'),
    )
```

### Pattern 2: Conversation Grouping Query
**What:** A SQL query that groups messages by (listing_id, other user) to produce the inbox view with last message preview.
**When to use:** Building the inbox conversation list.
**Example:**
```python
# Source: [ASSUMED] SQLAlchemy query pattern for conversation grouping
# Get all conversations for a user (where they are sender OR receiver)
from sqlalchemy import func, case, and_

user_id = session['user_id']

# Subquery: latest message per conversation
latest_msg = db.session.query(
    Message.listing_id,
    case(
        (Message.sender_id == user_id, Message.receiver_id),
        else_=Message.sender_id
    ).label('other_user_id'),
    func.max(Message.created_at).label('last_message_at')
).filter(
    db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
).group_by(
    Message.listing_id,
    'other_user_id'
).subquery()

# Join back to get the actual last message content
conversations = db.session.query(
    Message
).join(
    latest_msg,
    and_(
        Message.listing_id == latest_msg.c.listing_id,
        Message.created_at == latest_msg.c.last_message_at
    )
).order_by(
    Message.created_at.desc()
).all()
```

### Pattern 3: Modal Trigger (Reuse Existing Pattern)
**What:** Reuse the `openModal()` / `closeModal()` jQuery helpers from `dashboard.js` to open a message modal on the listing detail page.
**When to use:** "Message Seller" button click on listing_detail.html.
**Example:**
```javascript
// Source: [VERIFIED: app/static/js/dashboard.js lines 18-21]
// Existing helper -- just need to add a click handler
$('#btn-message-seller').on('click', function() {
    openModal('#modal-message');
});
```

### Anti-Patterns to Avoid
- **Anti-pattern: Separate Conversation model.** Adds unnecessary complexity. The conversation is implicit: it is the set of messages between two users about one listing. A Conversation table would duplicate information already derivable from the Message table.
- **Anti-pattern: Using flash messages for inline validation errors.** D-10 explicitly requires inline errors near the send button, not page-level flash messages. The modal form should show errors in a `.form-errors` div inside the modal.
- **Anti-pattern: AJAX-only message sending.** While AJAX could provide a smoother UX, the established pattern in this codebase is standard POST + redirect. The edit profile form, create listing form, and all action forms use full POST. Stick with this pattern for consistency.
- **Anti-pattern: Querying conversations as N+1.** Do not load all messages and then group in Python. Use SQL GROUP BY to aggregate at the database level. SQLite handles this efficiently for the expected data volume.
- **Anti-pattern: Adding sold_at timestamp to Message queries without a migration.** D-11 requires knowing when a listing was sold (30-day retention). A `sold_at` column must be added to the Listing model with a corresponding Flask-Migrate migration.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSRF protection for message forms | Custom token generation | Flask-WTF `hidden_tag()` / `csrf_token()` | Already integrated; every form in the project uses it |
| Message content validation | Manual string checks | WTForms `DataRequired()`, `Length(max=1000)` | Consistent with all other forms; handles edge cases |
| Password/session auth for messaging | Custom auth decorator | `email_verified_required` decorator | Already exists in routes.py; messaging requires verified email |
| Database schema changes | Manual SQL ALTER TABLE | `flask db migrate` + `flask db upgrade` | Alembic already initialized; migration chain exists |
| XSS in message content | Manual HTML escaping | Jinja2 auto-escaping (default) | Jinja2 `{{ message.content }}` auto-escapes; no need for `|e` filter |
| Modal overlay + animation | New modal CSS/JS | Existing `.modal-overlay` / `openModal()` pattern | Already styled and tested; consistent UX |

**Key insight:** This project has a well-established pattern for every common web operation (forms, modals, auth, CSRF, uploads). The messaging system should follow these patterns exactly rather than introducing new approaches.

## Common Pitfalls

### Pitfall 1: Template Variable Name Mismatch in listing_detail.html
**What goes wrong:** The `listing_detail` route passes `current_user=user` but the template references `user` (which comes from the `inject_user` context processor, not the route variable).
**Why it happens:** Two variables in scope with different names; `current_user` from the route is unused, `user` from the context processor is what the template actually reads.
**How to avoid:** When modifying listing_detail.html for messaging, always use `user` (context processor variable). Do not introduce `current_user` in the template. The messaging modal should check `{% if user and listing.user_id != user.id %}` to show the button to non-owners.
**Warning signs:** Template conditional not rendering correctly; button visible to seller or invisible to buyers.

### Pitfall 2: Self-Messaging Not Blocked at Server Level
**What goes wrong:** If only the template hides the "Message Seller" button from the listing owner, a malicious user could POST directly to `/send-message/<listing_id>` for their own listing.
**Why it happens:** Template-only guards are cosmetic; server must enforce business rules.
**How to avoid:** The `send_message` route must check `if listing.user_id == session['user_id']: abort(403)` before creating the message.
**Warning signs:** Test that POST to own listing returns 403 even without the button.

### Pitfall 3: Sold Listing Message Blocking Inconsistency
**What goes wrong:** D-11 says messages are blocked once sold, but D-12 says deleted listings also block messages. If the listing is physically deleted from the database (current `delete_listing` route does `db.session.delete(listing)`), the foreign key on Message.listing_id will cascade-delete all messages.
**Why it happens:** The current delete route removes the listing row. Messages reference it via foreign key.
**How to avoid:** Either (a) add `ON DELETE SET NULL` to the listing_id foreign key on Message and handle the NULL case in templates, or (b) change the delete behavior to soft-delete (status='deleted'). Option (b) is simpler and more consistent with the existing sold/active status pattern. Recommendation: change `delete_listing` to set `listing.status = 'deleted'` instead of removing the row, and update the gallery query to exclude status='deleted'.
**Warning signs:** Messages disappear when a listing is deleted; foreign key constraint errors.

### Pitfall 4: Conversation Uniqueness Ambiguity
**What goes wrong:** Two users could have multiple conversations about the same listing if the grouping query does not correctly identify the "other user."
**Why it happens:** If user A sends to user B and user B replies, the conversation has messages with different sender_id/receiver_id combinations but is the same conversation.
**How to avoid:** Always group by `(listing_id, CASE WHEN sender_id = current_user THEN receiver_id ELSE sender_id END)`. This normalizes the conversation partner regardless of who sent which messages.
**Warning signs:** Inbox shows two entries for the same listing with the same person.

### Pitfall 5: SQLite datetime Comparison for 30-Day Auto-Delete
**What goes wrong:** Using timezone-aware datetime comparison against naive UTC datetimes stored in SQLite.
**Why it happens:** SQLite has no native datetime type; comparisons are string-based. The project uses `_utcnow()` which returns naive datetimes.
**How to avoid:** Use `_utcnow() - timedelta(days=30)` for comparison, which produces naive datetimes consistent with what is stored. Do NOT use `datetime.utcnow()` (deprecated in Python 3.12+) or timezone-aware datetimes for this comparison.
**Warning signs:** Auto-delete not working; conversations deleted too early or too late.

### Pitfall 6: Missing sold_at Timestamp
**What goes wrong:** D-11 requires 30-day retention after listing is marked sold, but the current Listing model has no `sold_at` field -- only `status` which changes to 'sold'.
**Why it happens:** The `mark_sold` route was not designed with a timestamp.
**How to avoid:** Add `sold_at = db.Column(db.DateTime, nullable=True)` to the Listing model. Set it when `mark_sold` is called. Use this for the 30-day calculation instead of `listing.updated_at` (which does not exist).
**Warning signs:** Cannot determine when a listing was sold; all sold listings appear to have infinite or zero retention.

## Code Examples

### MessageForm (forms.py)
```python
# Source: [ASSUMED] following existing Flask-WTF pattern in forms.py
class MessageForm(FlaskForm):
    """Message form for buyer-seller communication (per D-09: max 1000 chars)."""
    content = TextAreaField('Message', validators=[
        DataRequired(message='Message cannot be empty.'),
        Length(max=1000, message='Message must be 1000 characters or fewer.'),
    ])
```

### send_message Route
```python
# Source: [ASSUMED] following existing route patterns in routes.py
@app.route('/send-message/<int:listing_id>', methods=['POST'])
@email_verified_required
def send_message(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        abort(404)
    # D-09: block messaging yourself
    if listing.user_id == session['user_id']:
        abort(403)
    # D-11: block messages on sold listings
    if listing.status == 'sold':
        flash('This listing has been sold. Messaging is disabled.', 'error')
        return redirect(url_for('listing_detail', listing_id=listing_id))
    # D-12: block messages on deleted listings
    if listing.status == 'deleted':
        abort(404)

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            listing_id=listing_id,
            sender_id=session['user_id'],
            receiver_id=listing.user_id,
            content=form.content.data,
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('inbox', thread=listing_id, with_user=listing.user_id))
    # D-10: inline errors -- redirect back with form data preserved via query params
    # (or render the modal with errors; see Pitfall 1 for template variable handling)
    return redirect(url_for('listing_detail', listing_id=listing_id))
```

### Inbox Conversation Query
```python
# Source: [ASSUMED] SQLAlchemy query pattern for conversation aggregation
@app.route('/inbox')
@email_verified_required
def inbox():
    user_id = session['user_id']
    thread_listing_id = request.args.get('thread', type=int)
    thread_with_user = request.args.get('with_user', type=int)

    if thread_listing_id and thread_with_user:
        # D-05: Show thread view in-place
        messages = Message.query.filter_by(
            listing_id=thread_listing_id
        ).filter(
            db.or_(
                db.and_(Message.sender_id == user_id, Message.receiver_id == thread_with_user),
                db.and_(Message.sender_id == thread_with_user, Message.receiver_id == user_id),
            )
        ).order_by(Message.created_at.asc()).all()
        listing = db.session.get(Listing, thread_listing_id)
        return render_template('inbox.html', mode='thread', messages=messages,
                               listing=listing, other_user_id=thread_with_user)

    # Default: show conversation list
    # Subquery for latest message per conversation
    from sqlalchemy import func, case, and_
    other_user = case(
        (Message.sender_id == user_id, Message.receiver_id),
        else_=Message.sender_id
    ).label('other_user_id')
    latest = db.session.query(
        Message.listing_id,
        other_user,
        func.max(Message.created_at).label('last_at')
    ).filter(
        db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).group_by(Message.listing_id, other_user).subquery()

    conversations = db.session.query(Message).join(
        latest,
        and_(
            Message.listing_id == latest.c.listing_id,
            Message.created_at == latest.c.last_at
        )
    ).order_by(Message.created_at.desc()).all()

    return render_template('inbox.html', mode='list', conversations=conversations,
                           current_user_id=user_id)
```

### Chat Bubble CSS (for DESIGN.md compliance)
```css
/* Source: [ASSUMED] following existing design system variables */
.chat-bubble {
    max-width: 75%;
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-xs);
    word-wrap: break-word;
}

.chat-bubble--sent {
    margin-left: auto;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-container) 100%);
    color: white;
    border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
}

.chat-bubble--received {
    margin-right: auto;
    background: var(--color-surface-low);
    color: var(--color-on-surface);
    border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm);
}

.chat-bubble-time {
    font-size: 0.6875rem;
    color: var(--color-on-surface-variant);
    margin-top: 0.25rem;
}
```

### Inbox Conversation Row Template
```html
{# Source: [ASSUMED] following existing card/row patterns in templates #}
<a href="{{ url_for('inbox', thread=conv.listing_id, with_user=other_user_id) }}"
   class="inbox-row">
    <div class="inbox-row-thumb">
        {% if conv.listing.image_path %}
        <img src="{{ url_for('static', filename='uploads/' + conv.listing.image_path) }}" alt="">
        {% else %}
        <span class="material-symbols-outlined">image</span>
        {% endif %}
    </div>
    <div class="inbox-row-content">
        <div class="inbox-row-title">{{ conv.listing.title }}</div>
        <div class="inbox-row-preview">{{ conv.content[:80] }}{% if conv.content|length > 80 %}...{% endif %}</div>
    </div>
    <div class="inbox-row-meta">
        <span class="inbox-row-name">{{ other_user.display_name }}</span>
        <span class="inbox-row-time">{{ conv.created_at.strftime('%d %b %H:%M') }}</span>
        {% if conv.listing.status == 'sold' %}
        <span class="ad-card-status status-sold" style="font-size:0.5rem;">Sold</span>
        {% endif %}
    </div>
</a>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `datetime.utcnow()` (deprecated) | `_utcnow()` helper with `datetime.now(timezone.utc).replace(tzinfo=None)` | Python 3.12+ | All new models must use `_utcnow()` -- already established in project |
| `lazy='dynamic'` on relationships | Still valid in Flask-SQLAlchemy 3.x | N/A | Dynamic lazy loads return query objects; use `.filter()/.all()` on them |
| `backref` string syntax | Still standard in Flask-SQLAlchemy 3.x | N/A | `db.backref('messages', lazy='dynamic')` is the correct pattern |
| `User.query.get(id)` | `db.session.get(User, id)` in SQLAlchemy 2.0+ style | Flask-SQLAlchemy 3.x | Project already uses `db.session.get()` throughout routes.py |

**Deprecated/outdated:**
- `datetime.utcnow()`: Deprecated in Python 3.12; project already uses `_utcnow()` helper
- `User.query.get()`: Old query API; project has migrated to `db.session.get()`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Conversation grouping via SQL subquery + join performs acceptably for the expected data volume (hundreds of messages, not millions) on SQLite | Architecture Patterns | Would need to switch to a Conversation model if data volume exceeds SQLite's comfortable range; unlikely for a student project |
| A2 | Soft-delete for listings (status='deleted') is acceptable even though current `delete_listing` hard-deletes; changing this behavior may affect existing tests | Common Pitfalls (#3) | Existing delete tests may fail; need to update tests to expect soft-delete behavior |
| A3 | No background task runner (Celery, etc.) exists or should be added; lazy cleanup at query time is sufficient for 30-day auto-delete | Architecture Patterns | If lazy cleanup causes performance issues on the inbox query, a scheduled cleanup CLI command could be added |
| A4 | The `listing_detail` route's `current_user=user` template variable is unused and the template relies solely on the `inject_user` context processor's `user` variable | Common Pitfalls (#1) | If both variables are somehow needed, the template could break; verified by reading the template code |

**If this table is empty:** All claims in this research were verified or cited -- no user confirmation needed.

## Open Questions

1. **Should listing deletion be changed to soft-delete?**
   - What we know: Current `delete_listing` hard-deletes the row. Messages reference listings via foreign key. D-12 says conversations should remain visible with "Listing removed" label after deletion.
   - What's unclear: Whether the project owner is okay with changing delete behavior from hard to soft.
   - Recommendation: Use soft-delete (status='deleted'). This preserves the listing row for message threads while hiding it from gallery. Update the gallery query to `filter(Listing.status != 'deleted')`.

2. **How should inline validation errors work in the message modal?**
   - What we know: D-10 says errors shown inline near the send button, not flash messages. The modal is a form that POSTs.
   - What's unclear: When the form POST fails validation, the redirect back to listing_detail loses the modal state.
   - Recommendation: Use AJAX form submission for the message modal (inconsistent with other forms, but necessary for inline errors within a modal). Return JSON errors on validation failure; show errors inside the modal. On success, redirect to inbox thread view.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All | Yes | 3.x | -- |
| Flask | Routes | Yes | 3.1.0 | -- |
| Flask-SQLAlchemy | Models | Yes | 3.1.1 | -- |
| Flask-WTF | Forms | Yes | 1.2.2 | -- |
| Flask-Migrate | Schema migration | Yes | 4.1.0 | -- |
| SQLite | Database | Yes | (system) | -- |
| jQuery | Modal helpers | Yes | 3.7.1 | -- |
| pytest | Tests | Yes | (installed) | -- |

**Missing dependencies with no fallback:**
None -- all required dependencies are already installed.

**Missing dependencies with fallback:**
None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | None -- conftest.py with in-memory SQLite fixture |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MSG-01 | Send message to listing owner | unit | `pytest tests/test_messaging.py::test_send_message -x` | No -- Wave 0 |
| MSG-01 | Block self-messaging | unit | `pytest tests/test_messaging.py::test_block_self_message -x` | No -- Wave 0 |
| MSG-01 | Block messages on sold listings | unit | `pytest tests/test_messaging.py::test_block_sold_listing_message -x` | No -- Wave 0 |
| MSG-01 | Max 1000 char validation | unit | `pytest tests/test_messaging.py::test_message_max_length -x` | No -- Wave 0 |
| MSG-02 | View message thread | unit | `pytest tests/test_messaging.py::test_view_thread -x` | No -- Wave 0 |
| MSG-03 | Inbox shows conversations | unit | `pytest tests/test_messaging.py::test_inbox_conversations -x` | No -- Wave 0 |
| MSG-03 | Inbox ordered by newest first | unit | `pytest tests/test_messaging.py::test_inbox_ordering -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_messaging.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_messaging.py` -- covers MSG-01, MSG-02, MSG-03
- [ ] No framework install needed -- pytest already configured

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | `email_verified_required` decorator on all messaging routes |
| V3 Session Management | yes | Same session-based auth as rest of app |
| V4 Access Control | yes | Server-side checks: user cannot message own listing; user can only view own conversations |
| V5 Input Validation | yes | WTForms DataRequired + Length(max=1000); Jinja2 auto-escaping for display |
| V6 Cryptography | no | No encryption needed for message content in v1 |

### Known Threat Patterns for Flask/jQuery/SQLite

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Stored XSS via message content | Tampering | Jinja2 auto-escaping (`{{ content }}` escapes HTML); do NOT use `|safe` filter |
| CSRF on message send | Tampering | Flask-WTF CSRF token in hidden form field; `csrf_token()` in templates |
| IDOR on message threads | Information Disclosure | Server-side filter: only show messages where current user is sender or receiver |
| Direct URL access to send-message | Spoofing | `email_verified_required` decorator; ownership check in route |
| SQL injection on conversation query | Tampering | SQLAlchemy ORM parameterized queries (never raw SQL strings) |

## Sources

### Primary (HIGH confidence)
- Codebase review: app/models.py, app/routes.py, app/forms.py, app/templates/*.html, app/static/js/*.js, app/static/css/styles.css -- all verified by reading source files
- pip show output for Flask 3.1.0, Flask-SQLAlchemy 3.1.1, Flask-WTF 1.2.2, Flask-Migrate 4.1.0, WTForms 3.2.1
- Flask-SQLAlchemy documentation (via Context7): relationship patterns, query patterns, model definition

### Secondary (MEDIUM confidence)
- DESIGN.md: Verified color variables, surface hierarchy, button patterns, no-line rule, input field patterns
- Existing test patterns in tests/conftest.py and tests/test_models.py

### Tertiary (LOW confidence)
- None -- all findings verified from codebase or documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all dependencies verified via pip show, already installed
- Architecture: HIGH -- Message model is simple; query patterns are standard SQLAlchemy
- Pitfalls: HIGH -- discovered by reading actual codebase (template variable mismatch, foreign key cascade)
- Integration: HIGH -- all integration points verified by reading existing templates and routes

**Research date:** 2026-04-25
**Valid until:** 2026-05-25 (stable stack, no external API dependencies)
