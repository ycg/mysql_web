# -*- coding: utf-8 -*-

import argparse, sys, pymysql, time
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent

# 复制错误检查
# 1032 - MySQL error code 1032 (ER_KEY_NOT_FOUND): Can't find record in '%-.192s'
# 1062 - MySQL error code 1062 (ER_DUP_ENTRY): Duplicate entry '%-.192s' for key %d

# 参数详解
# --host
# --user
# --password
# --port
# --execute：此参数将会在slave上执行补全或删除数据，不加就打印数据

# 检查复制状态示例
# python mysql_replication_error_check.py --host=192.168.11.102 --user=yangcg --password=yangcaogui

# 检查复制状态并进行修复
# python mysql_replication_error_check.py --host=192.168.11.102 --user=yangcg --password=yangcaogui --execute


KEY_NOT_FOUND = 1032
DUPLICATE_KEY = 1062


class Entity():
    def __init__(self):
        pass


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql host")
    parser.add_argument("--user", type=str, dest="user", help="mysql user")
    parser.add_argument("--password", type=str, dest="password", help="mysql password")
    parser.add_argument("--port", type=int, dest="port", help="mysql port", default=3306)
    parser.add_argument("-e", "--execute", dest="execute", help="execute sql", default=False, action='store_true')
    args = parser.parse_args()

    if not args.host or not args.user or not args.password or not args.port:
        print("[ERROR]:Please input host or user or password or port.")
        sys.exit(1)
    return args


# 检查复制状态
def check_replication_status(args):
    slave_status = get_slave_status(args)
    if (slave_status.slave_sql_running == "No"):
        if (slave_status.last_sql_errno == KEY_NOT_FOUND or slave_status.last_sql_errno == DUPLICATE_KEY):
            check_replication_error_1032_or_1062(args, slave_status)
        else:
            print("[ERROR]:Error info: {0}".format(slave_status.last_sql_error))
    else:
        print("[INFO]:Slave SQL thread is ok!")


# 处理复制1032和1062错误
def check_replication_error_1032_or_1062(args, slave_status):
    args.master_host = slave_status.master_host
    args.master_port = slave_status.master_port
    args.log_file = slave_status.relay_master_log_file
    args.start_pos = slave_status.exec_master_log_pos
    args.end_pos = slave_status.last_sql_error.split(" ")[-1]
    print("[INFO]:error code is {0}".format(slave_status.last_sql_errno))
    print("[INFO]:replication error binlog file {0} start pos {1}, end pos {2}".format(args.log_file, args.start_pos, args.end_pos))
    flashback_sql = binlog_process(args)

    if (args.execute):
        print("[INFO]:start execute flashback sql.")
        execute_flashback_sql(args, flashback_sql)
        check_slave_is_ok(args)


# 执行闪回sql再次检查slave sql thread状态
def check_slave_is_ok(args):
    for i in range(1, 6):
        slave_status = get_slave_status(args)
        if (slave_status.slave_sql_running == "No"):
            print("[ERROR]:SQL thread error: {0}".format(slave_status.last_sql_error))
        else:
            print("[INFO]:{0} Slave SQL thread is ok!".format(i))
        time.sleep(1)


# 获取show slave status数据
def get_slave_status(args):
    connection, cursor = None, None
    try:
        connection = pymysql.connect(host=args.host, user=args.user, passwd=args.password, port=args.port, use_unicode=True, charset="utf8", connect_timeout=2)
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute("show slave status;")
        info = Entity()
        for key, value in cursor.fetchone().items():
            setattr(info, key.lower(), value)
        return info
    finally:
        if (cursor != None):
            cursor.close()
        if (connection != None):
            connection.close()


