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
        $("#people-table tbody").html(template());
    }

    function load_dummy() {
        $(this).attr("src", window.course_roster.dummy_avatar);
    }

    function load_next_avatar() {
        var el = $("a.avatar:empty").first();
        if (el.length === 1) {
            $("<img/>").load(load_next_avatar).error(load_dummy)
                       .appendTo(el).attr("src", el.attr("data-avatar"));
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
        var template = Handlebars.compile($("#people-table-tmpl").html()),
            i,
            len,
            opt;

        $("#people-table tbody").html(template(data));

        for (i = 0, len = data.roles.length; i < len; i++) {
            opt = data.roles[i];
            $("<option>").attr("value", opt.role)
                         .text(opt.role + " (" + opt.count + ")")
                         .appendTo("#role-filter");
        }

        $("#people-table").dataTable({
            "aaSorting": [[ 0, "asc" ]],
            "bPaginate": true,
            "iDisplayLength": 25,
            "bScrollCollapse": true,
            "initComplete": create_filters,
            "order": [[ 1, "asc" ]],
            "columns": [{ "orderable": false, "searchable": false },
                null, null, null, null, null, null]
        }).on("draw.dt", load_next_avatar);

        load_next_avatar();
    }

    function load_people() {
        $.ajax({
            url: "/people/api/v1/people",
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
