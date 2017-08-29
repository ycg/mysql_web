# -*- coding: utf-8 -*-

import pymysql
from DBUtils.PooledDB import PooledDB

# 可以连接mysql_web系统的host_infos表读取要监控的数据库信息

# mysql主机信息列表
host_infos = []

# 一个字符串，联系人通过逗号分割
mail_list = ""

# 连接池对象
connection_pools = {}

# processlist的SQL语句
processlist_sql = """SELECT * FROM information_schema.processlist where COMMAND != 'Sleep' and LENGTH(info) > 0;"""


class Entity():
    def __init__(self):
        pass


def check_all_mysql_processlist():
    pass


def get_monitor_mysql_host_infos():
    return get_list_infos(None, "select host_id, host, port, user, password, remark, is_master, is_slave, master_id, is_deleted, ssh_port, ssh_password from mysql_web.host_infos;")


def get_list_infos(host_info, sql):
        result = []
        for row in fetchall(host_info, sql):
            info = Entity()
            for key, value in row.items():
                setattr(info, key.lower(), value)
            result.append(info)
        return result

def fetchall(host_info, sql):
    connection, cursor = None, None
    try:
        connection = get_mysql_connection(host_info.host, user=host_info.user, password=host_info.password, port=host_info.port)
        cursor = connection.connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        if (cursor != None):
            cursor.close()
        if (connection != None):
            connection.close()

def get_mysql_connection(host_name, port=3306, user="", password=""):
    if (connection_pools.get(host_name) == None):
        pool = PooledDB(creator=pymysql, mincached=2, maxcached=4, maxconnections=5,
                        host=host_name, port=port, user=user, passwd=password,
                        use_unicode=False, charset="utf8", cursorclass=pymysql.cursors.DictCursor, reset=False, autocommit=True)
        connection_pools[host_name] = pool
    return connection_pools[host_name].connection()


if (__name__ == "__main__"):
    while(True):
        host_infos = get_monitor_mysql_host_infos()
        check_all_mysql_processlist(host_infos)


