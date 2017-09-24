import collections, traceback
import cache, entitys, json, time, db_util, settings, common


def get_chart_data_by_host_id(host_id):
    result = entitys.BaseClass(None)
    os_info = cache.Cache().get_linux_info(host_id)
    status_info = cache.Cache().get_status_info(host_id)
    repl_info = cache.Cache().get_repl_info(host_id)
    result.qps = status_info.qps
    result.tps = status_info.tps
    result.threads = status_info.threads_count
    result.threads_run = status_info.threads_run_count
    result.select = status_info.select_count
    result.insert = status_info.insert_count
    result.update = status_info.update_count
    result.delete = status_info.delete_count
    result.mysql_cpu = os_info.mysql_cpu
    result.mysql_mem = os_info.mysql_memory
    result.io_qps = os_info.io_qps
    result.io_tps = os_info.io_tps
    result.io_read = os_info.io_read
    result.io_write = os_info.io_write
    result.rpl_delay = repl_info.seconds_behind_master
    result.time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    if (hasattr(os_info, "cpu_1")):
        result.cpu_1 = os_info.cpu_1
        result.cpu_5 = os_info.cpu_5
        result.cpu_15 = os_info.cpu_15
        result.cpu_user = os_info.cpu_user
        result.cpu_system = os_info.cpu_system
        result.cpu_idle = os_info.cpu_idle
    else:
        result.cpu_1 = result.cpu_5 = result.cpu_15 = result.cpu_user = result.cpu_system = result.cpu_idle = 0
    return json.dumps(result, default=lambda o: o.__dict__)


def get_chart_history_data(host_id):
    pass


def get_chart_data(obj):
    chart_data = ChartData()
    host_id = int(obj.host_id)
    str_list = chart_options[int(obj.key)].attribute_names.split(":")
    data_type = int(str_list[-1])
    if (data_type == 1):
        set_chart_data(cache.Cache().get_status_info(host_id), str_list, chart_data)
    elif (data_type == 2):
        set_chart_data(cache.Cache().get_linux_info(host_id), str_list, chart_data)
    elif (data_type == 3):
        set_chart_data(cache.Cache().get_repl_info(host_id), str_list, chart_data)
    elif (data_type == 4):
        set_chart_data(cache.Cache().get_innodb_info(host_id), str_list, chart_data)
    chart_data.time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    return json.dumps(chart_data, default=lambda o: o.__dict__)


def set_chart_data(obj, str_list, chart_data):
    list_len = len(str_list) - 1
    if (list_len == 1):
        chart_data.data1 = getattr(obj, str_list[0])
    if (list_len == 2):
        chart_data.data1 = getattr(obj, str_list[0])
        chart_data.data2 = getattr(obj, str_list[1])
    if (list_len == 3):
        chart_data.data1 = getattr(obj, str_list[0])
        chart_data.data2 = getattr(obj, str_list[1])
        chart_data.data3 = getattr(obj, str_list[2])
    if (list_len == 4):
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


def get_chart_obj(title, attribute_names, legend=None):
    chart_obj = ChartData()
    chart_obj.title = title
    chart_obj.legend = legend
    chart_obj.attribute_names = attribute_names
    return chart_obj


def get_chart_option(key):
    return json.dumps(chart_options[key], default=lambda o: o.__dict__)


chart_options = collections.OrderedDict()
chart_options[1] = get_chart_obj("QPS", "qps:1")
chart_options[2] = get_chart_obj("TPS", "tps:1")
chart_options[3] = get_chart_obj("Trxs", "trxs:1")
chart_options[4] = get_chart_obj("Thread", "threads_count:threads_run_count:1", ["connected", "running"])
chart_options[5] = get_chart_obj("DML", "insert_count:update_count:delete_count:1", ["insert", "update", "delete"])
chart_options[6] = get_chart_obj("CPU Load", "cpu_1:cpu_5:cpu_15:2", ["CPU_1", "CPU_5", "CPU_15"])
chart_options[7] = get_chart_obj("CPU", "cpu_user:cpu_system:cpu_idle:2", ["user", "sys", "idle"])
chart_options[8] = get_chart_obj("IO Q/T", "io_qps:io_tps:2", ["qps", "tps"])
chart_options[9] = get_chart_obj("IO R/W", "io_read:io_write:2", ["read", "write"])
chart_options[10] = get_chart_obj("IO Util", "util:2", ["util"])
chart_options[11] = get_chart_obj("Repl Delay", "seconds_behind_master:3", ["delay"])
chart_options[12] = get_chart_obj("MySQL CPU", "mysql_cpu:2")
chart_options[13] = get_chart_obj("MySQL Mem", "mysql_memory:2")
chart_options[14] = get_chart_obj("MySQL Mem", "mysql_memory:2")


def get_chart_config_infos():
    result = collections.OrderedDict()
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host,
                                         """select t1.chart_id, t1.chart_title, t2.line_id, t2.line_name, t2.attr_name, t2.obj_id
                                            from mysql_web.chart_infos t1 left join mysql_web.line_infos t2 on t1.chart_id=t2.chart_id WHERE t1.is_deleted = 0
                                            ORDER by t1.weight asc, t1.chart_id ASC;"""):
        info = common.get_object(row)
        if (info.chart_id in result.keys()):
            result[chart_info.chart_id].line_infos.append(info)
            result[chart_info.chart_id].line_names.append(info.line_name)
        else:
            chart_info = entitys.Entity()
            chart_info.line_infos = []
            chart_info.line_names = []
            chart_info.chart_id = info.chart_id
            chart_info.chart_title = info.chart_title
            chart_info.line_infos.append(info)
            chart_info.line_names.append(info.line_name)
            result[chart_info.chart_id] = chart_info
    cache.Cache().chart_config = result
    return common.convert_obj_to_json_str(result.values())


def get_chart_data_by_config(host_id):
    result = []
    for chart_info in cache.Cache().chart_config.values():
        for line_info in chart_info.line_infos:
            data = entitys.Entity()
            data.line_id = line_info.line_id
            try:
                if (line_info.obj_id == 1):
                    data.value = getattr(cache.Cache().get_status_info(host_id), line_info.attr_name)
                elif (line_info.obj_id == 2):
                    data.value = getattr(cache.Cache().get_linux_info(host_id), line_info.attr_name)
                elif (line_info.obj_id == 3):
                    data.value = getattr(cache.Cache().get_repl_info(host_id), line_info.attr_name)
                elif (line_info.obj_id == 4):
                    data.value = getattr(cache.Cache().get_innodb_info(host_id), line_info.attr_name)
            except:
                data.value = 0
                traceback.print_exc()
            result.append(data)
    data = entitys.Entity()
    data.line_id = 0;
    data.value = time.strftime('%H:%M:%S', time.localtime(time.time()))
    result.append(data)
    return common.convert_obj_to_json_str(result)
