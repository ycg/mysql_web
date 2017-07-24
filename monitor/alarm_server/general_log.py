# -*- coding: utf-8 -*-

import monitor.db_util, settings, monitor.base_class, monitor.slow_log

def get_general_logs_by_date(date):
    sql = """select t1.checksum, t1.fingerprint, t1.first_seen, t2.ts_cnt from
             (
                 SELECT checksum, fingerprint, first_seen FROM db1.general_log_review
                 where first_seen >
             ) t1
             left join db1.general_log_review_history t2 on t1.checksum = t2.checksum"""

def get_general_logs_by_page_index(page_number):
    sql = """select t1.checksum, left(t1.fingerprint, 100) as fingerprint, t1.first_seen, last_seen, is_reviewed,
             (
				select sum(ifnull(ts_cnt, 1)) from db1.general_log_review_history where checksum= t1.checksum
			 ) as ts_cnt
             from db1.general_log_review t1 order by t1.first_seen desc limit {0}, 50""".format((page_number - 1) * 50)

    general_logs = []
    for row in monitor.db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        info = monitor.base_class.BaseClass(None)
        info.checksum = row["checksum"]
        info.fingerprint = row["fingerprint"].decode("utf-8")
        info.first_seen = row["first_seen"]
        info.last_seen = row["last_seen"]
        info.ts_cnt = int(row["ts_cnt"] if row["ts_cnt"] else 0)
        info.is_reviewed = row["is_reviewed"]
        general_logs.append(info)
    return general_logs

def get_general_log_detail(checksum):
    sql = """select t1.checksum, t1.fingerprint, t1.first_seen, last_seen, t2.sample, sum(ifnull(ts_cnt, 1)) as ts_cnt, t1.is_reviewed
             from db1.general_log_review t1
             left join db1.general_log_review_history t2 on t1.checksum = t2.checksum
             where t1.checksum = {0} limit 1""".format(checksum)
    info = monitor.base_class.BaseClass(None)
    for row in monitor.db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        info.checksum = row["checksum"]
        info.fingerprint = row["fingerprint"].decode("utf-8")
        info.first_seen = row["first_seen"]
        info.last_seen = row["last_seen"]
        info.sample = row["sample"].decode("utf-8")
        info.ts_cnt = int(row["ts_cnt"] if row["ts_cnt"] else 0)
        info.is_reviewed = row["is_reviewed"]
    return info

def set_general_log_is_review(checksum):
    sql = "update db1.general_log_review set is_reviewed = 1 where checksum = {0};".format(checksum)
    monitor.db_util.DBUtil().execute(settings.MySQL_Host, sql)
    return "ok"

def set_general_log_is_review_by_host_id(host_id, checksum):
    sql = "update {0}.{1} set is_reviewed = 1 where checksum = {2}".format(monitor.slow_log.table_config[host_id].slow_log_db,
                                                                           monitor.slow_log.table_config[host_id].slow_log_table,
                                                                           checksum)
    monitor.db_util.DBUtil().execute(settings.MySQL_Host, sql)
    return "ok"
