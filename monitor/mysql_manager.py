# -*- coding: utf-8 -*-

import db_util, cache, common, settings, entitys, traceback


# 获取mysql线程信息
def get_show_processlist(host_id):
    return get_mysql_status_fetchall(host_id, "SELECT * FROM information_schema.processlist where COMMAND != 'Sleep';")


def get_show_processlist_infos(host_id):
    return db_util.DBUtil().get_list_infos_to_lower(cache.Cache().get_host_info(host_id),
                                                    "SELECT * FROM information_schema.processlist where COMMAND != 'Sleep' and LENGTH(info) > 0;")


# 获取从库复制信息
def get_show_slave_status(host_id):
    return get_mysql_status_fetchone(host_id, "show slave status;")


# 获取主库binlog信息
def get_show_master_status(host_id):
    return get_mysql_status_fetchone(host_id, "show master status;")


# 获取innodb的详细信息
def get_show_engine_innodb_status(host_id):
    return get_mysql_status_fetchone(host_id, "show engine innodb status;")


# 获取innodb事务信息
def get_innodb_trx(host_id):
    return get_mysql_status_fetchall(host_id, "SELECT * FROM information_schema.INNODB_TRX;")


# 获取innodb事务锁信息
def get_innodb_lock_status(host_id):
    return get_mysql_status_fetchall(host_id,
                                     """select r.trx_isolation_level,
                                        r.trx_id waiting_trx_id,
                                        r.trx_mysql_thread_id  waiting_trx_thread,
                                        r.trx_state  waiting_trx_state,
                                        lr.lock_mode waiting_trx_lock_mode,
                                        lr.lock_type  waiting_trx_lock_type,
                                        lr.lock_table  waiting_trx_lock_table,
                                        lr.lock_index  waiting_trx_lock_index,
                                        r.trx_query  waiting_trx_query,
                                        b.trx_id  blocking_trx_id,
                                        b.trx_mysql_thread_id  blocking_trx_thread,
                                        b.trx_state  blocking_trx_state,
                                        lb.lock_mode blocking_trx_lock_mode,
                                        lb.lock_type  blocking_trx_lock_type,
                                        lb.lock_table  blocking_trx_lock_table,
                                        lb.lock_index  blocking_trx_lock_index,
                                        b.trx_query  blocking_query
                                        from information_schema.innodb_lock_waits w
                                        inner join information_schema.innodb_trx b on b.trx_id=w.blocking_trx_id
                                        inner join information_schema.innodb_trx r on r.trx_id=w.requesting_trx_id
                                        inner join information_schema.innodb_locks lb on lb.lock_trx_id=w.blocking_trx_id
                                        inner join information_schema.innodb_locks lr on lr.lock_trx_id=w.requesting_trx_id;""")


# 获取单一mysql global status信息
def get_mysql_status_fetchone(host_id, sql):
    return db_util.DBUtil().fetchone(cache.Cache().get_host_info(host_id), sql)


# 获取多个mysql global status信息
def get_mysql_status_fetchall(host_id, sql):
    return db_util.DBUtil().fetchone(cache.Cache().get_host_info(host_id), sql)


def get_log_text(result):
    number = 0
    log_list = []
    if (isinstance(result, list)):
        for value_dict in result:
            number += 1
            log_list.append("*************************** {0}. row ***************************\n".format(number))
            append_log_list(value_dict, log_list)
    elif (isinstance(result, dict)):
        append_log_list(result, log_list)
    if (len(log_list) > 0):
        return "".join(log_list)
    return ""


def append_log_list(value_dict, log_list):
    for key, value in value_dict.items():
        log_list.append("{0}: {1}\n".format(key, value))


# 跳过从库复制错误
def skip_slave_error(host_id):
    slave_info = get_show_slave_status(host_id)
    if (slave_info["Slave_SQL_Running"] == "No"):
        sql = "stop slave sql_thread; set global sql_slave_skip_counter=1; start slave sql_thread;"
        db_util.DBUtil().execute(cache.Cache().get_host_info(host_id), sql)
        return "repl error skip ok."
    return "repl status is ok."


# 优化表空间
def optimized_table_space(host_id, table_name):
    db_util.DBUtil().execute(cache.Cache().get_host_info(host_id), "alter table {0} engine=innodb;".format(table_name))
    return "optimized ok."


# kill掉mysql的线程
def kill_mysql_thread(host_id, thread_id):
    db_util.DBUtil().execute(cache.Cache().get_host_info(host_id), "kill {0};".format(thread_id))
    return "kill thread {0} ok!".format(thread_id)


# 获取所有的MySQL主机信息
def add_mysql_host_info(obj):
    return "ok"


