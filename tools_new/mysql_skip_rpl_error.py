# -*- coding: utf-8 -*-

import argparse, sys, pymysql, time, traceback

class Entity():
    def __init__(self):
        pass


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql host")
    parser.add_argument("--user", type=str, dest="user", help="mysql user")
    parser.add_argument("--password", type=str, dest="password", help="mysql password")
    parser.add_argument("--port", type=int, dest="port", help="mysql port", default=3306)
    parser.add_argument("--sleep", type=float, dest="sleep", help="while sleep time second", default=0.5)
    args = parser.parse_args()

    if not args.host or not args.user or not args.password or not args.port:
        print("[ERROR]:Please input host or user or password or port.")
        sys.exit(1)
    return args


def main(args):
    slave_status = show_slave_status(args)
    if (slave_status.slave_sql_running == "No"):
        print_log("[Error]:SQL thread is error, error code is [{0}]".format(slave_status.last_sql_errno))
        print_log("[Error]:SQL error info is {0}".format(slave_status.last_sql_error))
    else:
        print_log("[INFO]:Slave SQL thread is ok!")
    time.sleep(args.sleep)


# 获取show slave status数据
def show_slave_status(args):
    return execute_sql(args, "show slave status;")


# 跳过sql线程的错误
def skip_sql_thread_error(args):
    execute_sql(args, "set global sql_slave_skip_counter=1; select sleep(0.1); start slave sql_thread;")


# 执行sql
def execute_sql(args, sql):
    connection, cursor = None, None
    try:
        connection = pymysql.connect(host=args.host, user=args.user, passwd=args.password, port=args.port, use_unicode=True, charset="utf8", connect_timeout=2)
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
        cursor.execute(sql)
        result = cursor.fetchone()
        info = Entity()
        if (result != None):
            for key, value in result.items():
                setattr(info, key.lower(), value)
        return info
    except:
        connection.rollback()
        traceback.print_exc()
    finally:
        if (cursor != None):
            cursor.close()
        if (connection != None):
            connection.close()


# 打印日志
def print_log(log_value):
    print("{0} {1}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), log_value))


if (__name__ == "__mian__"):
    main(check_arguments())


