# -*- coding: utf-8 -*-

#检查数据库表空间报表
#python check_tablespace.py --host=192.168.11.130 --user=yangcg --password='123456'
#python check_tablespace.py --host=192.168.11.130 --port=3310 --user=yangcg --password='123456'
#数据保存在tmp目录下，以host值为文件名
#--convert：是否把大小进行可读性格式化，如-1024M

import MySQLdb, paramiko, sys, argparse

class TableInfo():
    diff = 0

def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql host")
    parser.add_argument("--port", type=int, dest="port", help="mysql port", default=3306)
    parser.add_argument("--user", type=str, dest="user", help="mysql user")
    parser.add_argument("--password", type=str, dest="password", help="mysql password")
    parser.add_argument("--convert", type=str, dest="convert", help="data size convert", default=True)
    args = parser.parse_args()

    if(not args.host or not args.port or not args.user or not args.password):
        sys.exit(1)

    return args

def get_table_infos(args):
    table_infos = []
    connection = MySQLdb.connect(host=args.host, port=args.port, user=args.user, passwd=args.password)
    cursor = connection.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    cursor.execute("show global variables like '%datadir%';")
    args.data_dir = cursor.fetchone()["Value"]

    cursor.execute("select table_schema, table_name, DATA_LENGTH, INDEX_LENGTH from information_schema.tables "
                   "where table_schema != 'mysql' and table_schema != 'information_schema' and table_schema != 'performance_schema'")
    for row in cursor.fetchall():
        table_info = TableInfo()
        table_info.schema = row["table_schema"]
        table_info.t_name = row["table_name"]
        table_info.data_size = row["DATA_LENGTH"] if row["DATA_LENGTH"] else 0
        table_info.index_size = row["INDEX_LENGTH"] if row["INDEX_LENGTH"] else 0
        table_info.total_size = long(table_info.data_size) + long(table_info.index_size)
        table_infos.append(table_info)
    cursor.close()
    connection.close()
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

def save_file(args, table_infos):
    file = open("/tmp/{0}_tb.txt".format(args.host), "w")
    file.write("schema\ttable_name\ttable_fragment\tdata_size\tindex_size\ttotal_size\tfile_size\n")
    for table_info in table_infos:
        file.write(get_print_string(args, table_info) + "\n")
    file.close()
    return table_infos

def get_print_string(args, table_info):
    str_format = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}"
    if(args.convert == True):
        return str_format.format(table_info.schema, table_info.t_name, table_info.value, get_data_length(table_info.data_size),
                                 get_data_length(table_info.index_size), get_data_length(table_info.total_size), get_data_length(table_info.file_size))
    else:
        return str_format.format(table_info.schema, table_info.t_name, table_info.value, table_info.data_size,
                                 table_info.index_size, table_info.total_size, table_info.file_size)

'''
def get_all_table_file_size(args):
    table_size = {}
    host_client = paramiko.SSHClient()
    host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host_client.connect(args.host, port=22, username="root")
    connection = MySQLdb.connect(host=args.host, port=args.port, user=args.user, passwd=args.password)
    cursor = connection.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    cursor.execute("show databases;")
    for row in cursor.fetchall():
        db_name = row["Database"]
        if(db_name == "mysql" or db_name == "information_schema" or db_name == "performance_schema"):
            return
        shell = "ls -al {0}/{1}/ | grep -E '(ibd$)' | awk \'{2}\'".format(args.data_dir, db_name, "{print $5, $9}")
        stdin, stdout, stderr = host_client.exec_command(shell)
        result = stdout.readlines()
        if(len(result) > 0 and len(stderr) <= 0):
            for value in result:
                list_tmp = value.replace("\n", "").split(" ")
    cursor.close()
    connection.close()
    host_client.close()'''

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
            print(get_print_string(args, table_info))


    host_client.close()
    save_file(args, sorted(list_tmp, cmp=lambda x,y:cmp(x.diff,y.diff), reverse=True))

if(__name__ == "__main__"):
    print("start...")
    check_table_space(check_arguments())
    print("table space check is ok.")


