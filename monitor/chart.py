import cache, base_class, json, time

def get_chart_data_by_host_id(host_id):
    result = base_class.BaseClass(None)
    os_info = cache.Cache().get_linux_info(host_id)
    status_info = cache.Cache().get_status_infos(host_id)
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