# 执行闪回sql并重启slave
def execute_flashback_sql(args, flashback_sql):
    connection, cursor = None, None
    try:
        connection = pymysql.connect(host=args.host, user=args.user, passwd=args.password, port=args.port, use_unicode=True, charset="utf8", connect_timeout=2)
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
        sql = "start transaction;" + "".join(flashback_sql) + "commit;"
        print("[INFO]:execute sql is {0}".format(sql))
        cursor.execute(sql)
        print("[INFO]:execute sql ok!")
        time.sleep(1)
        cursor.execute("start slave sql_thread;")
        print("[INFO]:Start slave sql thread ok!")
    finally:
        if (cursor != None):
            cursor.close()
        if (connection != None):
            connection.close()


# region pymysql replication

connection_settings = {}
delete_sql = "DELETE FROM `{0}`.`{1}` WHERE {2};"
update_sql = "UPDATE `{0}`.`{1}` set {2} WHERE {3};"
insert_sql = "INSERT INTO `{0}`.`{1}` ({2}) VALUES ({3});"


def sql_format(dic, split_value):
    list = []
    for key, value in dic.items():
        if (value == None):
            list.append("`%s`=null" % key)
            continue
        if (isinstance(value, int)):
            list.append("`%s`=%d" % (key, value))
        else:
            list.append("`%s`='%s'" % (key, value))
    return split_value.join(list)


def sql_format_for_insert(values):
    list = []
    for value in values:
        if (value == None):
            list.append("null")
            continue
        if (isinstance(value, int)):
            list.append('%d' % value)
        else:
            list.append('\'%s\'' % value)
    return ', '.join(list)


def binlog_process(args):
    stream = None
    flashback_sql = []
    try:
        connection_settings = {"host": args.master_host, "port": args.master_port, "user": args.user, "passwd": args.password}
        stream = BinLogStreamReader(connection_settings=connection_settings, log_file=args.log_file, log_pos=args.start_pos, resume_stream=True, server_id=987654)

        for binlogevent in stream:
            if (args.log_file != stream.log_file):
                break

            if (args.end_pos != None):
                if (binlogevent.packet.log_pos > args.end_pos):
                    break

            if (isinstance(binlogevent, WriteRowsEvent)):
                for row in binlogevent.rows:
                    print("[INFO]:original sql - {0}".format(insert_to_sql(row, binlogevent)))
                    print("[INFO]:flashback sql - {0}".format(delete_to_sql(row, binlogevent)))
                    flashback_sql.append(delete_to_sql(row, binlogevent))
            elif (isinstance(binlogevent, DeleteRowsEvent)):
                for row in binlogevent.rows:
                    print("[INFO]:original sql - {0}".format(delete_to_sql(row, binlogevent)))
                    print("[INFO]:flashback sql - {0}".format(insert_to_sql(row, binlogevent)))
                    flashback_sql.append(insert_to_sql(row, binlogevent))
            elif (isinstance(binlogevent, UpdateRowsEvent)):
                for row in binlogevent.rows:
                    print("[INFO]:original sql - {0}".format(update_to_sql(row, binlogevent, False)))
                    print("[INFO]:flashback sql - {0}".format(update_to_sql(row, binlogevent, True)))
                    flashback_sql.append(update_to_sql(row, binlogevent, True))
    finally:
        if (stream != None):
            stream.close()

    return flashback_sql


def insert_to_sql(row, binlogevent):
    return insert_sql.format(binlogevent.schema, binlogevent.table, ', '.join(map(lambda k: '`%s`' % k, row['values'].keys())), sql_format_for_insert(row["values"].values()))


def delete_to_sql(row, binlogevent):
    return delete_sql.format(binlogevent.schema, binlogevent.table, sql_format(row['values'], " AND "))


def update_to_sql(row, binlogevent, flashback):
    if (flashback):
        return update_sql.format(binlogevent.schema, binlogevent.table, sql_format(row['before_values'], ", "), sql_format(row['after_values'], " AND "))
    else:
        return update_sql.format(binlogevent.schema, binlogevent.table, sql_format(row['after_values'], ", "), sql_format(row['before_values'], " AND "))


# endregion


if (__name__ == "__main__"):
    check_replication_status(check_arguments())
