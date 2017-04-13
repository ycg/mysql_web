import db_util, cache, settings

def execute_sql_test(host_id, sql, comment):
    conn, cur = None, None
    try:
        conn, cur = db_util.DBUtil().get_conn_and_cur(settings.MySQL_Host)
        #conn, cur = db_util.DBUtil().get_conn_and_cur(cache.Cache().get_host_info(host_id))
        cur.execute("start transaction;")
        cur.execute(sql)
        cur.execute("commit;")
        insert_execute_sql_log(host_id, sql, comment)
        return "execute sql ok."
    except Exception, e:
        return repr(e)
    finally:
        db_util.DBUtil().close(conn, cur)

def insert_execute_sql_log(host_id, sql, comment, is_backup=0, backup_name=""):
    sql = "insert into execute_sql_log (host_id, is_backup, backup_name, `sql`, `comment`) VALUES ({0}, {1}, '{2}', '{3}', '{4}')" \
          .format(host_id, is_backup, backup_name, sql, comment)
    db_util.DBUtil().execute(settings, sql)
