# -*- coding: utf-8 -*-

import pymysql
from DBUtils.PooledDB import PooledDB

# 用户名
user = ""

# 密码
password = ""

# 一个字符串，联系人通过逗号分割
mail_list = ""

# 主机ip地址列表，是一个list，手动添加
host_list = []

# 连接池对象
connection_pools = {}

# processlist的SQL语句
processlist_sql = """SELECT * FROM information_schema.processlist where COMMAND != 'Sleep' and LENGTH(info) > 0;"""

def get_processlist_infos(host):
    try:
        connection = get_mysql_connection(host, user=user, password=password)
    finally:
        connection.close()

def get_mysql_connection(host_name, port=3306, user="", password=""):
    if (connection_pools.get(host_name) == None):
        pool = PooledDB(creator=pymysql, mincached=2, maxcached=4, maxconnections=5,
                        host=host_name, port=port, user=user, passwd=password,
                        use_unicode=False, charset="utf8", cursorclass=pymysql.cursors.DictCursor, reset=False, autocommit=True)
        connection_pools[host_name] = pool
    return connection_pools[host_name].connection()


if (__name__ == "__main__"):
    for host in host_list:
        pass


