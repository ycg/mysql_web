# -*- coding: utf-8 -*-

import paramiko, time
import db_util, settings, cache

B = 1024
KB = B * 1024
M = KB * 1024
G = M * 1024
T = G * 1024

Table_Page_Size = 20

class TableInfo():
    def __init__(self):
        pass

    diff = 0
    value = 0
    file_size = 0
    free_size = 0
    rows_o = 0
    data_size_o = 0
    index_size_o = 0
    total_size_o = 0
    file_size_o = 0

def get_table_infos(host_info):
    table_infos = {}
    sql = "select table_schema, table_name, DATA_LENGTH, INDEX_LENGTH, TABLE_ROWS, AUTO_INCREMENT, create_time, engine, update_time " \
          "from information_schema.tables " \
          "where table_schema != 'mysql' and table_schema != 'information_schema' and table_schema != 'performance_schema' and table_schema != 'sys'";
    for row in db_util.DBUtil().fetchall(host_info, sql):
        table_info = TableInfo()
        table_info.schema = row["table_schema"]
        table_info.t_name = row["table_name"]
        table_info.rows = row["TABLE_ROWS"]
        table_info.data_size = row["DATA_LENGTH"] if row["DATA_LENGTH"] else 0
        table_info.index_size = row["INDEX_LENGTH"] if row["INDEX_LENGTH"] else 0
        table_info.auto_increment = row["AUTO_INCREMENT"] if row["AUTO_INCREMENT"] else 0
        table_info.total_size = long(table_info.data_size) + long(table_info.index_size)
        table_info.create_time = row["create_time"]
        table_info.update_time = row["update_time"] if row["update_time"] else ''
        #table_info.has_primary_key = check_table_has_primary_key(table_info.schema, table_info.t_name)
        table_name = row["table_schema"] + "." + row["table_name"]
        table_infos[table_name] = table_info
    return table_infos

def check_table_has_primary_key(table_schema, table_name):
    sql = "select count(1) as row_count from information_schema.COLUMNS where table_schema='{0}' and table_name='{1}' and column_key='PRI'".format(table_schema, table_name)
    result = db_util.DBUtil().fetchone(settings.MySQL_Host, sql)
    if(result == None):
        return False
    elif(int(result["row_count"]) == 1):
        return True
    return False

def get_data_length(data_length):
    if(data_length < B):
        return str(data_length) + "B"
    elif(data_length < KB):
        return str(int(data_length / B)) + "KB"
    elif(data_length < M):
        return str(int(data_length / KB)) + "M"
    elif(data_length < G):
        return str(round(float(data_length) / float(M), 2)) + "G"
    elif(data_length < T):
        return str(round(float(data_length) / float(G), 2)) + "T"

def get_tablespace_infos(host_info):
    print(host_info.remark, "start check tablespace")
    result_lst = []
    table_infos = get_table_infos(host_info)
    host_client = paramiko.SSHClient()
    host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host_client.connect(host_info.host, port=host_info.ssh_port, username="root")

    shell = "du -ab {0} | grep ibd".format(host_info.mysql_data_dir)
    stdin, stdout, stderr = host_client.exec_command(shell)
    result = stdout.readlines()
    if(len(result) > 0):
        for line in result:
            table_name, file_size = get_table_name_and_file_size(line.replace("\n", ""))
            if(table_infos.has_key(table_name) == True):
                table_info = table_infos[table_name]
                table_info.file_size = file_size
                table_info.diff = table_info.file_size - table_info.total_size
                table_info.free_size = table_info.diff
                table_info.rows_o = table_info.rows
                table_info.data_size_o = table_info.data_size
                table_info.index_size_o = table_info.index_size
                table_info.total_size_o = table_info.total_size
                table_info.file_size_o = table_info.file_size
                result_lst.append(table_info)
                convert_bytes(table_info)

    host_client.close()
    sum_tablespace_info(host_info, result_lst)
    insert_tablespace_data(host_info, result_lst)
    insert_host_tablespace_data(cache.Cache().get_tablespace_info(host_info.host_id))
    print(host_info.remark, "ok")

def sum_tablespace_info(host_info, table_infos):
    table_count = 0
    rows_total = 0
    data_total = 0
    index_total = 0
    file_total = 0
    free_total = 0
    tablespace_info = cache.Cache().get_tablespace_info(host_info.key)
    tablespace_info.detail = sorted(table_infos, cmp=lambda x,y:cmp(x.free_size, y.free_size), reverse=True)
    for info in table_infos:
        table_count += 1
        rows_total = info.rows_o + rows_total
        data_total = info.data_size_o + data_total
        index_total = info.index_size_o + index_total
        file_total = info.file_size_o + file_total
        free_total = info.free_size + free_total
    tablespace_info.rows_total = rows_total
    tablespace_info.table_count = table_count
    tablespace_info.data_total = get_data_length(data_total)
    tablespace_info.index_total = get_data_length(index_total)
    tablespace_info.file_total = get_data_length(file_total)
    tablespace_info.free_total = get_data_length(free_total)
    tablespace_info.total = get_data_length(data_total + index_total)
    tablespace_info.data_total_o = data_total
    tablespace_info.index_total_o = index_total
    tablespace_info.file_total_o = file_total
    tablespace_info.free_total_o = free_total
    tablespace_info.total_o = data_total + index_total
    tablespace_info.last_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

def get_table_name_and_file_size(value):
    lst = value.split("/")
    file_zie = long(lst[0])
    table_name = lst[-2] + "." + lst[-1].replace(".ibd", "")
    return table_name, file_zie

