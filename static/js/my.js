var timer = "";
var host_ids = new Array();
var my_url = "/mysql";

var post_url = ["/mysql", "/status", "/innodb", "/replication", "/os"]

function myrefresh() {
    if ($.inArray(my_url, post_url) >= 0) {
        $.post(my_url, {"keys":JSON.stringify(host_ids)}, function (data){
            $("#data").html(ungzip_new(data));
        });
    }
    else {
        $.get(my_url, "", function (data) {
            $("#data").html(data);
        });
    }
}

function get_data(url) {
    var result_data = "";
    $.get(url, "", function (data) {
        result_data = data;
    });
    return result_data
}

function post_data(url, input_data) {
    var result_data = "";
    $.post(url, {"keys": input_data}, function (data) {
        result_data = data
    });
    return result_data
}

function stop(parameter, id_name) {
    search_div(id_name)
    myActive(id_name)
    my_url = parameter
    myrefresh()
    stop_timer()
}

function start(parameter, id_name) {
    search_div(id_name)
    myActive(id_name)
    my_url = parameter
    myrefresh()
    start_timer()
}

function start_timer() {
    stop_timer()
    timer = setInterval(myrefresh, 2000)
}

function stop_timer() {
    clearInterval(timer)
}

myrefresh()
start_timer()

function myActive(id_name) {
    if (id_name == "") {
        return false
    }
    $("#myTab").find("a").each(function () {
        if ($(this).attr("id") == id_name) {
            $(this).addClass("active");
        } else {
            $(this).removeClass("active");
        }
    });
}

var id_names = ["sql", "slowlog", "tablespace", "general", "user", "thread", "chart"]

function search_div(id_name) {
    if ($.inArray(id_name, id_names) >= 0) {
        $("#host_search_div").hide();
    }
    else {
        $("#host_search_div").show();
    }
    //$("#host_search_div").hide()
}

function set_select_ids() {
    host_ids = $("#host_search").val();
    if(host_ids == null || host_ids == 0){
       host_ids = new Array();
    }
}

function reset_select_ids() {
    $("#host_search").each(function () {
        $(this).selectpicker('val', $(this).find('option:first').val());
        $(this).find("option").attr("selected", false);
        $(this).find("option:first").attr("selected", true);
    });
    host_ids = new Array()
}

function gzip_new(string) {
    var charData = string.split('').map(function (x) {
        return x.charCodeAt(0);
    });
    var binData = new Uint8Array(charData);
    var data = pako.gzip(binData);
    var strData = String.fromCharCode.apply(null, new Uint16Array(data));
    return btoa(strData);
}

function ungzip_new(string) {
    var strData = atob(string);
    var charData = strData.split('').map(function (x) {
        return x.charCodeAt(0);
    });
    var binData = new Uint8Array(charData);
    var data = pako.ungzip(binData);
    var strData = String.fromCharCode.apply(null, new Uint16Array(data));
    return strData;
}