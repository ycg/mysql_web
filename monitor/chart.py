import cache, base_class, json, time

def get_chart_data_by_host_id(host_id):
    result = base_class.BaseClass(None)
    os_info = cache.Cache().get_linux_info(host_id)
    status_info = cache.Cache().get_status_info(host_id)
    result.qps = status_info.qps
    result.tps = status_info.tps
    result.threads = status_info.threads_count
    result.select = status_info.select_count
    result.insert = status_info.insert_count
    result.update = status_info.update_count
    result.delete = status_info.delete_count
    result.time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    if(hasattr(os_info, "cpu_1")):
        result.cpu_1 = os_info.cpu_1
        result.cpu_5 = os_info.cpu_5
        result.cpu_15 = os_info.cpu_15
        result.cpu_user = os_info.cpu_user
        result.cpu_system = os_info.cpu_system
        result.cpu_idle = os_info.cpu_idle
    else:
        result.cpu_1 = result.cpu_5 = result.cpu_15 = result.cpu_user = result.cpu_system = result.cpu_idle = 0
    return json.dumps(result, default=lambda o: o.__dict__)

def get_chart_data(obj):
    chart_data = ChartData()
    host_id = int(obj.host_id)
    str_list = obj.attribute_names.split(":")
    data_type = int(str_list[-1])
    if(data_type == 1):
        set_chart_data(cache.Cache().get_status_info(host_id), str_list, chart_data)
    elif(data_type == 2):
        set_chart_data(cache.Cache().get_linux_info(host_id), str_list, chart_data)
    elif(data_type == 3):
        set_chart_data(cache.Cache().get_repl_info(host_id), str_list, chart_data)
    elif(data_type == 4):
        set_chart_data(cache.Cache().get_innodb_info(host_id), str_list, chart_data)
    chart_data.time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    return json.dumps(chart_data, default=lambda o: o.__dict__)

def set_chart_data(obj, str_list, chart_data):
    list_len = len(str_list) - 1
    if(list_len == 1):
        chart_data.data1 = getattr(obj, str_list[0])
    if(list_len == 2):
        chart_data.data1 = getattr(obj, str_list[0])
        chart_data.data2 = getattr(obj, str_list[1])
    if(list_len == 3):
        chart_data.data1 = getattr(obj, str_list[0])
        chart_data.data2 = getattr(obj, str_list[1])
        chart_data.data3 = getattr(obj, str_list[2])
    if(list_len == 4):
        chart_data.data1 = getattr(obj, str_list[0])
        chart_data.data2 = getattr(obj, str_list[1])
        chart_data.data3 = getattr(obj, str_list[2])
        chart_data.data4 = getattr(obj, str_list[3])
    return chart_data


class ChartData():
    def __init__(self):
        self.data1 = 0
        self.data2 = 0
        self.data3 = 0
        self.data4 = 0
