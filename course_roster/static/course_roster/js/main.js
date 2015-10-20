/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars */
(function ($) {
    "use strict";

    var photo_template,
        next_page,
        filter_search_term,
        filter_section_id;

    function loading_people(xhr) {
        $("span.loading").show();
        xhr.setRequestHeader("X-SessionId", window.course_roster.session_id);
    }

    function load_dummy() {
        $(this).attr("src", window.course_roster.nophoto_url);
    }

    function show_person() {
        // TODO: check the value of filter_section_id
        $(this).closest('div.person-container').show();
        load_next_photo();
    }

    function load_next_photo() {
        var el = $("a.person-photo:empty").first();
        if (el.length === 1) {
            $("<img/>").load(show_person).error(load_dummy)
                       .appendTo(el).addClass("roster-thumbnail img-responsive")
                       .attr("src", el.attr("data-photo"));
        } else {
            $("span.loading").hide();
            if (next_page) {
                load_course_people(window.course_roster.canvas_course_id);
            }
        }
    }

    function draw_people(data) {
        next_page = data.next_page;
        $("#thumbnail-grid").append(photo_template(data));
        load_next_photo();
    }

    function draw_error(xhr) {
        $("span.loading").hide();
        $("#thumbnail-grid").append("No photos");
    }

    function load_course_people(course_id) {
        var url = "api/v1/course/" + course_id + "/people",
            filter_params = {};

        if (next_page) {
            filter_params.page = next_page;
        }

        if (filter_search_term) {
            filter_params.search_term = filter_search_term;
            $("#thumbnail-grid").empty();
        }

        if (!$.isEmptyObject(filter_params)) {
            url += "?" + $.param(filter_params);
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

    function filter_by_section() {
        filter_section_id = $(this).val();

        $(".person-container").show();
        if (filter_section_id) {
            $(".person-container:not([data-sections*='" + filter_section_id + "'])")
                .hide();
        }
    }

    function filter_by_search() {
        var course_id = window.course_roster.canvas_course_id,
            search_term = $.trim($(this).val());

        if (search_term.length === 0 || search_term.length > 2) {
            $(this).val(search_term);
            filter_search_term = search_term;
            load_course_people(course_id);
        } else {
            filter_search_term = null;
        }
    }

    function loading_sections(xhr) {
        xhr.setRequestHeader("X-SessionId", window.course_roster.session_id);
    }

    function draw_section_selector(data) {
        var template = Handlebars.compile($("#section-filter-tmpl").html());
        if (data.sections.length > 1) {
            $("#section-filter").html(template(data));
            $("#course-section-selector").change(filter_by_section);
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
