import paramiko, db_util, settings

class TableInfo():
    diff = 0
    value = 0
    file_size = 0
    free_size = 0

def get_table_infos(host_info):
    table_infos = {}
    sql = "select table_schema, table_name, DATA_LENGTH, INDEX_LENGTH, TABLE_ROWS, AUTO_INCREMENT from information_schema.tables " \
          "where table_schema != 'mysql' and table_schema != 'information_schema' and table_schema != 'performance_schema'";
    for row in db_util.DBUtil().fetchall(host_info, sql):
        table_info = TableInfo()
        table_info.schema = row["table_schema"]
        table_info.t_name = row["table_name"]
        table_info.rows = row["TABLE_ROWS"]
        table_info.data_size = row["DATA_LENGTH"]
        table_info.index_size = row["INDEX_LENGTH"]
        table_info.auto_increment = row["AUTO_INCREMENT"] if row["AUTO_INCREMENT"] else 0
        table_info.total_size = long(table_info.data_size) + long(table_info.index_size)
        table_name = row["table_schema"] + "." + row["table_name"]
        table_infos[table_name] = table_info
    return table_infos

def get_data_length(data_length):
    value = float(1024)
    if(data_length > value):
        result = round(data_length / value, 0)
        if(result > value):
            return str(int(round(result / value, 0))) + "M"
        else:
            return str(int(result)) + "K"
    else:
        return str(data_length) + "KB"

def get_tablespace_infos(host_info):
    table_infos = get_table_infos(host_info)
    host_client = paramiko.SSHClient()
    host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host_client.connect(host_info.host, port=22, username="root")

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
                table_info.data_size_o = table_info.data_size
                table_info.index_size_o = table_info.index_size
                table_info.total_size_o = table_info.total_size
                table_info.file_size_o = table_info.file_size
                convert_bytes(table_info)

    host_client.close()
    insert_tablespace_data(host_info, table_infos.values())
    return sorted(table_infos.values(), cmp=lambda x,y:cmp(x.free_size, y.free_size), reverse=True)

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
    value_list = []
    value_format = "({0},'{1}','{2}',{3},{4},{5},{6},{7},{8},date(now()))"
    sql = "insert into mysql_web.mysql_data_size_log (host_id, `schema`, table_name, data_size, index_size, rows, auto_increment, file_size, free_size, `date`) values"
    for table_info in table_infos:
        value_list.append(value_format.format(host_info.key, table_info.schema, table_info.t_name, table_info.data_size_o, table_info.index_size_o,
                                              table_info.rows, table_info.auto_increment, table_info.file_size_o, table_info.free_size))
    sql = sql + ','.join(value_list) + ";"
    db_util.DBUtil().execute(settings.MySQL_Host, sql)

'''
def analysis_table_data(host_info):
    sql = "insert into mysql_web.mysql_data_size_for_day (host_id, data_size_incr)" \
          "select sum(data_size), sum(index_size), sum(rows), sum(auto_increment), sum(file_size), sum(diff) from mysql_web.mysql_data_size_log" \
          "where host_id={0} group by `date`;".format(host_info.key)'''

