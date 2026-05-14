"""Tests for messaging system (MSG-01, MSG-02, MSG-03)."""
import pytest
from app import db
from app.models import User, Listing, Message


def _create_verified_user(app, display_name, email):
    """Helper: create a verified user and return their id."""
    with app.app_context():
        user = User(display_name=display_name, email=email)
        user.set_password('Password1')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        return user.id


def _create_listing(app, user_id, title='Test Listing', status='active'):
    """Helper: create a listing and return its id."""
    with app.app_context():
        listing = Listing(
            user_id=user_id,
            title=title,
            description='A test listing description.',
            price=10.0,
            category='Textbooks',
            condition='Good',
            meetup_spot='Reid Library',
            status=status,
        )
        db.session.add(listing)
        db.session.commit()
        return listing.id


def _login(client, email):
    """Helper: log in a user."""
    return client.post('/login', data={'email': email, 'password': 'Password1'})


class TestSendMessage:
    """MSG-01: Send message to listing owner."""

    def test_send_message_success(self, app, client):
        """Buyer can send a message to the listing owner."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'Is this still available?'},
                           headers={'Accept': 'application/json'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'redirect' in data

        with app.app_context():
            msg = Message.query.first()
            assert msg is not None
            assert msg.content == 'Is this still available?'
            assert msg.sender_id == buyer_id
            assert msg.receiver_id == seller_id
            assert msg.listing_id == listing_id

    def test_block_self_messaging(self, app, client):
        """Seller cannot message their own listing (per D-09)."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'seller@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'Hello'},
                           headers={'Accept': 'application/json'})
        assert resp.status_code == 403

    def test_block_empty_message(self, app, client):
        """Empty messages are rejected (per D-09)."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': ''},
                           headers={'Accept': 'application/json'})
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'errors' in data

    def test_block_message_too_long(self, app, client):
        """Messages over 1000 chars are rejected (per D-09)."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'x' * 1001},
                           headers={'Accept': 'application/json'})
        assert resp.status_code == 400

    def test_block_message_on_sold_listing(self, app, client):
        """Messages blocked on sold listings (per D-11)."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id, status='sold')
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'Hello'},
                           headers={'Accept': 'application/json'})
        assert resp.status_code == 400

    def test_block_message_on_deleted_listing(self, app, client):
        """Messages blocked on deleted listings (per D-12)."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id, status='deleted')
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'Hello'},
                           headers={'Accept': 'application/json'})
        assert resp.status_code == 404


class TestViewThread:
    """MSG-02: View message thread per listing."""

    def test_view_thread(self, app, client):
        """User can view their message thread with another user about a listing."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'buyer@test.student.uwa.edu.au')

        # Send a message first
        client.post(f'/send-message/{listing_id}',
                    data={'content': 'Hello!'})

        # View the thread
        resp = client.get(f'/inbox?thread={listing_id}&with_user={seller_id}')
        assert resp.status_code == 200, (
            f"thread view should render for a participant; got {resp.status_code} "
            f"(403 = participant check broken, 404 = thread route missing the case)"
        )
        assert b'Hello!' in resp.data, (
            "the message body 'Hello!' should appear in the rendered thread -- "
            "either the message was not stored, or the template stopped iterating "
            "over the messages list"
        )

    def test_thread_reply(self, app, client):
        """User can reply within a thread."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'buyer@test.student.uwa.edu.au')

        # Send initial message
        client.post(f'/send-message/{listing_id}',
                    data={'content': 'First message'})

        # Reply via thread
        resp = client.post(f'/thread-reply/{listing_id}/{seller_id}',
                           data={'content': 'Reply message'})
        assert resp.status_code == 302  # redirect back to thread

        with app.app_context():
            msgs = Message.query.filter_by(listing_id=listing_id).all()
            contents = [m.content for m in msgs]
            assert len(msgs) == 2, (
                f"expected 2 messages on the thread (1 initial + 1 reply); "
                f"found {len(msgs)}: {contents!r} -- thread-reply may have "
                f"silently dropped the message or written it under a different listing_id"
            )
            assert 'Reply message' in contents, (
                f"expected the reply text 'Reply message' to be saved; "
                f"actual stored contents are {contents!r}"
            )


