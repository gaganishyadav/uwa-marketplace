$(document).ready(function () {

    // ─── Nav Avatar Dropdown ────────────────────────────────────────────────
    $('#nav-avatar-btn').on('click', function (e) {
        e.stopPropagation();
        const isOpen = $('#nav-dropdown').hasClass('open');
        $('#nav-dropdown').toggleClass('open');
        $(this).attr('aria-expanded', !isOpen);
    });

    $(document).on('click', function () {
        $('#nav-dropdown').removeClass('open');
        $('#nav-avatar-btn').attr('aria-expanded', false);
    });

    // ─── Modal Helpers ──────────────────────────────────────────────────────
    function openModal(selector) {
        $(selector).addClass('open');
        $('body').css('overflow', 'hidden');
    }

    function closeModal($overlay) {
        $overlay.removeClass('open');
        $('body').css('overflow', '');
    }

    // Close on overlay click
    $('.modal-overlay').on('click', function (e) {
        if ($(e.target).hasClass('modal-overlay')) {
            closeModal($(this));
        }
    });

    // Close on Escape key
    $(document).on('keydown', function (e) {
        if (e.key === 'Escape') {
            $('.modal-overlay.open').each(function () {
                closeModal($(this));
            });
        }
    });

    // All modal close buttons
    $('.modal-close').on('click', function () {
        closeModal($(this).closest('.modal-overlay'));
    });

    // ─── Open Edit Profile Modal ────────────────────────────────────────────
    $('#btn-edit-profile').on('click', function () {
        openModal('#modal-edit-profile');
    });

    // ─── Open Post Ad Modal ─────────────────────────────────────────────────
    $('#btn-post-ad, #nav-post-btn').on('click', function () {
        // Reset modal to "Post New Ad" state
        $('#modal-post-ad .modal-title').text('Post New Ad');
        $('#form-post-ad')[0].reset();
        openModal('#modal-post-ad');
    });

    // ─── View Public Profile (placeholder) ─────────────────────────────────
    $('#btn-view-public').on('click', function () {
        // TODO: link to /profile/<username> once backend is ready
        alert('Public profile view coming soon!');
    });

    // ─── Edit Profile Form Submit ───────────────────────────────────────────
    $('#form-edit-profile').on('submit', function (e) {
        e.preventDefault();
        const name = $('#edit-display-name').val().trim();
        const bio  = $('#edit-bio').val().trim();
        const pref = $('#edit-contact-pref').val();

        if (!name) {
            $('#edit-display-name').focus();
            return;
        }

        // Update visible profile name & bio
        $('.profile-name').text(name);
        $('.profile-bio').text(bio);

        // Update avatar initials (first letter of each word, max 2)
        const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
        $('.profile-avatar-lg, .nav-avatar').text(initials);

        // TODO: AJAX POST to /api/profile when backend is ready
        console.log('Profile update:', { name, bio, pref });

        closeModal($('#modal-edit-profile'));
    });

    // ─── Post New Ad Form Submit ────────────────────────────────────────────
    $('#form-post-ad').on('submit', function (e) {
        e.preventDefault();
        const payload = {
            title:       $('#ad-title').val().trim(),
            category:    $('#ad-category').val(),
            price:       parseFloat($('#ad-price').val()),
            condition:   $('#ad-condition').val(),
            description: $('#ad-description').val().trim(),
            location:    $('#ad-location').val(),
        };

        if (!payload.title || !payload.category || isNaN(payload.price) || !payload.condition || !payload.location) {
            return;
        }

        // TODO: AJAX POST to /api/listings when backend is ready
        console.log('New ad payload:', payload);

        closeModal($('#modal-post-ad'));
    });

    // ─── Ad Card: Edit ──────────────────────────────────────────────────────
    // Delegate to handle cards added dynamically in the future
    $('#ads-grid').on('click', '.btn-ad-edit', function () {
        const card     = $(this).closest('.ad-card');
        const title    = card.find('.ad-card-title').text().trim();
        const category = card.find('.ad-card-category').text().trim().toLowerCase();

        // Pre-fill form with existing data
        $('#ad-title').val(title);
        // Attempt to match category value from the select options
        $('#ad-category option').filter(function () {
            return $(this).text().toLowerCase().includes(category);
        }).prop('selected', true);

        $('#modal-post-ad .modal-title').text('Edit Ad');
        openModal('#modal-post-ad');
    });

    // ─── Ad Card: Mark Sold ─────────────────────────────────────────────────
    $('#ads-grid').on('click', '.btn-ad-sold', function () {
        const card = $(this).closest('.ad-card');
        card.find('.ad-card-status')
            .removeClass('status-active')
            .addClass('status-sold')
            .text('Sold');
        card.addClass('ad-card--sold');
        $(this).remove();

        // Disable the edit button on now-sold card
        card.find('.btn-ad-edit').prop('disabled', true);

        // TODO: AJAX PATCH to /api/listings/<id>/sold
        console.log('Marked sold:', card.data('id'));
    });

    // ─── Ad Card: Delete ────────────────────────────────────────────────────
    $('#ads-grid').on('click', '.btn-ad-delete', function () {
        const card = $(this).closest('.ad-card');
        if (!confirm('Are you sure you want to delete this listing?')) return;

        card.fadeOut(200, function () {
            $(this).remove();
            checkEmptyState();
        });

        // TODO: AJAX DELETE to /api/listings/<id>
        console.log('Deleted listing:', card.data('id'));
    });

    // ─── Empty State ────────────────────────────────────────────────────────
    function checkEmptyState() {
        if ($('#ads-grid .ad-card').length === 0) {
            $('#ads-grid').html(
                '<div class="ads-empty">' +
                    '<div class="ads-empty-icon">📭</div>' +
                    '<h3 class="ads-empty-title">No listings yet</h3>' +
                    '<p class="ads-empty-desc">Post your first ad to start selling to fellow UWA students.</p>' +
                    '<button class="btn-primary" id="btn-empty-post">Post Your First Ad</button>' +
                '</div>'
            );
            // Bind the new button
            $('#ads-grid').on('click', '#btn-empty-post', function () {
                openModal('#modal-post-ad');
            });
        }
    }

});