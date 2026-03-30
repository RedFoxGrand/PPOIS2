function toggleLibFields() {
    var action = document.getElementById("lib_action").value;
    var extraFields = document.getElementById("lib_extra");
    var studentSelect = document.getElementById("lib_student");

    if (action === "add_book") {
        extraFields.style.display = "block";
        studentSelect.style.display = "none";
        studentSelect.required = false;
    } else {
        extraFields.style.display = "none";
        studentSelect.style.display = "block";
        studentSelect.required = true;
    }
}