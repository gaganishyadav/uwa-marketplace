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
        assert resp.status_code == 200
        assert b'Hello!' in resp.data

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
            assert len(msgs) == 2
            assert any(m.content == 'Reply message' for m in msgs)


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
        assert resp.status_code == 200
        assert b'Test message for inbox' in resp.data

    def test_inbox_empty_state(self, app, client):
        """Empty inbox shows empty state."""
        _create_verified_user(app, 'User', 'user@test.student.uwa.edu.au')
        _login(client, 'user@test.student.uwa.edu.au')

        resp = client.get('/inbox')
        assert resp.status_code == 200
        assert b'No messages yet' in resp.data

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
        assert resp.status_code == 200
        assert b'Sold' in resp.data
