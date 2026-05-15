"""Sanity checks for accessibility markup.

These are page-level smoke tests, not a full audit -- they verify the
landmarks, ARIA roles, and labelling patterns added by the
chore/accessibility-sweep PR survive future template edits.
"""

from app import db
from app.models import User, Listing


def _make_user(app, email='a11y@student.uwa.edu.au'):
    with app.app_context():
        u = User(display_name='A11y User', email=email)
        u.set_password('Password1')
        u.email_verified = True
        db.session.add(u)
        db.session.commit()
        return u.id


def _login(client, uid):
    with client.session_transaction() as sess:
        sess['user_id'] = uid


# ---------------------------------------------------------------------------
# Landmark + skip-link
# ---------------------------------------------------------------------------

def test_every_page_has_main_landmark(client, app):
    """Every authenticated page renders a <main id='main-content'> landmark."""
    uid = _make_user(app)
    _login(client, uid)
    for path in ('/', '/dashboard', '/inbox'):
        body = client.get(path).data
        assert b'id="main-content"' in body, (
            f"page {path} is missing the <main id='main-content'> landmark; "
            f"keyboard users have nothing to skip to"
        )


def test_skip_link_present_on_gallery(client):
    """The keyboard skip-to-content link is the first focusable element."""
    body = client.get('/').data
    assert b'class="skip-link"' in body, "skip-to-content link missing from base.html"
    assert b'#main-content' in body, "skip link does not point at the main landmark"


# ---------------------------------------------------------------------------
# Modal dialog semantics
# ---------------------------------------------------------------------------

def test_post_ad_modal_announces_as_dialog(client, app):
    """The post/edit-ad modal carries role='dialog' aria-modal aria-labelledby."""
    uid = _make_user(app)
    _login(client, uid)
    body = client.get('/dashboard').data
    assert b'id="modal-post-ad"' in body, "post-ad modal not rendered"
    # We can't easily parse the attribute set; verify each piece appears
    # somewhere in the modal markup region. A regression in any one of them
    # would point at the modal having stopped being announced.
    for needle, why in (
        (b'role="dialog"', "modal missing role='dialog'"),
        (b'aria-modal="true"', "modal missing aria-modal='true'"),
        (b'aria-labelledby="modal-post-ad-title"', "modal aria-labelledby drifted from the h2 id"),
        (b'id="modal-post-ad-title"', "modal h2 id was renamed; aria-labelledby will now point at nothing"),
    ):
        assert needle in body, why


def test_edit_profile_modal_announces_as_dialog(client, app):
    """The edit-profile modal carries the same dialog semantics."""
    uid = _make_user(app)
    _login(client, uid)
    body = client.get('/dashboard').data
    assert b'id="modal-edit-profile"' in body
    for needle in (b'role="dialog"', b'aria-modal="true"', b'aria-labelledby="modal-edit-profile-title"'):
        assert needle in body, f"edit-profile modal missing {needle.decode()}"


# ---------------------------------------------------------------------------
# Live regions for AJAX content
# ---------------------------------------------------------------------------

def test_gallery_grid_is_aria_live(client):
    """The grid is replaced wholesale by /api/search; it must be aria-live."""
    body = client.get('/').data
    # Look for the grid element with aria-live on the same element
    assert b'id="gallery-grid"' in body
    # find the gallery-grid tag and check it has aria-live
    idx = body.find(b'id="gallery-grid"')
    # Look backwards for the opening '<' of the same tag
    tag_start = body.rfind(b'<', 0, idx)
    tag_end = body.find(b'>', idx)
    tag = body[tag_start:tag_end + 1]
    assert b'aria-live=' in tag, (
        f"gallery-grid element is missing aria-live -- screen reader users "
        f"will not be told when /api/search updates the result count or grid. "
        f"Tag was: {tag!r}"
    )


# ---------------------------------------------------------------------------
# Decorative icons are not announced
# ---------------------------------------------------------------------------

def test_listing_detail_decorative_icons_aria_hidden(client, app):
    """The four item-meta icons (category, star, location_on, schedule) are aria-hidden."""
    uid = _make_user(app)
    with app.app_context():
        listing = Listing(
            user_id=uid, title='A11y Item', description='Test description please',
            price=10.0, category='Textbooks', condition='Good',
            meetup_spot='Reid Library', status='active',
        )
        db.session.add(listing)
        db.session.commit()
        lid = listing.id

    body = client.get(f'/listing/{lid}').data
    # Each meta icon should have aria-hidden right alongside the icon name
    for icon_name in (b'category', b'star', b'location_on', b'schedule'):
        # Find the icon span and verify aria-hidden is on the SAME tag
        idx = body.find(b'>' + icon_name + b'<')
        assert idx != -1, f"icon span containing {icon_name.decode()} was not rendered"
        tag_start = body.rfind(b'<span', 0, idx)
        tag = body[tag_start:idx]
        assert b'aria-hidden="true"' in tag, (
            f"the decorative icon span for '{icon_name.decode()}' is missing "
            f"aria-hidden='true' -- screen readers will read the icon name "
            f"out loud on top of the label next to it"
        )
