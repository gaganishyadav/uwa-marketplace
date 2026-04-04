$(document).ready(function () {
    // Tab switching between Login and Sign Up
    $('.auth-tab').on('click', function () {
        var targetTab = $(this).data('tab');

        $('.auth-tab').removeClass('active');
        $(this).addClass('active');

        $('.auth-form').removeClass('active');
        $('#form-' + targetTab).addClass('active');
    });
});
