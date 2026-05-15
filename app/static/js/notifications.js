(function () {
    if (typeof io === 'undefined') return;

    var socket = io();
    window.notifSocket = socket;

    socket.on('unread_notification', function (data) {
        var count = data && data.count;
        if (typeof count !== 'number') return;

        // --- Avatar badge ---
        var avatarBtn = document.getElementById('nav-avatar-btn');
        if (avatarBtn) {
            var badge = avatarBtn.querySelector('.nav-badge');
            if (count > 0) {
                var label = count < 10 ? String(count) : '9+';
                if (badge) {
                    badge.textContent = label;
                } else {
                    badge = document.createElement('span');
                    badge.className = 'nav-badge';
                    badge.setAttribute('aria-hidden', 'true');
                    badge.textContent = label;
                    avatarBtn.appendChild(badge);
                }
                avatarBtn.setAttribute('aria-label', count + ' unread message' + (count !== 1 ? 's' : ''));
            } else {
                if (badge) badge.remove();
                avatarBtn.removeAttribute('aria-label');
            }
        }

        // --- Dropdown Inbox badge ---
        var inboxLink = document.querySelector('.nav-dropdown-item--with-badge');
        if (inboxLink) {
            var dropBadge = inboxLink.querySelector('.nav-dropdown-badge');
            if (count > 0) {
                var label = count < 100 ? String(count) : '99+';
                if (dropBadge) {
                    dropBadge.textContent = label;
                } else {
                    dropBadge = document.createElement('span');
                    dropBadge.className = 'nav-dropdown-badge';
                    dropBadge.textContent = label;
                    inboxLink.appendChild(dropBadge);
                }
            } else {
                if (dropBadge) dropBadge.remove();
            }
        }
    });
})();
