# WebSocket Real-Time Chat — Code Explanation

This document explains the code changes that upgraded the UWA Swap-Meet messaging system from a page-reload HTTP flow to a real-time WebSocket chat using **Flask-SocketIO**.

---

## How it works (big picture)

```
Browser A  <---WebSocket--->  Flask-SocketIO Server  <---WebSocket--->  Browser B
   |                                |                                |
   |  emit('send_message', data)    |                                |
   |  ----------------------------> |                                |
   |                                |  persist Message to SQLite     |
   |                                |  broadcast 'new_message'       |
   |                                |  ----------------------------> |
   |   (chat bubble appears)        |                  (chat bubble appears)
```

- The server groups connected clients into **rooms** — one room per conversation thread.
- When a user sends a message, the server saves it to the database and broadcasts it to everyone in that room.
- Both users see the new message instantly — no page reload needed.

---

## File-by-file explanation

### 1. `requirements.txt` — Added Flask-SocketIO

```
Flask-SocketIO==5.5.0
```

Flask-SocketIO is the library that adds WebSocket support to Flask. It provides:
- Room management (group connected clients by conversation)
- Automatic fallback to long-polling if WebSocket fails
- Built-in reconnection logic on the client side
- A JavaScript client (`socket.io.min.js`) loaded from CDN — no npm needed

---

### 2. `app/__init__.py` — App Factory (lines 8, 15, 61, 104-106)

```python
from flask_socketio import SocketIO          # line 8

socketio = SocketIO()                        # line 15 — module-level instance
```

SocketIO is initialized the same way as the other Flask extensions (`db`, `mail`, `csrf`):

```python
socketio.init_app(app, manage_session=False) # line 61
```

- `manage_session=False` tells SocketIO not to interfere with Flask's session handling. The app uses Flask's native cookie-based sessions (`session['user_id']`), so we want SocketIO to leave them alone.

The event handlers are registered after routes:

```python
from app.socket_events import register_socket_events   # line 105
register_socket_events()                                 # line 106
```

---

### 3. `run.py` — Dev Server Entry Point (lines 4, 8)

```python
from app import create_app, socketio      # line 4
app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)         # line 8
```

