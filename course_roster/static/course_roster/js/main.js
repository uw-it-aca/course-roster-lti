/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars */
(function ($) {
    "use strict";

    Handlebars.registerHelper('nonbreaking', function (text) {
        return text.replace(/ /g, '\u00a0');
    });

    var photo_template,
        next_page,
        image_size = '120',
        nophoto_url = 'https://www.gravatar.com/avatar/' +
            '00000000000000000000000000000000?s=' + image_size + '&d=mm&f=y',
        filter_search_term,
        filter_section_id;

    function loading_people(xhr) {
        $('.loading').show();
        xhr.setRequestHeader('X-SessionId', window.course_roster.session_id);
    }

    function load_avatar() {
        /*jshint validthis: true */
        var avatar_url = $(this).closest('a.person-photo').attr('data-avatar');
        if (!avatar_url.length) {
            avatar_url = nophoto_url;
        }
        $(this).attr('src', avatar_url);
    }

    function show_person() {
        /*jshint validthis: true */
        if (filter_section_id &&
                $(this).attr('data-sections').indexOf(filter_section_id) === -1) {
            $(this).addClass('hidden');
        } else if (filter_search_term &&
                $(this).attr('data-names').indexOf(filter_search_term) === -1) {
            $(this).addClass('hidden');
        } else {
            $(this).find('span.name,span.login-id').removeHighlight();
            if (filter_search_term) {
                $(this).find('span.name,span.login-id')
                       .highlight(filter_search_term);
            }
            $(this).removeClass('hidden');
        }
    }

    function image_loaded() {
        /*jshint validthis: true */
        show_person.call($(this).closest('div.person-container'));
        load_next_photo();
    }

    function load_next_photo() {
        var el = $('a.person-photo:empty').first();
        if (el.length === 1) {
            $('<img/>').load(image_loaded).error(load_avatar)
                       .appendTo(el).attr('src', el.attr('data-photo'));
        } else {
            $('.loading').hide();
            if (next_page) {
                load_course_people(window.course_roster.canvas_course_id);
            }
        }
    }

    function draw_people(data) {
        next_page = data.next_page;
        $('#thumbnail-grid').append(photo_template(data));
        load_next_photo();

        if (next_page === null && $('.person-container').length === 0) {
            $('#filter-none').removeClass('hidden')
                             .find('p').text('No students in this course');
        }
    }

    function draw_error(xhr) {
        $('.loading').hide();
    }

    function load_course_people(course_id) {
        var url = "api/v1/course/" + course_id +
            "/people?image_size=" + image_size;

        if (next_page) {
            url += "&page=" + next_page;
        }

        $.ajax({
            type: "GET",
            url: url,
            dataType: "json",
            beforeSend: loading_people,
            error: draw_error,
            success: draw_people
        });
    }

    function filter_people() {
        $('#filtering').removeClass('hidden');
        setTimeout(function () {
            $('.person-container').each(show_person);
            $('#filtering').addClass('hidden');
            if ($('.person-container').filter(':visible').length === 0) {
                $('#filter-none').removeClass('hidden');
            } else {
                $('#filter-none').addClass('hidden');
            }
        }, 500);
    }

    function filter_by_section() {
        /*jshint validthis: true */
        var section_id = $(this).val();
        filter_section_id = (section_id.length) ? section_id : null;
        filter_people();
    }

    function filter_by_search() {
        /*jshint validthis: true */
        var search_term = $.trim($(this).val());
        $(this).val(search_term);
        filter_search_term = (search_term.length > 0) ? search_term.toLowerCase() : null;
        filter_people();
    }

    function loading_sections(xhr) {
        xhr.setRequestHeader('X-SessionId', window.course_roster.session_id);
    }

    function draw_section_selector(data) {
        var template = Handlebars.compile($('#section-filter-tmpl').html());
        if (data.sections.length > 1) {
            $('#search-filter').after(template(data));
            $('#section-filter').change(filter_by_section);
        }
    }

    function load_course_sections(course_id) {
        $.ajax({
            type: "GET",
            url: "api/v1/course/" + course_id + "/sections",
            dataType: "json",
            beforeSend: loading_sections,
            success: draw_section_selector
        });
    }

    function initialize() {
        var course_id = window.course_roster.canvas_course_id;

        photo_template = Handlebars.compile($("#thumbnail-grid-tmpl").html());
        $("#search-filter").keyup(filter_by_search);
        load_course_sections(course_id);
        load_course_people(course_id);
    }

    $(document).ready(initialize);
}(jQuery));
