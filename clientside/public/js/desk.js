$(document).ready(function() {
    setTimeout(function() {
        $("button.btn.btn-default.btn-sm").filter(function() {
            return $(this).text().trim() === "Watch Tutorial";
        }).hide();

    }, 3000); 
});