class TestInbox:
    """MSG-03: Inbox view (all conversations)."""

    def test_inbox_shows_conversations(self, app, client):
        """Inbox displays conversations for the logged-in user."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        _login(client, 'buyer@test.student.uwa.edu.au')

        # Send a message
        client.post(f'/send-message/{listing_id}',
                    data={'content': 'Test message for inbox'})

        # View inbox
        resp = client.get('/inbox')
        assert resp.status_code == 200, f"/inbox should render for a logged-in user; got {resp.status_code}"
        assert b'Test message for inbox' in resp.data, (
            "the conversation preview should include the sent message text -- "
            "the inbox is either skipping this user's conversation or the preview "
            "is being truncated to fewer than the test message's length"
        )

    def test_inbox_empty_state(self, app, client):
        """Empty inbox shows empty state."""
        _create_verified_user(app, 'User', 'user@test.student.uwa.edu.au')
        _login(client, 'user@test.student.uwa.edu.au')

        resp = client.get('/inbox')
        assert resp.status_code == 200, f"/inbox should render even when empty; got {resp.status_code}"
        assert b'No messages yet' in resp.data, (
            "expected the empty-state copy 'No messages yet' on /inbox with no "
            "messages -- the empty-state branch may have been removed from the template"
        )

    def test_inbox_requires_login(self, app, client):
        """Inbox redirects unauthenticated users."""
        resp = client.get('/inbox')
        assert resp.status_code == 302

    def test_inbox_shows_sold_badge(self, app, client):
        """Inbox shows Sold badge for sold listing conversations (per D-13)."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id, status='sold')
        _login(client, 'buyer@test.student.uwa.edu.au')

        # Create a message directly
        with app.app_context():
            msg = Message(
                listing_id=listing_id,
                sender_id=buyer_id,
                receiver_id=seller_id,
                content='Test for sold badge',
            )
            db.session.add(msg)
            db.session.commit()

        resp = client.get('/inbox')
        assert resp.status_code == 200, f"/inbox should render; got {resp.status_code}"
        assert b'Sold' in resp.data, (
            "the 'Sold' badge should appear next to a conversation on a sold listing "
            "(per D-13); not finding it means the template stopped rendering the "
            "status badge or the listing.status wasn't set to 'sold'"
        )


# ---------------------------------------------------------------------------
# Rate-limit tests (per-sender, Message.RATE_LIMIT messages per
# Message.RATE_WINDOW_SECONDS rolling window — see Message model for the actual
# numbers; currently 20 per 60s)
# ---------------------------------------------------------------------------

