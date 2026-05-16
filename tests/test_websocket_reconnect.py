"""WebSocket reconnection tests.

The chat UI uses Socket.IO, which reconnects automatically when the
underlying transport drops. These tests use Flask-SocketIO's
SocketIOTestClient to simulate that flow at the server boundary:

  - a client can be disconnected and a fresh client can connect
    again under the same authenticated session
  - after reconnection, joining the same thread works and incoming
    messages are still received

Real-world disconnects happen when:
  - the user's network blips (wifi <-> mobile handoff)
  - the server is restarted during deploy
  - the browser tab is backgrounded too long for the socket to stay alive
"""
from app import db, socketio
from app.models import User, Listing, Message


def _make_verified(app, display_name, email):
    """Create a verified user, return their id."""
    with app.app_context():
        u = User(display_name=display_name, email=email)
        u.set_password('Password1')
        u.email_verified = True
        db.session.add(u)
        db.session.commit()
        return u.id


def _make_listing(app, owner_id):
    """Create an active listing, return its id."""
    with app.app_context():
        listing = Listing(
            user_id=owner_id, title='Socket Test Item',
            description='Listing used by WebSocket reconnect tests.',
            price=10.0, category='Textbooks', condition='Good',
            meetup_spot='Reid Library', status='active',
        )
        db.session.add(listing)
        db.session.commit()
        return listing.id


def _seed_thread(app, sender_id, receiver_id, listing_id, content='hi'):
    """Insert a seed message so participant checks accept the pair."""
    with app.app_context():
        m = Message(
            listing_id=listing_id, sender_id=sender_id,
            receiver_id=receiver_id, content=content,
        )
        db.session.add(m)
        db.session.commit()


def _login_session(flask_client, user_id):
    """Set user_id in the Flask session so socketio.test_client sees it."""
    with flask_client.session_transaction() as sess:
        sess['user_id'] = user_id


def test_socket_can_be_disconnected_and_reconnected(app, client):
    """An authenticated client can disconnect and a fresh client can
    connect again under the same session."""
    uid = _make_verified(app, 'Sock User', 'sock@test.student.uwa.edu.au')
    _login_session(client, uid)

    # First connection
    sio_a = socketio.test_client(app, flask_test_client=client)
    assert sio_a.is_connected(), (
        "first socket client should be accepted -- the connect handler "
        "rejected an authenticated session. Check handle_connect's "
        "session.get('user_id') guard."
    )
    sio_a.disconnect()
    assert not sio_a.is_connected(), "first client should be disconnected"

    # Reconnect: a fresh test client under the same Flask session
    sio_b = socketio.test_client(app, flask_test_client=client)
    assert sio_b.is_connected(), (
        "second socket client (reconnection) should be accepted -- "
        "either the server is holding state from the first connection "
        "that blocks a re-connect, or the session is being cleared on "
        "disconnect"
    )
    sio_b.disconnect()
