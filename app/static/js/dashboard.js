$(document).ready(function () {

    // ─── Nav Avatar Dropdown ────────────────────────────────────────────────
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

    // ─── Modal Helpers ──────────────────────────────────────────────────────
    window.openModal = function (selector) {
        $(selector).addClass('open');
        $('body').css('overflow', 'hidden');
    };

    window.closeModal = function ($overlay) {
        $overlay.removeClass('open');
        $('body').css('overflow', '');
    };

    $('.modal-overlay').on('click', function (e) {
        if ($(e.target).hasClass('modal-overlay')) {
            closeModal($(this));
        }
    });

    $(document).on('keydown', function (e) {
        if (e.key === 'Escape') {
            $('.modal-overlay.open').each(function () {
                closeModal($(this));
            });
        }
    });

    $('.modal-close').on('click', function () {
        closeModal($(this).closest('.modal-overlay'));
    });

    // ─── Open Edit Profile Modal ────────────────────────────────────────────
    $('#btn-edit-profile').on('click', function () {
        openModal('#modal-edit-profile');
    });

    // ─── Open Post Ad Modal ─────────────────────────────────────────────────
    $('#btn-post-ad, #nav-post-btn').on('click', function () {
        $('#modal-post-ad .modal-title').text('Post New Ad');
        // Reset modal to "List an Item" state
        $('#modal-post-ad .modal-title').text('List an Item');
        $('#form-post-ad')[0].reset();
        $('#edit-listing-id').val('');
        $('#form-post-ad').attr('action', '/create-listing');
        openModal('#modal-post-ad');
        initMeetupMap(null);
    });

    // ─── Edit Ad Modal ──────────────────────────────────────────────────────
    window.openEditModal = function (id, title, category, condition, price, description, meetupSpot) {
        $('#modal-post-ad .modal-title').text('Edit Ad');
        $('#edit-listing-id').val(id);
        $('#form-post-ad').attr('action', '/edit-listing/' + id);
        $('#ad-title').val(title);
        $('#ad-category').val(category);
        $('#ad-condition').val(condition);
        $('#ad-price').val(price);
        $('#ad-description').val(description);
        $('#ad-location').val(meetupSpot);
        openModal('#modal-post-ad');
        initMeetupMap(meetupSpot);
    };

    // --- Open Message Seller Modal ---
    $('#btn-message-seller').on('click', function () {
        // Reset form
        $('#message-content').val('');
        $('#char-counter').text('0/1000');
        $('#message-errors').empty();
        openModal('#modal-message');
    });

    // ─── File Upload Preview ────────────────────────────────────────────────
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

    // ─── Edit Profile Form Submit ────────────────────────────────────────────
    $('#form-edit-profile').on('submit', function () {
        // submits normally to /edit-profile
    });

    // ─── Empty State Check ───────────────────────────────────────────────────
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
                initMeetupMap(null);
            });
        }
    }

    checkEmptyState();

    // ─── MazeMap Meetup Spot ─────────────────────────────────────────────────

    // [building number/code, building name]
    var UWA_BUILDINGS = [
        ['1', 'Winthrop Hall'],
        ['2', 'Undercroft'],
        ['3', 'Reid Library'],
        ['4', 'Main Administration Building'],
        ['5', 'Arts Building'],
        ['6', 'Social Sciences Building'],
        ['7', 'Education Building'],
        ['8', 'Law Building'],
        ['9', 'Economics & Commerce Building'],
        ['10', 'Business School'],
        ['11', 'Physics Building'],
        ['12', 'Chemistry Building'],
        ['13', 'Mathematics Building'],
        ['14', 'Computer Science & Software Engineering'],
        ['15', 'Civil, Environmental & Mining Engineering'],
        ['16', 'Mechanical Engineering'],
        ['17', 'Electrical, Electronic & Computer Engineering'],
        ['18', 'Engineering Library'],
        ['19', 'Biological Sciences'],
        ['20', 'Botany & Zoology Building'],
        ['21', 'Geography & Planning'],
        ['22', 'Psychology Building'],
        ['23', 'Architecture, Landscape & Visual Arts'],
        ['24', 'Medical & Dental Library'],
        ['25', 'Anatomy, Physiology & Human Biology'],
        ['26', 'Pharmacology'],
        ['27', 'Pathology Building'],
        ['28', 'Physiology Building'],
        ['29', 'Medical Research Foundation'],
        ['30', 'Public Health Building'],
        ['31', 'University Club'],
        ['32', 'Student Guild Building'],
        ['33', 'UniCentre'],
        ['34', 'Sports & Recreation Centre'],
        ['35', 'University Health Service'],
        ['36', 'Matilda Bay Reserve'],
        ['37', 'Lawrence Wilson Art Gallery'],
        ['38', 'Hackett Hall'],
        ['39', 'Shenton House'],
        ['40', 'Bayliss Building'],
        ['41', 'Barry J. Marshall Library'],
        ['42', 'Agriculture & Environment Building'],
        ['43', 'Indian Ocean Marine Research Centre'],
        ['44', 'Oceans Institute'],
        ['45', 'Tropical Medicine Research Centre'],
        ['46', 'Telethon Kids Institute'],
        ['47', 'EZONE UWA Student Hub'],
        ['48', 'The Refectory'],
        ['49', 'Clough Engineering Student Centre'],
        ['50', 'Forum'],
    ];

    var meetupMap = null;
    var meetupMarker = null;

    function cleanBuildingName(raw) {
        return raw.replace(/^\d+\s*[-–]\s*/, '').trim();
    }

    function placeMeetupMarker(lngLat) {
        if (meetupMarker) meetupMarker.remove();
        meetupMarker = new Mazemap.MazeMarker({
            color: '#003087',
            innerCircle: true,
            innerCircleColor: '#FFB81C',
            size: 36,
            innerCircleScale: 0.45,
            zLevel: 1
        }).setLngLat(lngLat).addTo(meetupMap);
    }

    function setMeetupSpot(name, lngLat) {
        $('#ad-location').val(name);
        $('#building-search').val(name);
        $('#building-suggestions').hide().attr('hidden', true).empty();
        if (lngLat && meetupMap) {
            placeMeetupMarker(lngLat);
            meetupMap.flyTo({ center: lngLat, zoom: 17 });
        }
    }

    function searchBuildingOnMap(query) {
        if (!meetupMap) return;
        $.getJSON('https://search.mazemap.com/search/equery/', {
            q: query,
            campusid: 309,
            rows: 1,
            srid: 4326
        }, function (data) {
            if (data.result && data.result.length > 0) {
                var r = data.result[0];
                var lngLat = {
                    lng: r.point.coordinates[0],
                    lat: r.point.coordinates[1]
                };
                placeMeetupMarker(lngLat);
                meetupMap.flyTo({ center: lngLat, zoom: 17 });
            }
        });
    }


    function initMeetupMap(prefillValue) {
        // Delay to let modal finish opening before map initialises
        setTimeout(function () {
            var container = document.getElementById('meetup-map');
            if (!container) return;

            if (meetupMap) {
                meetupMap.remove();
                meetupMap = null;
            }
            meetupMarker = null;

            // Reset meetup UI
            $('#building-search').val('');
            $('#meetup-selected').hide().attr('hidden', true);
            $('#meetup-selected-name').text('');
            $('#ad-location').val(prefillValue || '');
            $('#building-suggestions').hide().attr('hidden', true).empty();

            meetupMap = new Mazemap.Map({
                container: 'meetup-map',
                campuses: 309,
                center: { lng: 115.8175, lat: -31.9800 },
                zoom: 15,
                zLevel: 1
            });

            meetupMap.on('load', function () {
                if (prefillValue) {
                    $('#building-search').val(prefillValue);
                    searchBuildingOnMap(prefillValue);
                }
            });

            meetupMap.on('click', function (e) {
                var lngLat = e.lngLat;
                var zLevel = (meetupMap.zLevel !== undefined) ? meetupMap.zLevel : 1;
                // getPoiAt is the correct static method (not getPoiAtPoint)
                Mazemap.Data.getPoiAt(lngLat, zLevel)
                    .then(function (poi) {
                        if (!poi || !poi.properties) return;
                        var name = poi.properties.buildingName || poi.properties.name || poi.properties.title;
                        if (name && !name.toLowerCase().endsWith(' campus')) {
                            setMeetupSpot(cleanBuildingName(name), lngLat);
                        }
                    })
                    .catch(function () {});

            });
        }, 200);
    }

    // ─── Building Autocomplete ───────────────────────────────────────────────

    $('#building-search').on('input', function () {
        var raw = $(this).val();
        var q = raw.trim().toLowerCase();
        var $list = $('#building-suggestions');

        // If the user edits away from the confirmed value, invalidate the hidden field
        if (raw.trim() !== $('#ad-location').val()) {
            $('#ad-location').val('');
        }

        if (q.length < 1) {
            $list.hide().attr('hidden', true).empty();
            return;
        }

        var matches = UWA_BUILDINGS.filter(function (b) {
            return b[1].toLowerCase().indexOf(q) !== -1 || b[0].indexOf(q) !== -1;
        }).slice(0, 8);

        if (!matches.length) {
            $list.hide().attr('hidden', true).empty();
            return;
        }

        $list.empty();
        matches.forEach(function (b) {
            $('<li class="suggestion-item" tabindex="0"></li>')
                .append('<span class="suggestion-num">' + b[0] + '</span>')
                .append('<span class="suggestion-name">' + b[1] + '</span>')
                .on('mousedown', function (e) {
                    e.preventDefault(); // keep focus on input
                    setMeetupSpot(b[1], null);
                    searchBuildingOnMap(b[1]);
                })
                .appendTo($list);
        });

        $list.removeAttr('hidden').show();
    });

    $('#building-search').on('keydown', function (e) {
        var $items = $('#building-suggestions .suggestion-item:visible');
        var $active = $items.filter('.active');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            var $next = $active.length ? $active.removeClass('active').next('.suggestion-item') : $items.first();
            $next.addClass('active');
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            var $prev = $active.length ? $active.removeClass('active').prev('.suggestion-item') : $items.last();
            $prev.addClass('active');
        } else if (e.key === 'Enter' && $active.length) {
            e.preventDefault();
            $active.trigger('mousedown');
        } else if (e.key === 'Escape') {
            $('#building-suggestions').hide().attr('hidden', true);
        }
    });

    $('#building-search').on('blur', function () {
        // Short delay so mousedown on suggestion fires first
        setTimeout(function () {
            $('#building-suggestions').hide().attr('hidden', true);
        }, 150);
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.building-search-wrapper').length) {
            $('#building-suggestions').hide().attr('hidden', true);
        }
    });

});
