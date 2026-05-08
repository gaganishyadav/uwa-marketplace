(function ($) {
    'use strict';

    var searchTimer = null;
    var suggestTimer = null;
    var suggestRequest = null;
    var DEBOUNCE_MS = 300;
    var SUGGEST_MIN_CHARS = 3;

    function performSearch() {
        var q = $('#search-input').val().trim();
        var category = $('.filter-pill.active').data('category') || '';
        var minPrice = $('#min-price').val();
        var maxPrice = $('#max-price').val();

        var params = {};
        if (q) params.q = q;
        if (category) params.category = category;
        if (minPrice) params.min_price = minPrice;
        if (maxPrice) params.max_price = maxPrice;

        $.get('/api/search', params, function (html) {
            $('#gallery-grid').html(html);
        }).fail(function () {
            // Graceful degradation per D-09 -- log error, leave current results displayed
            console.error('Search request failed');
        });
    }

    function hideSuggestions() {
        $('#search-suggestions').hide().attr('hidden', true).empty();
    }

    function fetchSuggestions(q) {
        if (suggestRequest) suggestRequest.abort();
        suggestRequest = $.getJSON('/api/listings/suggest', { q: q }, renderSuggestions);
    }

    function renderSuggestions(titles) {
        var $list = $('#search-suggestions');
        if (!titles || !titles.length) {
            hideSuggestions();
            return;
        }
        $list.empty();
        titles.forEach(function (title) {
            $('<li class="search-suggestion-item" tabindex="0"></li>')
                .text(title)
                .on('mousedown', function (e) {
                    e.preventDefault(); // keep input focused while we update
                    selectSuggestion(title);
                })
                .appendTo($list);
        });
        $list.removeAttr('hidden').show();
    }

    function selectSuggestion(title) {
        $('#search-input').val(title);
        $('#search-clear').show();
        hideSuggestions();
        clearTimeout(searchTimer);
        clearTimeout(suggestTimer);
        performSearch();
    }

    function resetFilters() {
        $('#search-input').val('');
        $('#search-clear').hide();
        $('.filter-pill').removeClass('active');
        $('#filter-all').addClass('active');
        $('#min-price').val('');
        $('#max-price').val('');
        hideSuggestions();
        performSearch();
    }

    $(document).ready(function () {
        // Only run on gallery page (check if search bar exists)
        if (!$('#search-input').length) return;

        // Debounced search on text input (per D-02)
        $('#search-input').on('input', function () {
            var val = $(this).val();
            var hasText = val.length > 0;
            $('#search-clear').toggle(hasText);
            clearTimeout(searchTimer);
            searchTimer = setTimeout(performSearch, DEBOUNCE_MS);

            // Typeahead suggestions (min 3 chars)
            clearTimeout(suggestTimer);
            var q = val.trim();
            if (q.length < SUGGEST_MIN_CHARS) {
                hideSuggestions();
            } else {
                suggestTimer = setTimeout(function () { fetchSuggestions(q); }, DEBOUNCE_MS);
            }
        });

        // Hide suggestions on Escape or outside click
        $('#search-input').on('keydown', function (e) {
            if (e.key === 'Escape') hideSuggestions();
        });
        $('#search-input').on('blur', function () {
            // small delay so mousedown on a suggestion fires first
            setTimeout(hideSuggestions, 150);
        });
        $(document).on('click', function (e) {
            if (!$(e.target).closest('.search-input-wrapper').length) hideSuggestions();
        });

        // Debounced search on price inputs
        $('#min-price, #max-price').on('input', function () {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(performSearch, DEBOUNCE_MS);
        });

        // Category pills -- immediate, no debounce (per D-06: single-select toggle)
        $(document).on('click', '.filter-pill', function () {
            var $clicked = $(this);
            if ($clicked.hasClass('active') && $clicked.attr('id') !== 'filter-all') {
                // Clicking active non-"All" pill deselects it, return to "All"
                $('.filter-pill').removeClass('active');
                $('#filter-all').addClass('active');
            } else {
                $('.filter-pill').removeClass('active');
                $clicked.addClass('active');
            }
            performSearch();
        });

        // Clear button in search bar (per D-04)
        $('#search-clear').on('click', function (e) {
            e.stopPropagation();
            resetFilters();
        });

        // Clear filters button in empty state (delegated -- button is in AJAX response, per D-10)
        $(document).on('click', '#btn-clear-filters', function () {
            resetFilters();
        });
    });
})(jQuery);
