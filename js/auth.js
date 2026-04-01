$(document).ready(function () {
    // Tab switching between Login and Sign Up
    $('.auth-tab').on('click', function () {
        var targetTab = $(this).data('tab');

        $('.auth-tab').removeClass('active');
        $(this).addClass('active');

        $('.auth-form').removeClass('active');
        $('#form-' + targetTab).addClass('active');
    });

    // Login form submission
    $('#form-login').on('submit', function (e) {
        e.preventDefault();
        var email = $('#login-email').val().trim();
        var password = $('#login-password').val();

        if (!email || !password) {
            return;
        }

        // TODO: Replace with actual AJAX login request
        console.log('Login attempt:', { email: email });
    });

    // Sign Up form submission with validation
    $('#form-signup').on('submit', function (e) {
        e.preventDefault();
        var username = $('#signup-username').val().trim();
        var email = $('#signup-email').val().trim();
        var password = $('#signup-password').val();
        var confirm = $('#signup-confirm').val();

        if (!username || !email || !password || !confirm) {
            return;
        }

        if (password !== confirm) {
            alert('Passwords do not match.');
            return;
        }

        if (password.length < 8) {
            alert('Password must be at least 8 characters.');
            return;
        }

        // TODO: Replace with actual AJAX signup request
        console.log('Signup attempt:', { username: username, email: email });
    });
});
