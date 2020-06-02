if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
}
  
function recur_options() {
    type = document.getElementById("types").value;
    if(type == "dates_both"){
        document.getElementById("start_date").style.display = "block";
        document.getElementById("end_date").style.display = "block";
        document.getElementById("date_options_div").style.display = "block";
        document.getElementById("recur_days").style.display = "table";
        document.getElementById("count").style.display = "none";
        date_visibility();
    }
    else if(type == "dates_mix"){
        document.getElementById("start_date").style.display = "block";
        document.getElementById("end_date").style.display = "none";
        document.getElementById("date_options_div").style.display = "block";
        document.getElementById("recur_days").style.display = "table";
        document.getElementById("count").style.display = "block";
        date_visibility();
    }
    else if(type == "number"){
        document.getElementById("start_date").style.display = "none";
        document.getElementById("end_date").style.display = "none";
        document.getElementById("date_options_div").style.display = "none";
        document.getElementById("recur_days").style.display = "none";
        document.getElementById("count").style.display = "block";
        // Put all dates back in
        // select = document.getElementById("date_options");
        // for(i = 0; i < select.options.length; i++){
        //     document.getElementById(select.options[i].value).style.display = "block";
        // }
    }
}

function date_visibility() {
    select = document.getElementById("date_options");
    value = select.value;
    for(i = 0; i < select.options.length; i++){
        // console.log(select.options[i].value)
        if(select.options[i].value == value){
            document.getElementById(select.options[i].value).style.display = "none";
        }
        else{
            document.getElementById(select.options[i].value).style.display = "block";
        }
    }
}