$(document).ready(function () {

    // --- Character Counter for Message Modal ---
    $('#message-content').on('input', function () {
        var len = $(this).val().length;
        var max = 1000;
        $('#char-counter').text(len + '/' + max);
        if (len >= max) {
            $('#char-counter').addClass('char-counter--at-limit');
            $('#char-counter').removeClass('char-counter--near-limit');
        } else if (len >= 900) {
            $('#char-counter').addClass('char-counter--near-limit');
            $('#char-counter').removeClass('char-counter--at-limit');
        } else {
            $('#char-counter').removeClass('char-counter--near-limit');
            $('#char-counter').removeClass('char-counter--at-limit');
        }
    });

    // --- AJAX Send Message from Modal (per D-10 inline errors) ---
    $('#form-message').on('submit', function (e) {
        e.preventDefault();
        var $form = $(this);
        var $btn = $('#btn-send-message');
        var $errors = $('#message-errors');
        var listingId = $form.data('listing-id');

        if (!listingId) {
            return;
        }

        $errors.empty();
        $btn.prop('disabled', true).text('Sending...');

        $.ajax({
            url: '/send-message/' + listingId,
            method: 'POST',
            data: $form.serialize(),
            dataType: 'json',
            success: function (resp) {
                if (resp.redirect) {
                    window.location.href = resp.redirect;
                }
            },
            error: function (xhr) {
                $btn.prop('disabled', false).text('Send Message');
                if (xhr.responseJSON) {
                    if (xhr.responseJSON.errors) {
                        xhr.responseJSON.errors.forEach(function (msg) {
                            var $span = $('<span>').addClass('form-error').text(msg);
                            $errors.append($span);
                        });
                    } else if (xhr.responseJSON.error) {
                        var $span = $('<span>').addClass('form-error').text(xhr.responseJSON.error);
                        $errors.append($span);
                    }
                }
            }
        });
    });

    // --- Character Counter for Thread Reply ---
    $('#thread-reply-content').on('input', function () {
        var len = $(this).val().length;
        var max = 1000;
        $('#thread-char-counter').text(len + '/' + max);
    });

    // --- Scroll to bottom of chat container on thread view ---
    var chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // --- Real-time WebSocket chat (thread view only) ---
    var $chatContainer = $('.chat-container');
    if ($chatContainer.length && typeof io !== 'undefined') {
        var listingId = parseInt($chatContainer.data('listing-id'), 10);
        var otherUserId = parseInt($chatContainer.data('other-user-id'), 10);
        var currentUserId = parseInt($chatContainer.data('current-user-id'), 10);
        var csrfToken = $('meta[name="csrf-token"]').attr('content');

        var socket = window.notifSocket || io();

        socket.on('connect', function () {
            socket.emit('join_thread', {
                listing_id: listingId,
                other_user_id: otherUserId
            });
        });

        // Receive new messages in real-time
        socket.on('new_message', function (data) {
            var bubbleClass = data.sender_id === currentUserId ? 'chat-bubble--sent' : 'chat-bubble--received';
            var iso = data.created_at_iso;
            var d = new Date(iso);

            // Perth time fallback (matches server-side local_time filter)
            var perthStr = '';
            if (!isNaN(d.getTime())) {
                perthStr = new Intl.DateTimeFormat('en-AU', {
                    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false,
                    timeZone: 'Australia/Perth'
                }).format(d);
            }

            var senderLabel = data.sender_id === currentUserId ? 'You' : escapeHtml(data.sender_name);
            var timeEl = '<time class="local-time" datetime="' + escapeHtml(iso) + '" data-format="%d %b %H:%M"'
                + ' title="Perth time: ' + escapeHtml(perthStr) + '"'
                + ' aria-label="' + senderLabel + ' at ' + escapeHtml(perthStr) + '">'
                + escapeHtml(perthStr || iso) + '</time>';

            var bubble = $(
                '<div class="chat-bubble ' + bubbleClass + '">' +
                    '<div>' + escapeHtml(data.content) + '</div>' +
                    '<div class="chat-bubble-time">' + timeEl + '</div>' +
                '</div>'
            );
            $chatContainer.append(bubble);

            // Apply browser-local formatting (mirrors local_time.js)
            var timeNode = bubble.find('time.local-time')[0];
            if (timeNode && !isNaN(d.getTime()) && perthStr) {
                var browserLang = navigator.language || '';
                var locale = browserLang.indexOf('en') === 0 ? browserLang : 'en-AU';
                var opts = { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false };
                try {
                    var localStr = new Intl.DateTimeFormat(locale, opts).format(d);
                    if (localStr && localStr !== perthStr) {
                        timeNode.textContent = localStr;
                    }
                } catch (e) { /* keep Perth fallback */ }
            }

            $chatContainer.scrollTop($chatContainer[0].scrollHeight);
        });

        // Server-side rejection (e.g. rate limit) -- surface to the user
        // and put the unsent draft back in the input so they can wait + retry.
        socket.on('send_error', function (data) {
            var msg = (data && data.error) || 'Could not send message.';
            var $errors = $('#thread-reply-errors');
            if ($errors.length) {
                $errors.text(msg).show();
                setTimeout(function () { $errors.fadeOut(); }, 5000);
            } else {
                window.alert(msg);
            }
        });

        // Typing indicator
        var typingTimeout = null;
        socket.on('user_typing', function (data) {
            $('.typing-indicator-name').text(data.sender_name);
            $('.typing-indicator').show();
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(function () {
                $('.typing-indicator').hide();
            }, 2000);
        });

        // Enter to send, Shift+Enter for newline
        $('#thread-reply-content').on('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                $('#form-thread-reply').trigger('submit');
            }
        });

        // Intercept thread reply form — send via WebSocket instead of HTTP POST
        $('#form-thread-reply').on('submit', function (e) {
            e.preventDefault();
            var $textarea = $('#thread-reply-content');
            var content = $textarea.val().trim();
            if (!content) return;

            socket.emit('send_message', {
                listing_id: listingId,
                other_user_id: otherUserId,
                content: content,
                csrf_token: csrfToken
            });
            $textarea.val('');
            $('#thread-char-counter').text('0/1000');
        });

        // Emit typing events (debounced)
        var typingTimer = null;
        $('#thread-reply-content').on('input', function () {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(function () {
                socket.emit('typing', {
                    listing_id: listingId,
                    other_user_id: otherUserId
                });
            }, 300);
        });

        // Leave thread on page unload
        $(window).on('beforeunload', function () {
            socket.emit('leave_thread', {
                listing_id: listingId,
                other_user_id: otherUserId
            });
        });
    } else {
        // Non-WebSocket fallback: standard form submit
        $('#form-thread-reply').on('submit', function () {
            // Let it POST normally
        });
    }
});

function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}
