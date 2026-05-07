(function () {
    function rewrite() {
        var els = document.querySelectorAll('time.local-time');
        if (!els.length) return;
        var browserLang = navigator.language || '';
        var locale = browserLang.indexOf('en') === 0 ? browserLang : 'en-AU';

        els.forEach(function (el) {
            var iso = el.getAttribute('datetime');
            if (!iso) return;
            var d = new Date(iso);
            if (isNaN(d.getTime())) return;

            var fmt = el.getAttribute('data-format') || '';
            var hasTime = fmt.indexOf('%H') !== -1 || fmt.indexOf('%M') !== -1;
            var hasYear = fmt.indexOf('%Y') !== -1;

            var opts = { day: '2-digit', month: 'short' };
            if (hasYear) opts.year = 'numeric';
            if (hasTime) {
                opts.hour = '2-digit';
                opts.minute = '2-digit';
                opts.hour12 = false;
            }

            var localStr;
            try {
                localStr = new Intl.DateTimeFormat(locale, opts).format(d);
            } catch (e) {
                return;
            }

            var perthFallback = el.textContent.trim();
            if (localStr && localStr !== perthFallback) {
                el.textContent = localStr;
                el.title = 'Perth time: ' + perthFallback;
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', rewrite);
    } else {
        rewrite();
    }
})();
