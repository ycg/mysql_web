var timer = "";
var host_ids = new Array();
var my_url = "/mysql";

var post_url = ["/mysql", "/status", "/innodb", "/replication", "/os"]

function myrefresh() {
    if ($.inArray(my_url, post_url) >= 0) {
        $.post(my_url, {"keys": JSON.stringify(host_ids)}, function (data) {
            var login_flag = data.substring(0, 25);
            if (login_flag == "<p hidden>login_error</p>") {
                window.location.href = 'login';
            }
            else {
                $("#data").html(ungzip_new(data));
            }
        });

        /*$.post(my_url, {"keys": JSON.stringify(host_ids)}).success(function (data, status, xhr) {
         console.log(xhr);
         $("#data").html(ungzip_new(data));
         }).success(function (data, status, xhr) {
         console.log(xhr);
         });*/
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

function show_modal_dialog(id_name) {
    $(id_name).modal("show")
}

function hide_modal_dialog(id_name) {
    $(id_name).modal("hide")
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
    timer = setInterval(myrefresh, interval_refresh)
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

var id_names = ["sql", "slowlog", "tablespace", "general", "user", "thread", "chart", "config", "backup", "mysql_log", "chart_new", "host", "binlog", "alarm"]

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
    if (host_ids == null || host_ids == 0) {
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

function ajaxSubmit(frm, fn, efn) {
    var dataPara = get_form_json(frm);
    $.ajax({
        url: frm.action,
        type: frm.method,
        data: dataPara,
        success: fn,
        error: efn
    });
}

function get_form_json(frm) {
    var o = {};
    var a = $(frm).serializeArray();
    $.each(a, function () {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
}

$(function () {
    $(document).on('click', '.accordion-toggle', function (event) {
        event.stopPropagation();
        var $this = $(this);
        var parent = $this.data('parent');
        var actives = parent && $(parent).find('.collapse.in');

        // From bootstrap itself
        if (actives && actives.length) {
            actives.data('collapse');
            actives.collapse('hide');
        }

        var target = $this.attr('data-target') || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, ''); //strip for ie7
        $(target).collapse('toggle');
    });
})

function changeFeedback(id) {
    var str = document.getElementById(id).className;
    var tag = str.substring(25, str.length);
    if (tag == "right") {
        document.getElementById(id).className = "glyphicon glyphicon-menu-down";
    } else {
        document.getElementById(id).className = "glyphicon glyphicon-menu-right";
    }
}

$("button[type='reset']").click(function () {
    $('input').attr("value", '');
    $("textarea").val("");
    $("select.selectpicker").each(function () {
        $(this).selectpicker('val', $(this).find('option:first').val());
        $(this).find("option").attr("selected", false);
        $(this).find("option:first").attr("selected", true);
        $(this).val(0)
    });
});

function skip_slave_error(host_id) {

}

function kill_mysql_thread_id(host_id, thread_id) {
    if (window.confirm("确认kill掉?")) {
        $.post("/mysql/kill/" + host_id + "/" + thread_id, "", function (data) {
            alert(data);
            myrefresh();
        });
    }
}

function post_request(url, json_data) {
    $.post(url, json_data, function (data) {
        alert(data)
    });
}

function logout() {
    if (window.confirm("是否确认退出?")) {
        $.post("/logout", "", function (data) {
            alert("logout ok!")
        });
    }
}

function input_data_for_post(url, json_data, div_id) {
    $.post(url, json_data, function (data) {
        $(div_id).html(data)
    });
}

