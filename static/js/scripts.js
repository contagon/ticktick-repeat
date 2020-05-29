if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
}
  
function recur_options() {
    type = document.getElementById("types").value
    if(type == "dates_both"){
        document.getElementById("start_date").style.display = "block";
        document.getElementById("end_date").style.display = "block";
        document.getElementById("recur_days").style.display = "table";
        document.getElementById("count").style.display = "none";
        document.getElementById("recur_settings").className = "grid-container halves"
    }
    else if(type == "dates_mix"){
        document.getElementById("start_date").style.display = "block";
        document.getElementById("end_date").style.display = "none";
        document.getElementById("recur_days").style.display = "table";
        document.getElementById("count").style.display = "block";
        document.getElementById("recur_settings").className = "grid-container halves"
    }
    else if(type == "number"){
        document.getElementById("start_date").style.display = "none";
        document.getElementById("end_date").style.display = "none";
        document.getElementById("recur_days").style.display = "none";
        document.getElementById("count").style.display = "block";
        document.getElementById("recur_settings").className = "grid-container full"
    }
}