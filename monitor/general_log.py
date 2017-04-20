# -*- coding: utf-8 -*-

import db_util, settings, base_class

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
				select sum(ts_cnt) from db1.general_log_review_history where checksum= t1.checksum
			 ) as ts_cnt
             from db1.general_log_review t1 order by t1.first_seen desc limit {0}, 50""".format(page_number * 50)

    general_logs = []
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host_Tmp, sql):
        info = base_class.BaseClass(None)
        info.checksum = row["checksum"]
        info.fingerprint = row["fingerprint"].decode("utf-8")
        info.first_seen = row["first_seen"]
        info.last_seen = row["last_seen"]
        info.ts_cnt = int(row["ts_cnt"] if row["ts_cnt"] else 0)
        info.is_reviewed = row["is_reviewed"]
        general_logs.append(info)
    return general_logs

def get_general_log_detail(checksum):
    sql = """select t1.checksum, t1.fingerprint, t1.first_seen, last_seen, t2.sample, sum(t2.ts_cnt) as ts_cnt, t1.is_reviewed
             from db1.general_log_review t1
             left join db1.general_log_review_history t2 on t1.checksum = t2.checksum
             where t1.checksum = '{0}' limit 1""".format(checksum)
    info = base_class.BaseClass(None)
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host_Tmp, sql):
        info.checksum = row["checksum"]
        info.fingerprint = row["fingerprint"].decode("utf-8")
        info.first_seen = row["first_seen"]
        info.last_seen = row["last_seen"]
        info.sample = row["sample"].decode("utf-8")
        info.ts_cnt = int(row["ts_cnt"] if row["ts_cnt"] else 0)
        info.is_reviewed = row["is_reviewed"]
    return info