class TestMessageRateLimit:
    """Per-sender rate limit on /send-message and /thread-reply."""

    def _seed_recent_messages(self, app, sender_id, receiver_id, listing_id, count):
        """Insert `count` messages from sender to receiver dated 'now' so they
        fall inside the rolling window and consume the rate-limit budget."""
        with app.app_context():
            for _ in range(count):
                db.session.add(Message(
                    listing_id=listing_id,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content='spam' * 3,
                ))
            db.session.commit()

    def test_send_message_blocked_at_limit(self, app, client):
        """Once a buyer has sent RATE_LIMIT messages in the window, /send-message
        returns 429 with a JSON error and does not insert a new row."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        self._seed_recent_messages(app, buyer_id, seller_id, listing_id, Message.RATE_LIMIT)
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'one too many'},
                           headers={'Accept': 'application/json'})

        assert resp.status_code == 429, (
            f"expected HTTP 429 once sender exceeds RATE_LIMIT={Message.RATE_LIMIT} "
            f"within {Message.RATE_WINDOW_SECONDS}s; got {resp.status_code}. "
            f"Body: {resp.get_data(as_text=True)[:200]}"
        )
        data = resp.get_json()
        assert data is not None, (
            f"expected JSON response on 429; got non-JSON: {resp.get_data(as_text=True)[:200]}"
        )
        assert 'errors' in data, f"expected 'errors' key in 429 response; got keys: {list(data.keys())}"
        assert any('quickly' in e.lower() for e in data['errors']), (
            f"expected rate-limit message containing 'quickly'; got errors: {data['errors']}"
        )
        with app.app_context():
            count = Message.query.count()
            assert count == Message.RATE_LIMIT, (
                f"rate-limit guard let an extra message through: expected exactly "
                f"{Message.RATE_LIMIT} rows (the pre-seeded ones), found {count}"
            )

    def test_send_message_succeeds_when_seed_is_old(self, app, client):
        """Messages dated outside the rolling window do not consume the budget."""
        from datetime import timedelta
        from app.models import _utcnow

        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        # Pre-seed RATE_LIMIT messages but date them well outside the window
        with app.app_context():
            past = _utcnow() - timedelta(seconds=Message.RATE_WINDOW_SECONDS + 30)
            for _ in range(Message.RATE_LIMIT):
                m = Message(
                    listing_id=listing_id,
                    sender_id=buyer_id,
                    receiver_id=seller_id,
                    content='stale',
                )
                m.created_at = past
                db.session.add(m)
            db.session.commit()
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/send-message/{listing_id}',
                           data={'content': 'fresh'},
                           headers={'Accept': 'application/json'})

        assert resp.status_code == 200, (
            f"expected fresh message to succeed (all seeded rows are outside the "
            f"{Message.RATE_WINDOW_SECONDS}s window); got {resp.status_code}. "
            f"Body: {resp.get_data(as_text=True)[:200]}"
        )
        with app.app_context():
            count = Message.query.count()
            assert count == Message.RATE_LIMIT + 1, (
                f"expected new row to be inserted: {Message.RATE_LIMIT} stale + 1 fresh "
                f"= {Message.RATE_LIMIT + 1} total; found {count}. The rolling window "
                f"may be using >= instead of > on the threshold, or stale rows are "
                f"being counted."
            )

    def test_thread_reply_blocked_at_limit(self, app, client):
        """Once at the limit, /thread-reply flashes an error and writes no row."""
        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        self._seed_recent_messages(app, buyer_id, seller_id, listing_id, Message.RATE_LIMIT)
        _login(client, 'buyer@test.student.uwa.edu.au')

        resp = client.post(f'/thread-reply/{listing_id}/{seller_id}',
                           data={'content': 'reply that should be blocked'},
                           follow_redirects=True)

        assert resp.status_code == 200, (
            f"expected 200 after redirect-then-render flow; got {resp.status_code}. "
            f"Either the redirect target itself errored, or the rate-limit guard "
            f"raised instead of flashing."
        )
        assert b'too quickly' in resp.data.lower(), (
            "expected the flashed rate-limit warning ('...too quickly...') to appear "
            "in the rendered inbox after the redirect, but it wasn't found. The "
            "guard may have allowed the reply through, or the flash category is "
            "being filtered out by the template."
        )
        with app.app_context():
            count = Message.query.count()
            assert count == Message.RATE_LIMIT, (
                f"thread-reply rate-limit guard let a message through: expected "
                f"exactly {Message.RATE_LIMIT} rows (the pre-seeded ones), found {count}"
            )

    def test_recent_count_for_sender_helper(self, app):
        """Unit test for the Message.recent_count_for_sender classmethod."""
        from datetime import timedelta
        from app.models import _utcnow

        seller_id = _create_verified_user(app, 'Seller', 'seller@test.student.uwa.edu.au')
        buyer_id = _create_verified_user(app, 'Buyer', 'buyer@test.student.uwa.edu.au')
        listing_id = _create_listing(app, seller_id)
        with app.app_context():
            # 3 recent, 2 stale
            now = _utcnow()
            stale_at = now - timedelta(seconds=Message.RATE_WINDOW_SECONDS + 30)
            for created in (now, now, now, stale_at, stale_at):
                m = Message(
                    listing_id=listing_id,
                    sender_id=buyer_id,
                    receiver_id=seller_id,
                    content='x',
                )
                m.created_at = created
                db.session.add(m)
            db.session.commit()

            buyer_count = Message.recent_count_for_sender(buyer_id)
            assert buyer_count == 3, (
                f"seeded 3 fresh + 2 stale messages for buyer; expected only the "
                f"3 fresh to be counted, got {buyer_count}. The window check may "
                f"be inclusive on the wrong side, or _utcnow() is drifting."
            )
            assert Message.is_sender_rate_limited(buyer_id) is False, (
                f"buyer has only 3 messages in window vs RATE_LIMIT="
                f"{Message.RATE_LIMIT}; is_sender_rate_limited must be False"
            )
            seller_count = Message.recent_count_for_sender(seller_id)
            assert seller_count == 0, (
                f"the seller never sent anything; expected count 0, got {seller_count}. "
                f"The query is leaking across senders."
            )
