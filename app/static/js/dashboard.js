$(document).ready(function () {

    // --- Nav Avatar Dropdown ---
    $('#nav-avatar-btn').on('click', function (e) {
        e.stopPropagation();
        var isOpen = $('#nav-dropdown').hasClass('open');
        $('#nav-dropdown').toggleClass('open');
        $(this).attr('aria-expanded', !isOpen);
    });

    $(document).on('click', function () {
        $('#nav-dropdown').removeClass('open');
        $('#nav-avatar-btn').attr('aria-expanded', false);
    });

    // --- Modal Helpers ---
    // Expose globally so inline onclick handlers can call them
    window.openModal = function (selector) {
        $(selector).addClass('open');
        $('body').css('overflow', 'hidden');
    };

    window.closeModal = function ($overlay) {
        $overlay.removeClass('open');
        $('body').css('overflow', '');
    };

    // Close on overlay background click
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

    // --- Open Edit Profile Modal ---
    $('#btn-edit-profile').on('click', function () {
        openModal('#modal-edit-profile');
    });

    // --- Open Post Ad Modal ---
    $('#btn-post-ad, #nav-post-btn').on('click', function () {
        // Reset modal to "List an Item" state
        $('#modal-post-ad .modal-title').text('List an Item');
        $('#form-post-ad')[0].reset();
        // Clear hidden edit-id field
        $('#edit-listing-id').val('');
        // Reset form action to create
        $('#form-post-ad').attr('action', '/create-listing');
        openModal('#modal-post-ad');
    });

    // --- Edit Ad: Prefill modal with existing listing data ---
    window.openEditModal = function (id, title, category, condition, price, description, meetupSpot) {
        // Change modal title
        $('#modal-post-ad .modal-title').text('Edit Ad');
        // Set hidden edit ID
        $('#edit-listing-id').val(id);
        // Change form action to edit route
        $('#form-post-ad').attr('action', '/edit-listing/' + id);
        // Prefill fields
        $('#ad-title').val(title);
        $('#ad-category').val(category);
        $('#ad-condition').val(condition);
        $('#ad-price').val(price);
        $('#ad-description').val(description);
        $('#ad-location').val(meetupSpot);
        openModal('#modal-post-ad');
    };

    // --- File Upload Preview ---
    $('#ad-image').on('change', function () {
        var file = this.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function (e) {
                $('#form-upload-zone').find('.form-upload-icon').html(
                    '<img src="' + e.target.result + '" style="max-height:120px;max-width:100%;border-radius:8px;">'
                );
                $('#form-upload-zone').find('.form-upload-text').text(file.name);
            };
            reader.readAsDataURL(file);
        }
    });

    // --- Edit Profile Form Submit ---
    $('#form-edit-profile').on('submit', function (e) {
        // Form submits normally to /edit-profile -- no preventDefault needed
        // The form has action="/edit-profile" method="POST"
    });

    // --- Empty State Check ---
    function checkEmptyState() {
        if ($('#ads-grid .ad-card').length === 0) {
            $('#ads-grid').html(
                '<div class="ads-empty">' +
                    '<div class="ads-empty-icon"><span class="material-symbols-outlined" style="font-size:3rem;opacity:0.4;">inbox</span></div>' +
                    '<h3 class="ads-empty-title">No listings yet</h3>' +
                    '<p class="ads-empty-desc">Post your first ad to start selling to fellow UWA students.</p>' +
                    '<button class="btn-primary" id="btn-empty-post">Post Your First Ad</button>' +
                '</div>'
            );
            $('#ads-grid').on('click', '#btn-empty-post', function () {
                openModal('#modal-post-ad');
            });
        }
    }

    // Check on load
    checkEmptyState();
});
