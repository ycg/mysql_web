import db_util, settings
from entitys import BaseClass

query_type = {1: "sql_count", 2: "query_sum", 3: "lock_sum", 4: "rows_sent_count", 5: "rows_exam_sum"}

table_config = {}

def get_slow_log_top_20():
    sql = """select t1.checksum, t2.ts_cnt, t2.Query_time_sum, t1.first_seen, t1.last_seen, left(t1.fingerprint, 100) as fingerprint
             from db1.mysql_slow_query_review t1
             left join db1.mysql_slow_query_review_history t2 on t1.checksum = t2.checksum
             order by t2.Query_time_sum desc limit 20;"""
    sql = """select * from
             (
                select t1.checksum, t1.first_seen, t1.last_seen, left(t1.fingerprint, 100) as fingerprint,
                (
                    select round(sum(ifnull(ts_cnt, 0)), 2) from db1.mysql_slow_query_review_history where checksum= t1.checksum
                ) as ts_cnt,
                (
                    select round(sum(ifnull(Query_time_sum, 0)), 2) from db1.mysql_slow_query_review_history where checksum= t1.checksum
                ) as Query_time_sum
                from db1.mysql_slow_query_review t1
             ) t2 order by Query_time_sum desc limit 20;"""
    slow_list = []
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_info = BaseClass(None)
        slow_info.checksum = row["checksum"]
        slow_info.count = int(row["ts_cnt"])
        slow_info.query_time_sum = row["Query_time_sum"]
        slow_info.first_seen = row["first_seen"]
        slow_info.last_seen = row["last_seen"]
        slow_info.fingerprint = row["fingerprint"].decode("utf-8")
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
             where t1.checksum={0} limit 1;""".format(checksum)
    slow_log_detail = None
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_log_detail = BaseClass(None)
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
    return slow_log_detail

def get_all_slow_infos(host_id, query_type_id):
    sql = """select * from
             (
                 select t1.checksum, sum(ifnull(t2.ts_cnt, 0)) as sql_count, t1.is_reviewed, t1.first_seen, t1.last_seen, t1.id, t1.fingerprint,
                 round(sum(Query_time_sum), 2) as query_sum, round(sum(Lock_time_sum), 2) as lock_sum,
                 sum(Rows_sent_sum) as rows_sent_count, sum(Rows_examined_sum) as rows_exam_sum
                 from db1.mysql_slow_query_review t1
                 left join db1.mysql_slow_query_review_history t2 on t1.checksum = t2.checksum
                 group by t1.checksum
             ) t3 order by {0} desc limit 50;"""
    if(query_type_id <= 0):
        sql = sql.format(query_type[1])
    else:
        sql = sql.format(query_type[query_type_id])
    slow_list = []
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_info = BaseClass(None)
        slow_info.id = row["id"]
        slow_info.checksum = row["checksum"]
        slow_info.sql_count = int(row["sql_count"])
        slow_info.is_reviewed = row["is_reviewed"]
        slow_info.first_seen = row["first_seen"]
        slow_info.last_seen = row["last_seen"]
        slow_info.fingerprint = row["fingerprint"].decode("utf-8")
        slow_info.query_sum = row["query_sum"]
        slow_info.lock_sum = row["lock_sum"]
        slow_info.rows_sent_count = int(row["rows_sent_count"])
        slow_info.rows_exam_sum = int(row["rows_exam_sum"])
        slow_info.display_sql = slow_info.fingerprint[0:60] + "..." if len(slow_info.fingerprint) > 60 else slow_info.fingerprint
        slow_list.append(slow_info)
    return slow_list

def get_slow_log_by_host_id(host_id, query_type_id):
    if(table_config.get(host_id) == None):
        return None

    sql = """select * from
             (
                 select t1.checksum, sum(ifnull(t2.ts_cnt, 0)) as sql_count, t1.is_reviewed, t1.first_seen, t1.last_seen, t1.id, t1.fingerprint,
                 round(sum(Query_time_sum), 2) as query_sum, round(sum(Lock_time_sum), 2) as lock_sum,
                 sum(Rows_sent_sum) as rows_sent_count, sum(Rows_examined_sum) as rows_exam_sum
                 from {0}.{1} t1
                 left join {0}.{2} t2 on t1.checksum = t2.checksum
                 group by t1.checksum
             ) t3 order by {3} desc limit 50;""".format(table_config[host_id].slow_log_db,
                                                        table_config[host_id].slow_log_table,
                                                        table_config[host_id].slow_log_table_history, query_type[query_type_id])

    slow_list = []
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_info = BaseClass(None)
        slow_info.id = row["id"]
        slow_info.checksum = row["checksum"]
        slow_info.sql_count = int(row["sql_count"])
        slow_info.is_reviewed = row["is_reviewed"]
        slow_info.first_seen = row["first_seen"]
        slow_info.last_seen = row["last_seen"]
        slow_info.fingerprint = row["fingerprint"].decode("utf-8")
        slow_info.query_sum = row["query_sum"]
        slow_info.lock_sum = row["lock_sum"]
        slow_info.rows_sent_count = int(row["rows_sent_count"])
        slow_info.rows_exam_sum = int(row["rows_exam_sum"])
        slow_info.display_sql = slow_info.fingerprint[0:60] + "..." if len(slow_info.fingerprint) > 60 else slow_info.fingerprint
        slow_list.append(slow_info)
    return slow_list

def get_slow_log_detail_by_host_id(host_id, checksum):
    sql = """select * from {0}.{1} t1
             left join {0}.{2} t2 on t1.checksum = t2.checksum
             where t1.checksum={3} limit 1;""".format(table_config[host_id].slow_log_db,
                                                        table_config[host_id].slow_log_table,
                                                        table_config[host_id].slow_log_table_history, checksum)
    slow_log_detail = None
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_log_detail = BaseClass(None)
        for key, value in row.items():
            setattr(slow_log_detail, key, value)
    return slow_log_detail

    '''for row in db_util.DBUtil().fetchall(settings.MySQL_Host_Tmp, sql):
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
        slow_log_detail.fingerprint = row["fingerprint"].decode("utf-8")
        slow_log_detail.sample = row["sample"].decode("utf-8")
    return slow_log_detail'''

def load_slow_log_table_config():
    sql = """select host_id, slow_log_db, slow_log_table, slow_log_table_history,
             general_log_db, general_log_table, general_log_table_history
             from mysql_web.slow_general_log_table_config where is_deleted = 0;"""
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        info = BaseClass(None)
        info.host_id = int(row["host_id"])
        info.slow_log_db = row["slow_log_db"]
        info.slow_log_table = row["slow_log_table"]
        info.slow_log_table_history = row["slow_log_table_history"]
        info.general_log_db = row["general_log_db"]
        info.general_log_table = row["general_log_table"]
        info.general_log_table_history = row["general_log_table_history"]
        table_config[info.host_id] = info