def convert_bytes(table_info):
    table_info.data_size = get_data_length(table_info.data_size)
    table_info.index_size = get_data_length(table_info.index_size)
    table_info.total_size = get_data_length(table_info.total_size)
    table_info.file_size = get_data_length(table_info.file_size)
    table_info.diff = get_data_length(table_info.diff)

def insert_tablespace_data(host_info, table_infos):
    if(len(table_infos) <= 0):
        return
    value_list = []
    value_format = "({0},'{1}','{2}',{3},{4},{5},{6},{7},{8},{9},date(now()))"
    sql = "insert into mysql_web.mysql_data_size_log (host_id, `schema`, table_name, data_size, total_size, index_size, rows, auto_increment, file_size, free_size, `date`) values"
    for table_info in table_infos:
        value_list.append(value_format.format(host_info.key, table_info.schema, table_info.t_name, table_info.data_size_o, table_info.index_size_o, table_info.total_size_o,
                                              table_info.rows_o, table_info.auto_increment, table_info.file_size_o, table_info.free_size))
    sql = sql + ','.join(value_list) + ";"
    db_util.DBUtil().execute(settings.MySQL_Host, sql)

def insert_host_tablespace_data(info):
    sql = "insert into mysql_web.mysql_data_total_size_log " \
          "(host_id, rows_t, data_t, index_t, all_t, file_t, free_t, table_count, `date`) " \
          "values " \
          "({0},{1},{2},{3},{4},{5},{6},{7},date(now()));"
    sql = sql.format(info.host_info.key, info.rows_total, info.data_total_o,
                     info.index_total_o, info.total_o, info.file_total_o, info.free_total_o, info.table_count)
    db_util.DBUtil().execute(settings.MySQL_Host, sql)

def sort_tablespace(sort_type):
    infos = cache.Cache().get_all_tablespace_infos()
    if(sort_type == 1):
        return sorted(infos, cmp=lambda x, y: cmp(x.rows_total, y.rows_total), reverse=True)
    elif(sort_type == 2):
        return sorted(infos, cmp=lambda x, y: cmp(x.data_total_o, y.data_total_o), reverse=True)
    elif(sort_type == 3):
        return sorted(infos, cmp=lambda x, y: cmp(x.index_total_o, y.index_total_o), reverse=True)
    elif(sort_type == 4):
        return sorted(infos, cmp=lambda x, y: cmp(x.total_o, y.total_o), reverse=True)
    elif(sort_type == 5):
        return sorted(infos, cmp=lambda x, y: cmp(x.file_total_o, y.file_total_o), reverse=True)
    else:
        return sorted(infos, cmp=lambda x, y: cmp(x.free_total_o, y.free_total_o), reverse=True)

def sort_tablespace_by_host_id(host_id, sort_type, page_number, table_name):
    start_index = (page_number - 1) * Table_Page_Size
    stop_index = start_index + Table_Page_Size
    infos = cache.Cache().get_tablespace_info(host_id).detail
    if(sort_type == 1):
        result_table_list = sorted(infos, cmp=lambda x, y: cmp(x.rows_o, y.rows_o), reverse=True)
    elif(sort_type == 2):
        result_table_list = sorted(infos, cmp=lambda x, y: cmp(x.data_size_o, y.data_size_o), reverse=True)
    elif(sort_type == 3):
        result_table_list = sorted(infos, cmp=lambda x, y: cmp(x.index_size_o, y.index_size_o), reverse=True)
    elif(sort_type == 4):
        result_table_list = sorted(infos, cmp=lambda x, y: cmp(x.total_size_o, y.total_size_o), reverse=True)
    elif(sort_type == 5):
        result_table_list = sorted(infos, cmp=lambda x, y: cmp(x.file_size_o, y.file_size_o), reverse=True)
    else:
        result_table_list = sorted(infos, cmp=lambda x, y: cmp(x.free_size, y.free_size), reverse=True)

    if(len(table_name) > 0):
        result_table_list = search_table(result_table_list, table_name)

    return result_table_list[start_index: stop_index]

def search_table(table_infos, table_name):
    result = []
    for info in table_infos:
        if(table_name in info.t_name):
            result.append(info)
    return result

#region get table detail

def get_table_info(host_id, table_schema, table_name):
    infos = cache.Cache().get_tablespace_info(host_id).detail
    for table_info in infos:
        if(table_info.schema == table_schema and table_info.t_name == table_name):
            table_info.index_infos = get_table_indexs(host_id, table_schema, table_name)
            table_info.column_infos = get_table_columns(host_id, table_schema, table_name)
            return table_info
    return None

def get_table_indexs(host_id, table_schema, table_name):
    sql = """select index_name, non_unique, seq_in_index, column_name, collation, cardinality, nullable, index_type
             from information_schema.STATISTICS
             where table_schema = '{0}' and table_name = '{1}';""".format(table_schema, table_name)
    return db_util.DBUtil().get_list_infos(cache.Cache().get_host_info(host_id), sql)

def get_table_columns(host_id, table_schema, table_name):
    sql = """select column_name, ordinal_position, column_default, is_nullable, column_type, column_key, extra
             from information_schema.COLUMNS
             where table_schema = '{0}' and table_name = '{1}';""".format(table_schema, table_name)
    return db_util.DBUtil().get_list_infos(cache.Cache().get_host_info(host_id), sql)

#endregion

'''
def analysis_table_data(host_info):
    sql = "insert into mysql_web.mysql_data_size_for_day (host_id, data_size_incr)" \
          "select sum(data_size), sum(index_size), sum(rows), sum(auto_increment), sum(file_size), sum(diff) from mysql_web.mysql_data_size_log" \
          "where host_id={0} group by `date`;".format(host_info.key)'''
