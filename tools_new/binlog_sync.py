# -*- coding: utf-8 -*-

# binlog实时同步
# 使用场景：需要把mysql1实例的部分表数据同步到mysql2
# 虽然可以使用mysql repl的过滤条件搞定，但这种可动态性比较好
# 如果同步的比较复杂，可以自己定制


import time, sys, pymysql, traceback
from DBUtils.PooledDB import PooledDB
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent

reload(sys)
sys.setdefaultencoding('UTF-8')

delete_sql = "DELETE FROM `{0}` WHERE {1};"
update_sql = "UPDATE `{0}` set {1} WHERE {2};"
insert_sql = "INSERT INTO `{0}` ({1}) VALUES ({2});"

server_id = 666555

# 开始同步的pos位置
start_pos = 61528514

# 从那个binlog文件开始同步，不填，同步所以binlog
log_file = "log_bin.000446"

# mysql连接池
connection_pools = {}

# 需要复制的对象,是一个字典结构，key：库名 value：表名称，可以有多个表
do_replication_tables = {"db1": ["table1"], "db2": ["table1", "table2"]}

# master地址
from_connection_string = {"host": "", "port": 3306, "user": "", "passwd": ""}

# slave地址
to_connection_string = {"host": "", "port": 3306, "user": "", "passwd": ""}


def binlog_process():
    try:
        stream = BinLogStreamReader(connection_settings=from_connection_string, log_file=log_file, log_pos=start_pos, resume_stream=True, server_id=server_id)

        for binlogevent in stream:

            sql_list = []
            if (isinstance(binlogevent, WriteRowsEvent)):
                for row in binlogevent.rows:
                    if (check_table(binlogevent)):
                        sql = insert_to_sql(row, binlogevent)
                        sql_list.append(sql)
            elif (isinstance(binlogevent, DeleteRowsEvent)):
                for row in binlogevent.rows:
                    if (check_table(binlogevent)):
                        sql = insert_to_sql(row, binlogevent)
                        sql_list.append(sql)
            elif (isinstance(binlogevent, UpdateRowsEvent)):
                for row in binlogevent.rows:
                    if (check_table(binlogevent)):
                        sql = update_to_sql(row, binlogevent)
                        sql_list.append(sql)

            if (len(sql_list) > 0):
                execute_sql_to_group2_master(sql_list, stream.log_file, binlogevent.packet.log_pos)
    finally:
        pass


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


def insert_to_sql(row, binlogevent):
    return insert_sql.format(binlogevent.table, ', '.join(map(lambda k: '`%s`' % k, row['values'].keys())), sql_format_for_insert(row["values"].values()))


def delete_to_sql(row, binlogevent):
    return delete_sql.format(binlogevent.table, sql_format(row['values'], " AND "))


def update_to_sql(row, binlogevent):
    return update_sql.format(binlogevent.table, sql_format(row['after_values'], ", "), sql_format(row['before_values'], " AND "))


def check_table(binlogevent):
    if (do_replication_tables.has_key(binlogevent.schema)):
        for table_list in do_replication_tables.values():
            if (binlogevent.table in table_list):
                return True
    return False


def get_log_file_and_pos():
    global log_file, start_pos
    result = fetchone("select log_file, log_pos from db1.sync_binlog_info where id = 1;", to_connection_string)
    if (result != None):
        if (len(result["log_file"]) > 0 and len(result["log_pos"]) > 0):
            log_file = result["log_file"]
            start_pos = result["log_pos"]


def execute_sql_to_group2_master(sql_list, log_file, log_pos):
    sql = "start transaction;"
    sql += "use agent;"
    sql += "".join(sql_list)
    sql += "update db1.sync_binlog_info set log_file='{0}', log_pos={1};".format(log_file, log_pos)
    sql += "commit;"
    print(sql + "\n")

    # 如果要执行sql，取消下面的注释，请测试好了在进行上线使用
    # sql += "update db1.sync_binlog_info set log_file='{0}', log_pos={1};".format(log_file, log_pos)
    # execute_sql(sql, to_connection_string)


def execute_sql(sql, connection_string):
    try:
        conn = get_mysql_connection(connection_string)
        cur = conn.cursor()
        sql = "start transaction;" + sql + "commit;"
        cur.execute(sql)
    except:
        traceback.print_exc()
    finally:
        close(conn, cur)


def fetchone(sql, connection_string):
    try:
        conn = get_mysql_connection(connection_string)
        cur = conn.cursor()
        return cur.fetchone(sql)
    except:
        traceback.print_exc()
    finally:
        close(conn, cur)


def close(connection, cursor):
    if (cursor != None):
        cursor.close()
    if (connection != None):
        connection.close()


def get_mysql_connection(connection_string):
    if (connection_pools.get(connection_string["host"]) == None):
        pool = PooledDB(creator=pymysql, mincached=5, maxcached=10,
                        host=connection_string["host"],
                        port=connection_string["port"],
                        user=connection_string["user"],
                        passwd=connection_string["passwd"],
                        use_unicode=False, charset="utf8", cursorclass=pymysql.cursors.DictCursor, reset=False, autocommit=False)
        connection_pools[connection_string["host"]] = pool
    return connection_pools[connection_string["host"]].connection()


def check_table_exist():
    create_table_sql = """create database db1;
                          create table sync_binlog_info
                          (
                              id tinyint NOT NULL PRIMARY KEY,
                              log_file VARCHAR(50) NOT NULL default '',
                              log_pos bigint NOT NULL DEFAULT 0,
                              updated_time TIMESTAMP NOT NULL default current_timestamp on update current_timestamp
                          );
                          insert into db1.sync_binlog_info (id) values(1);"""
    sql = "select * from tables WHERE TABLE_SCHEMA = 'db1' and TABLE_NAME = 'sync_binlog_info';"
    result = fetchone(sql, to_connection_string)
    if (result == None):
        execute_sql(create_table_sql, to_connection_string)


if (__name__ == "__main__"):
    start_time = time.time()
    print("Start process binlog.....")
    check_table_exist()
    binlog_process()
    end_time = time.time()
    print("Complete ok, total time: %d" % (end_time - start_time))
