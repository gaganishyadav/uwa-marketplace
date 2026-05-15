from flask import request, session
from flask_socketio import join_room, leave_room
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError

from app import db, socketio
from app.models import User, Listing, Message, _utcnow


def _room_key(listing_id, user_a, user_b):
    ids = sorted([user_a, user_b])
    return f"thread_{listing_id}_{ids[0]}_{ids[1]}"


def register_socket_events():

    @socketio.on('connect')
    def handle_connect():
        if 'user_id' not in session:
            return False

    @socketio.on('join_thread')
    def handle_join_thread(data):
        user_id = session.get('user_id')
        if not user_id:
            return False

        listing_id = data.get('listing_id')
        other_user_id = data.get('other_user_id')
        if not listing_id or not other_user_id:
            return

        existing = Message.query.filter_by(listing_id=listing_id).filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
        ).first()
        if not existing:
            return

        room = _room_key(listing_id, user_id, other_user_id)
        join_room(room)

        Message.query.filter_by(
            listing_id=listing_id,
            sender_id=other_user_id,
            receiver_id=user_id,
            read_at=None,
        ).update({'read_at': _utcnow()})
        db.session.commit()

    @socketio.on('leave_thread')
    def handle_leave_thread(data):
        user_id = session.get('user_id')
        if not user_id:
            return

        listing_id = data.get('listing_id')
        other_user_id = data.get('other_user_id')
        if not listing_id or not other_user_id:
            return

        room = _room_key(listing_id, user_id, other_user_id)
        leave_room(room)

    @socketio.on('send_message')
    def handle_send_message(data):
        user_id = session.get('user_id')
        if not user_id:
            return

        listing_id = data.get('listing_id')
        other_user_id = data.get('other_user_id')
        content = (data.get('content') or '').strip()
        csrf_token = data.get('csrf_token')

        if not listing_id or not other_user_id or not content:
            return

        try:
            validate_csrf(csrf_token)
        except ValidationError:
            return

        if len(content) > 1000:
            return

        listing = db.session.get(Listing, listing_id)
        if not listing or listing.status == 'deleted':
            return
        if listing.status == 'sold':
            return
        if other_user_id == user_id:
            return

        existing = Message.query.filter_by(listing_id=listing_id).filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
        ).first()
        if not existing:
            return

        # Per-sender rate limit (anti-spam). Mirrors the guard on
        # /send-message and /thread-reply; otherwise an abusive client
        # could bypass throttling by going straight through the socket.
        if Message.is_sender_rate_limited(user_id):
            socketio.emit('send_error', {
                'error': (f'You are sending messages too quickly. Please wait a moment '
                          f'(limit: {Message.RATE_LIMIT} per minute).')
            }, to=request.sid)
            return

        msg = Message(
            listing_id=listing_id,
            sender_id=user_id,
            receiver_id=other_user_id,
            content=content,
        )
        db.session.add(msg)
        db.session.commit()

        sender = db.session.get(User, user_id)
        room = _room_key(listing_id, user_id, other_user_id)
        socketio.emit('new_message', {
            'id': msg.id,
            'sender_id': user_id,
            'sender_name': sender.display_name if sender else 'Unknown',
            'content': msg.content,
            'created_at_iso': msg.created_at.replace(tzinfo=timezone.utc).isoformat(),
        }, room=room)

    @socketio.on('typing')
    def handle_typing(data):
        user_id = session.get('user_id')
        if not user_id:
            return

        listing_id = data.get('listing_id')
        other_user_id = data.get('other_user_id')
        if not listing_id or not other_user_id:
            return

        sender = db.session.get(User, user_id)
        room = _room_key(listing_id, user_id, other_user_id)
        socketio.emit('user_typing', {
            'sender_name': sender.display_name if sender else 'Someone',
        }, room=room, include_self=False)
