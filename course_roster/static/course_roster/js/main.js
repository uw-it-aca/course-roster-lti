/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, moment */
(function ($) {
    "use strict";

    var photo_template;

    function loading_people(xhr) {
        $("span.loading").show();
        xhr.setRequestHeader("X-SessionId", window.course_roster.session_id);
    }

    function load_dummy() {
        $(this).attr("src", window.course_roster.nophoto_url);
    }

    function load_next_photo() {
        var el = $("a.person-photo:empty").first();
        if (el.length === 1) {
            $("<img/>").load(load_next_photo).error(load_dummy)
                       .appendTo(el).addClass("roster-thumbnail img-responsive")
                       .attr("src", el.attr("data-photo"));
        } else {
            $("span.loading").hide();
        }
    }

    function draw_people(data) {
        $("#thumbnail-grid").append(photo_template(data));
        load_next_photo();
    }

    function load_people() {
        $.ajax({
            url: "/roster/api/v1/roster",
            dataType: "json",
            beforeSend: loading_people,
            //error: ...
            success: draw_people
        });
    }

    function initialize() {
        photo_template = Handlebars.compile($("#thumbnail-grid-tmpl").html());
        load_people();
    }

    $(document).ready(function () {
        initialize();
    });
}(jQuery));
