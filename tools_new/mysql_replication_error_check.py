# -*- coding: utf-8 -*-

import argparse, sys, pymysql


# 复制错误检查
# 1032 - MySQL error code 1032 (ER_KEY_NOT_FOUND): Can't find record in '%-.192s'
# 1062 - MySQL error code 1062 (ER_DUP_ENTRY): Duplicate entry '%-.192s' for key %d


# 参数详解
# --host
# --user
# --password
# --port
# --execute：此参数将会在slave上执行补全或删除数据，不加就打印数据

# 调用示例

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
    parser.add_argument("--execute", type=str, dest="execute", help="execute sql")
    args = parser.parse_args()

    if not args.host or not args.user or not args.password or not args.port:
        print("[error]:Please input host or user or password or port.")
        sys.exit(1)
    return args


def check_replication_status(args):
    slave_status = get_slave_status(args)
    if (slave_status.slave_sql_running == "NO"):
        if (slave_status.last_sql_errno == KEY_NOT_FOUND):
            check_replication_error_1032(args, slave_status)
        elif (slave_status.last_sql_errno == DUPLICATE_KEY):
            check_replication_error_1062(args, slave_status)
        else:
            print("[error]:Error info: {0}".format(slave_status.last_sql_error))
    else:
        print("Slave SQL thread is ok!")


def check_replication_error_1032(args, slave_status):
    # 行记录未发现
    start_pos = slave_status.exec_master_log_pos
    end_pos = slave_status.last_sql_error.split(" ")[-1]
    print("[info]:start pos {0}, end pos {1}".format(start_pos, end_pos))


def check_replication_error_1062(args, slave_status):
    # 主键冲突
    pass


def get_slave_status(args):
    try:
        connection = pymysql.connect(host=args.host, user=args.user, passwd=args.password, port=args.port, use_unicode=True, charset="utf8", connect_timeout=2)
        cursor = connection.cursor(cursorclass=pymysql.cursors.DictCursor)
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
