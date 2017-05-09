import db_util, base_class, settings

def get_slow_logs(server_id, start_datetime="", stop_datetime=""):
    sql = """select a.checksum, left(a.fingerprint, 30) fingerprint, a.first_seen, a.last_seen,
                    b.serverid_max, b.db_max, b.user_max, b.ts_min, b.ts_max, sum(b.ts_cnt) ts_cnt,
                    sum(b.Query_time_sum)/sum(b.ts_cnt) Query_time_avg,
                    max(b.Query_time_max) Query_time_max, min(b.Query_time_min) Query_time_min, sum(b.Query_time_sum) Query_time_sum,
                    max(b.Lock_time_max) Lock_time_max, min(b.Lock_time_min) Lock_time_min, sum(b.Lock_time_sum) Lock_time_sum
             from mysql_web.mysql_slow_query_review a
             inner join mysql_web.mysql_slow_query_review_history b on a.checksum=b.checksum and b.serverid_max={0}
             group by a.checksum
             order by last_seen desc
             limit 30;"""
    result = []
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host_Tmp, sql.format(server_id)):
        info = base_class.BaseClass(None)
        info.checksum = row["checksum"]
        info.fingerprint = row["fingerprint"]
        info.first_seen = row["first_seen"]
        info.last_seen = row["last_seen"]
        info.serverid_max = row["serverid_max"]
        info.db_max = row["db_max"]
        info.user_max = row["user_max"]
        info.ts_max = row["ts_max"]
        info.ts_cnt = int(row["ts_cnt"])
        info.Query_time_avg = get_float(row["Query_time_avg"])
        info.Query_time_max = get_float(row["Query_time_max"])
        info.Query_time_min = get_float(row["Query_time_min"])
        info.Query_time_sum = get_float(row["Query_time_sum"])
        info.Lock_time_max = get_float(row["Lock_time_max"])
        info.Lock_time_min = get_float(row["Lock_time_min"])
        info.Lock_time_sum = get_float(row["Lock_time_sum"])
        result.append(info)
    return result

def get_slow_log_detail(checksum, server_id):
    sql = """select t1.checksum, t2.ts_cnt,  t1.first_seen, t1.last_seen, t1.fingerprint, t2.sample,
             t2.serverid_max, t2.db_max, t2.user_max,
             t2.Query_time_min, t2.Query_time_max, t2.Query_time_sum, t2.Query_time_pct_95,
             Lock_time_sum,Lock_time_min,Lock_time_max,Lock_time_pct_95,
             Rows_sent_sum,Rows_sent_min,Rows_sent_max,Rows_sent_pct_95,
             Rows_examined_sum,Rows_examined_min,Rows_examined_max,Rows_examined_pct_95
             from mysql_web.mysql_slow_query_review t1
             left join mysql_web.mysql_slow_query_review_history t2 on t1.checksum = t2.checksum and t2.serverid_max={0}
             where t1.checksum={1} limit 1;""".format(server_id, checksum)
    slow_log_detail = None
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host_Tmp, sql):
        slow_log_detail = base_class.BaseClass(None)
        slow_log_detail.serverid_max = row["serverid_max"]
        slow_log_detail.db_max = row["db_max"]
        slow_log_detail.user_max = row["user_max"]
        slow_log_detail.checksum = row["checksum"]
        slow_log_detail.count = int(row["ts_cnt"])
        slow_log_detail.query_time_sum = row["Query_time_sum"]
        slow_log_detail.query_time_max = row["Query_time_max"]
        slow_log_detail.query_time_min = row["Query_time_min"]
        slow_log_detail.query_time_pct_95 = row["Query_time_pct_95"]
        slow_log_detail.lock_time_sum = row["Lock_time_sum"]
        slow_log_detail.lock_time_max = row["Lock_time_max"]
        slow_log_detail.lock_time_min = row["Lock_time_min"]
        slow_log_detail.lock_time_pct_95 = row["Lock_time_pct_95"]
        slow_log_detail.rows_sent_sum = row["Rows_sent_sum"]
        slow_log_detail.rows_sent_max = row["Rows_sent_max"]
        slow_log_detail.rows_sent_min = row["Rows_sent_min"]
        slow_log_detail.rows_sent_pct_95 = row["Rows_sent_pct_95"]
        slow_log_detail.rows_examined_sum = row["Rows_examined_sum"]
        slow_log_detail.rows_examined_max = row["Rows_examined_max"]
        slow_log_detail.rows_examined_min = row["Rows_examined_min"]
        slow_log_detail.rows_examined_pct_95 = row["Rows_examined_pct_95"]
        slow_log_detail.first_seen = row["first_seen"]
        slow_log_detail.last_seen = row["last_seen"]
        slow_log_detail.fingerprint = row["fingerprint"].decode("utf-8")
        slow_log_detail.sample = row["sample"].decode("utf-8")
    slow_log_detail.explain_infos = get_slow_log_explain(server_id, slow_log_detail.db_max, slow_log_detail.sample)
    return slow_log_detail

def get_slow_log_explain(server_id, db, sql):
    connection, cursor = db_util.DBUtil().get_conn_and_cur(settings.MySQL_Host_Tmp)
    cursor.execute("use {0};".format(db))
    cursor.execute("explain {0};".format(sql))
    result = []
    for row in cursor.fetchall():
        info = base_class.BaseClass(None)
        info.rows = row["rows"]
        info.select_type = row["select_type"]
        info.Extra = row["Extra"]
        info.ref = row["ref"]
        info.key_len = row["key_len"]
        info.possible_keys = row["possible_keys"]
        info.key = row["key"]
        info.table = row["table"]
        info.type = row["type"]
        info.id = row["id"]
        result.append(info)
    db_util.DBUtil().close(connection, cursor)
    return result

def get_float(value):
    return str("%.5f" % value)