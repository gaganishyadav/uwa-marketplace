document.addEventListener('DOMContentLoaded', function () {
    // --- User dropdown toggle (desktop) ---
    var menuBtn = document.getElementById('user-menu-btn');
    var dropdown = document.getElementById('user-dropdown');

    if (menuBtn && dropdown) {
        menuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = dropdown.classList.toggle('open');
            menuBtn.setAttribute('aria-expanded', isOpen);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (e) {
            if (!e.target.closest('#user-menu')) {
                dropdown.classList.remove('open');
                menuBtn.setAttribute('aria-expanded', 'false');
            }
        });

        // Close dropdown on Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && dropdown.classList.contains('open')) {
                dropdown.classList.remove('open');
                menuBtn.setAttribute('aria-expanded', 'false');
                menuBtn.focus();
            }
        });
    }

    // --- Mobile hamburger menu toggle ---
    var hamburger = document.getElementById('nav-hamburger');
    var mobileMenu = document.getElementById('nav-mobile-menu');
    var hamburgerIcon = document.getElementById('hamburger-icon');

    if (hamburger && mobileMenu) {
        hamburger.addEventListener('click', function () {
            var isOpen = mobileMenu.classList.toggle('open');
            // Switch icon between menu and close
            if (hamburgerIcon) {
                hamburgerIcon.textContent = isOpen ? 'close' : 'menu';
            }
            hamburger.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
        });
    }
});
