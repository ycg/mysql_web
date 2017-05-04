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