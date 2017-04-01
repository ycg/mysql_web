import db_util, cache

def get_show_processlist(host_id):
    return get_mysql_status_fetchall(host_id, "show full processlist;")

def get_show_slave_status(host_id):
    return get_mysql_status_fetchone(host_id, "show slave status;")

def get_show_master_status(host_id):
    return get_mysql_status_fetchone(host_id, "show master status;")

def get_show_engine_innodb_status(host_id):
    return get_mysql_status_fetchone(host_id, "show engine innodb status;")

def get_innodb_trx(host_id):
    return get_mysql_status_fetchall(host_id, "SELECT * FROM information_schema.INNODB_TRX;")

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

def get_mysql_status_fetchone(host_id, sql):
    return db_util.DBUtil().fetchone(cache.Cache().get_host_info(host_id), sql)

def get_mysql_status_fetchall(host_id, sql):
    return db_util.DBUtil().fetchone(cache.Cache().get_host_info(host_id), sql)




