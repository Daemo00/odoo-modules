odoo.define("website_event_tournament.attendee_details", function () {
    "use strict";

    function my_func() {
        alert("hi");
    }

    $(document).ready(function () {
        // Does not bind because modal does not exist when document is ready: when is it populated?
        $("#attendee_registration button[name='js_copy_team']").on(
            "click",
            function () {
                alert("hi");
            }
        );
    });
});
