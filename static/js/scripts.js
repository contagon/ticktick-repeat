if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
}

function recur_options() {
    type = document.getElementById("types").value;
    if(type == "dates_both"){
        document.getElementById("start_date").style.display = "block";
        document.getElementById("end_date").style.display = "block";
        document.getElementById("dueDate_div").style.display = "none";
        document.getElementById("recur_days").style.display = "block";
        document.getElementById("count").style.display = "none";
    }
    else if(type == "dates_mix"){
        document.getElementById("start_date").style.display = "block";
        document.getElementById("end_date").style.display = "none";
        document.getElementById("dueDate_div").style.display = "none";
        document.getElementById("recur_days").style.display = "block";
        document.getElementById("count").style.display = "block";
    }
    else if(type == "number"){
        document.getElementById("start_date").style.display = "none";
        document.getElementById("end_date").style.display = "none";
        document.getElementById("dueDate_div").style.display = "block";
        document.getElementById("recur_days").style.display = "none";
        document.getElementById("count").style.display = "block";
    }
}

function toggle(source) {
    var checkboxes = document.querySelectorAll('#single_day');
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i] != source)
            checkboxes[i].checked = source.checked;
    }
}

// Runs all functions for first time, initializes timezone
window.onload = function() {
    recur_options();
    document.getElementById("timezone").value = jstz.determine().name();
};
