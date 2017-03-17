import paramiko, host_info, db_util

class TableInfo():
    diff = 0
    value = 0
    file_size = 0

def get_table_infos(args):
    table_infos = []
    args.data_dir = db_util.DBUtil().fetchone(args, "show global variables like '%datadir%';")
    sql = "select table_schema, table_name, DATA_LENGTH, INDEX_LENGTH, TABLE_ROWS, AUTO_INCREMENT from information_schema.tables " \
          "where table_schema != 'mysql' and table_schema != 'information_schema' and table_schema != 'performance_schema'";
    for row in db_util.DBUtil().fetchall(args, sql):
        table_info = TableInfo()
        table_info.schema = row["table_schema"]
        table_info.t_name = row["table_name"]
        table_info.rows = row["TABLE_ROWS"]
        table_info.data_size = row["DATA_LENGTH"]
        table_info.index_size = row["INDEX_LENGTH"]
        table_info.auto_increment = row["AUTO_INCREMENT"] if row["AUTO_INCREMENT"] else 0
        table_info.total_size = long(table_info.data_size) + long(table_info.index_size)
        table_infos.append(table_info)
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

def check_table_space(args):
    list_tmp = []
    table_infos = get_table_infos(args)
    host_client = paramiko.SSHClient()
    host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host_client.connect(args.host, port=22, username="root")

    for table_info in table_infos:
        shell = "ls -al {0}{1}/{2}.ibd | awk \'{3}\'".format(args.data_dir, table_info.schema, table_info.t_name, "{print $5}")
        stdin, stdout, stderr = host_client.exec_command(shell)
        result = stdout.readlines()
        if(len(result) > 0):
            table_info.file_size = long(result[0].replace("\n", ""))
            table_info.diff = table_info.file_size - table_info.total_size
            table_info.value = get_data_length(table_info.diff)
            list_tmp.append(table_info)

    host_client.close()
    return sorted(list_tmp, cmp=lambda x,y:cmp(x.diff,y.diff), reverse=True)

def insert_table_data(host_info, table_infos):
    value_list = []
    value_format = "({0},'{1}','{2}',{3},{4},{5},{6},{7},{8},date(now()))"
    sql = "insert into mysql_web.mysql_data_size_log (host_id, `schema`, table_name, data_size, index_size, rows, auto_increment, file_size, diff, `date`) values"
    for table_info in table_infos:
        value_list.append(value_format.format(host_info.key, table_info.schema, table_info.t_name, table_info.data_size, table_info.index_size,
                                              table_info.rows, table_info.auto_increment, table_info.file_size, table_info.diff))
    sql =  sql + ','.join(value_list) + ";"
    db_util.DBUtil().execute(host_info, sql)

def analysis_table_data(host_info):
    sql = "insert into mysql_web.mysql_data_size_for_day (host_id, data_size_incr)" \
          "select sum(data_size), sum(index_size), sum(rows), sum(auto_increment), sum(file_size), sum(diff) from mysql_web.mysql_data_size_log" \
          "where host_id={0} group by `date`;".format(host_info.key)


MySQL_Host = host_info.HoseInfo(host="192.168.11.128", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")
MySQL_Host.key = 1
aa = get_table_infos(MySQL_Host)
insert_table_data(MySQL_Host, aa)
