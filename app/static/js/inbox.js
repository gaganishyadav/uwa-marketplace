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

    // --- Thread Reply Form Submission ---
    $('#form-thread-reply').on('submit', function () {
        // Standard form submit -- no preventDefault, let it POST normally
        // The route handles validation and redirects back with errors via flash
    });

    // --- Scroll to bottom of chat container on thread view ---
    var chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
