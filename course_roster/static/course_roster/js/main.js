/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, moment */
var CourseRoster = {};

CourseRoster.format_last_activity = function (date_str) {
    "use strict";
    return (date_str === null) ? "" : moment(date_str).format("MMM D [at] h:mma");
};

CourseRoster.format_total_activity = function (sec) {
    "use strict";
    return (sec === 0) ? "" : moment().startOf("day").seconds(sec).format("H:mm:ss");
};

Handlebars.registerHelper("format_last_activity", function (datetime) {
    "use strict";
    return CourseRoster.format_last_activity(datetime);
});
Handlebars.registerHelper("format_total_activity", function (sec) {
    "use strict";
    return CourseRoster.format_total_activity(sec);
});

(function ($) {
    "use strict";

    function loading_people(xhr) {
        var template = Handlebars.compile($("#loading-people-tmpl").html());
        $("#thumbnail-grid").html(template());
    
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
        }
    }

    function create_filters() {
        var api = $("#people-table").dataTable().api();
        $("#role-filter").on("change", function () {
            var val = $(this).val(),
                col = 4;
            api.column(col).search(val).draw();
        }).appendTo("#people-table_filter").show();
    }

    function draw_people(data) {
        var template = Handlebars.compile($("#thumbnail-grid-tmpl").html()),
            i,
            len,
            opt;

        $("#thumbnail-grid").html(template(data));

        for (i = 0, len = data.roles.length; i < len; i++) {
            opt = data.roles[i];
            $("<option>").attr("value", opt.role)
                         .text(opt.role + " (" + opt.count + ")")
                         .appendTo("#role-filter");
        }

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

    $(document).ready(function () {
        load_people();
    });
}(jQuery));
