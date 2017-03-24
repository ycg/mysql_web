import db_util, base_class, settings

def get_slow_log_top_20():
    sql = """select t1.checksum, t2.ts_cnt, t2.Query_time_sum, t1.first_seen, t1.last_seen, left(t1.fingerprint, 100) as fingerprint
             from db1.mysql_slow_query_review t1
             left join db1.mysql_slow_query_review_history t2 on t1.checksum = t2.checksum
             order by t2.Query_time_sum desc limit 20;"""
    slow_list = []
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_info = base_class.BaseClass(None)
        slow_info.checksum = row["checksum"]
        slow_info.count = int(row["ts_cnt"])
        slow_info.query_time_sum = row["Query_time_sum"]
        slow_info.first_seen = row["first_seen"]
        slow_info.last_seen = row["last_seen"]
        slow_info.fingerprint = row["fingerprint"]
        slow_list.append(slow_info)
    return slow_list

def get_slow_log_detail(checksum):
    sql = """select t1.checksum, t2.ts_cnt,  t1.first_seen, t1.last_seen, t1.fingerprint, t2.sample,
             t2.Query_time_min, t2.Query_time_max, t2.Query_time_sum, t2.Query_time_pct_95,
             Lock_time_sum,Lock_time_min,Lock_time_max,Lock_time_pct_95,
             Rows_sent_sum,Rows_sent_min,Rows_sent_max,Rows_sent_pct_95,
             Rows_examined_sum,Rows_examined_min,Rows_examined_max,Rows_examined_pct_95
             from db1.mysql_slow_query_review t1
             left join db1.mysql_slow_query_review_history t2 on t1.checksum = t2.checksum
             where t1.checksum='{0}' limit 1;""".format(checksum)
    slow_log_detail = None
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_log_detail = base_class.BaseClass(None)
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
        slow_log_detail.fingerprint = row["fingerprint"]
        slow_log_detail.sample = row["sample"]
    return slow_log_detail