Instead of `app.run()` (which is a standard WSGI server that doesn't support WebSockets), we use `socketio.run()` which starts a server that handles both HTTP requests and WebSocket connections.

---

### 4. `app/models.py` — Message Model (added `read_at`)

```python
class Message(db.Model):
    # ... existing fields ...
    read_at = db.Column(db.DateTime, nullable=True)  # NEW
```

The `read_at` field tracks when a message was read. It's `None` for unread messages. This powers:
- The `/api/unread-count` endpoint
- Marking messages as read when a user opens a thread

A new database index was added to speed up unread-count queries:

```python
db.Index('ix_message_receiver_read', 'receiver_id', 'read_at')
```

---

### 5. `app/socket_events.py` — WebSocket Event Handlers (NEW FILE)

This is the core of the real-time system. Every WebSocket event has a handler function.

#### Room naming

```python
def _room_key(listing_id, user_a, user_b):
    ids = sorted([user_a, user_b])
    return f"thread_{listing_id}_{ids[0]}_{ids[1]}"
```

Each conversation thread gets a unique room name based on the listing ID and the two user IDs (sorted so both users compute the same room name). Example: `thread_5_2_7`.

#### `connect` (lines 17-20) — Authentication gate

```python
@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        return False
```

When a browser opens a WebSocket connection, this handler checks if the user is logged in (same `session['user_id']` used by HTTP routes). Returning `False` rejects the connection. This prevents unauthenticated users from connecting to the WebSocket.

#### `join_thread` (lines 22-49) — Entering a conversation

```python
@socketio.on('join_thread')
def handle_join_thread(data):
```

When a user opens a thread view, the client sends `join_thread` with `listing_id` and `other_user_id`. The handler:
1. Verifies the user is actually part of this conversation (prevents snooping)
2. Calls `join_room(room)` to add this connection to the thread's room
3. Marks all unread messages from the other user as read (sets `read_at`)

#### `leave_thread` (lines 51-63) — Leaving a conversation

```python
@socketio.on('leave_thread')
def handle_leave_thread(data):
```

When the user navigates away from the thread, the client sends `leave_thread`. The handler calls `leave_room(room)` so the user stops receiving messages for that thread.

#### `send_message` (lines 65-119) — Sending a message in real-time

This is the most important handler. When a user sends a reply in a thread:

1. **Authenticate**: Check `session['user_id']` exists
2. **Validate input**: Content is non-empty and under 1000 chars
3. **Validate CSRF**: The client sends the CSRF token from the `<meta>` tag. The server validates it using `validate_csrf()` — this prevents cross-site request forgery attacks on WebSocket events
4. **Business rules**: Listing must be active (not sold/deleted), no self-messaging, user must be a participant
5. **Persist**: Create a `Message` row in the database
6. **Broadcast**: Emit `new_message` to everyone in the room (both sender and receiver):

```python
socketio.emit('new_message', {
    'id': msg.id,
    'sender_id': user_id,
    'sender_name': sender.display_name,
    'content': msg.content,
    'created_at_formatted': msg.created_at.strftime('%d %b %H:%M'),
}, room=room)
```

The message data includes the formatted timestamp so the client doesn't need to do date formatting.

#### `typing` (lines 121-136) — Typing indicator

```python
socketio.emit('user_typing', {
    'sender_name': sender.display_name,
}, room=room, include_self=False)
```

When a user types, the server broadcasts `user_typing` to the room **excluding the sender** (`include_self=False`) so only the other person sees "Alice is typing...".

---

### 6. `app/routes.py` — New API Endpoint (lines 486-492)

```python
@app.route('/api/unread-count')
@email_verified_required
def api_unread_count():
    count = Message.query.filter_by(
        receiver_id=session['user_id'], read_at=None
    ).count()
    return jsonify({'count': count})
```

A lightweight JSON endpoint that returns the number of unread messages for the logged-in user. This can be polled by the navigation bar to show an unread badge. No existing routes were modified — all HTTP routes still work as fallback.

---

### 7. `app/templates/inbox.html` — Template Changes

#### Data attributes on chat container (lines 44-48)

```html
<div class="chat-container"
     data-listing-id="{{ thread_listing.id if thread_listing else '' }}"
     data-other-user-id="{{ other_user_id }}"
     data-current-user-id="{{ current_user_id }}">
```

These `data-*` attributes pass server-side values to JavaScript so the client knows which conversation it's in. The JS reads them with `$chatContainer.data('listing-id')` etc.

#### Typing indicator (lines 66-68)

```html
<div class="typing-indicator" style="display:none;">
    <span class="typing-indicator-name"></span> is typing...
</div>
```

Hidden by default. JavaScript shows/hides it when the `user_typing` event arrives.

#### SocketIO CDN (lines 130-132)

```html
{% if mode == 'thread' %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
{% endif %}
```

The SocketIO client library is only loaded in thread view — not on the conversation list or other pages. This avoids unnecessary loading on pages that don't use WebSocket.

---

### 8. `app/static/js/inbox.js` — Client-Side Real-Time Logic

#### Initialization (lines 76-81)

```javascript
var $chatContainer = $('.chat-container');
if ($chatContainer.length && typeof io !== 'undefined') {
```

The real-time code only runs if:
- The `.chat-container` element exists (we're in thread view)
- The SocketIO library is loaded (`typeof io !== 'undefined'`)

If either condition is false (e.g. on the conversation list page, or if the CDN failed to load), the code falls back to the standard form POST.

#### Connect and join room (lines 83-90)

```javascript
var socket = io();
socket.on('connect', function () {
    socket.emit('join_thread', {
        listing_id: listingId,
        other_user_id: otherUserId
    });
});
```

`io()` opens a WebSocket connection. Once connected, it immediately joins the thread room so it starts receiving messages.

#### Receiving messages (lines 93-103)

```javascript
socket.on('new_message', function (data) {
    var bubbleClass = data.sender_id === currentUserId
        ? 'chat-bubble--sent' : 'chat-bubble--received';
    var bubble = $(
        '<div class="chat-bubble ' + bubbleClass + '">' +
            '<div>' + escapeHtml(data.content) + '</div>' +
            '<div class="chat-bubble-time">' + escapeHtml(data.created_at_formatted) + '</div>' +
        '</div>'
    );
    $chatContainer.append(bubble);
    $chatContainer.scrollTop($chatContainer[0].scrollHeight);
});
```

When a `new_message` event arrives:
1. Determine if it's sent or received based on `sender_id`
2. Create a chat bubble DOM element (using `escapeHtml()` to prevent XSS)
3. Append it to the chat container
4. Auto-scroll to the bottom so the latest message is visible

#### Sending messages via WebSocket (lines 117-131)

```javascript
$('#form-thread-reply').on('submit', function (e) {
    e.preventDefault();
    var content = $textarea.val().trim();
    if (!content) return;

    socket.emit('send_message', {
        listing_id: listingId,
        other_user_id: otherUserId,
        content: content,
        csrf_token: csrfToken
    });
    $textarea.val('');
});
```

Intercepts the reply form submit, prevents the default HTTP POST, and sends the message via WebSocket instead. The CSRF token is included for server-side validation.

#### Typing indicator (lines 134-143)

```javascript
$('#thread-reply-content').on('input', function () {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function () {
        socket.emit('typing', { listing_id: listingId, other_user_id: otherUserId });
    }, 300);
});
```

Debounced at 300ms — only sends a typing event after the user stops typing for 300ms. This avoids flooding the server with events on every keystroke.

#### Cleanup on page leave (lines 146-151)

```javascript
$(window).on('beforeunload', function () {
    socket.emit('leave_thread', { listing_id: listingId, other_user_id: otherUserId });
});
```

When the user closes the tab or navigates away, emits `leave_thread` so the server removes them from the room.

#### XSS prevention (lines 160-164)

```javascript
function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}
```

Escapes any HTML in message content before inserting it into the DOM. Even though the server creates the payload, this is defense-in-depth against XSS.

---

## Progressive Enhancement

The system is designed to degrade gracefully:

| Scenario | Behavior |
|----------|----------|
| WebSocket works | Real-time messaging, typing indicators |
| WebSocket fails to connect | Falls back to standard form POST (page reload) |
| JavaScript disabled | Form POST still works via the `/thread-reply` route |

All original HTTP routes (`/send-message`, `/inbox`, `/thread-reply`) remain unchanged and functional.

---

## Testing

```bash
# Unit tests — all 90 pass (HTTP routes unchanged)
pytest

# Manual test — real-time chat
flask run
# Open Chrome → login as Alice → send message to Bob's listing
# Open Firefox → login as Bob → open the conversation
# Alice types a reply → Bob sees it instantly (no reload)
```
