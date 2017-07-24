import monitor.db_util, monitor.cache, settings, monitor.base_class, json, traceback, pymysql

def execute_sql_test(host_id, sql, comment, is_backup):
    result = monitor.base_class.BaseClass(None)
    result.error = ""
    result.success = ""
    conn, cur = None, None
    try:
        host_info = monitor.cache.Cache().get_host_info(int(host_id))
        conn = pymysql.connect(host=host_info.host, port=host_info.port, user=host_info.user, passwd=host_info.password, db="mysql", charset="utf8", autocommit=True)
        cur = conn.cursor()
        sql = "start transaction;" + sql + "commit;"
        cur.execute(sql)
        result.success = "execute sql ok."
        close(conn, cur)
        insert_execute_sql_log(host_id, sql, comment, is_backup=is_backup)
    except Exception, e:
        traceback.print_exc()
        result.error = str(e)
        try:
            close(conn, cur)
        except Exception:
            pass
    return json.dumps(result, default=lambda o: o.__dict__)

def close(connection, cursor):
    if(cursor != None):
        cursor.close()
    if(connection != None):
        connection.close()

def insert_execute_sql_log(host_id, sql, comment, is_backup=0, backup_name=""):
    sql = "insert into mysql_web.execute_sql_log " \
          "(host_id, is_backup, backup_name, `sql`, `comment`) " \
          "VALUES " \
          "(%s, %s, '%s', '%s', '%s')" % (host_id, is_backup, backup_name, pymysql.escape_string(sql), pymysql.escape_string(comment))
    monitor.db_util.DBUtil().execute(settings.MySQL_Host, sql);

