# -*- coding: utf-8 -*-

import json, re
import sqlparse
from entitys import BaseClass
import db_util, settings, traceback, cache, common

order_by_options = {1: "last_seen", 2: "Query_time_sum", 3: "ts_cnt", 4: "Lock_time_sum"}


def get_slow_logs(server_id, start_datetime="", stop_datetime="", order_by_type=1, page_number=1, status=2):
    where_sql = ""
    if (len(start_datetime) > 0):
        where_sql += " and a.last_seen >= '{0}'".format(start_datetime)
    if (len(stop_datetime) > 0):
        where_sql += " and a.last_seen <= '{0}'".format(stop_datetime)
    if (status != 2 and status < 2):
        where_sql += " and a.is_reviewed = {0}".format(status)

    sql = """select a.checksum, a.fingerprint, a.first_seen, a.last_seen, a.is_reviewed,
                    b.serverid_max, b.db_max, b.user_max, b.ts_min, b.ts_max, sum(ifnull(b.ts_cnt, 1)) ts_cnt,
                    sum(b.Query_time_sum)/sum(b.ts_cnt) Query_time_avg,
                    max(b.Query_time_max) Query_time_max, min(b.Query_time_min) Query_time_min, sum(b.Query_time_sum) Query_time_sum,
                    sum(b.Lock_time_sum)/sum(b.ts_cnt) Lock_time_avg,
                    max(b.Lock_time_max) Lock_time_max, min(b.Lock_time_min) Lock_time_min, sum(b.Lock_time_sum) Lock_time_sum
             from mysql_web.mysql_slow_query_review a
             inner join mysql_web.mysql_slow_query_review_history b on a.checksum=b.checksum and b.serverid_max={0}
             where 1 = 1 {1}
             group by a.checksum
             order by {2} desc
             limit {3}, 15;"""

    """sql = select t1.*, t2.checksum, t2.fingerprint, t2.first_seen, t2.last_seen, t2.is_reviewed
             from
             (
                 select b.serverid_max, b.db_max, b.user_max, b.ts_min, b.ts_max, sum(b.ts_cnt) ts_cnt,
                        sum(b.Query_time_sum)/sum(b.ts_cnt) Query_time_avg,
                        max(b.Query_time_max) Query_time_max, min(b.Query_time_min) Query_time_min, sum(b.Query_time_sum) Query_time_sum,
                        sum(b.Lock_time_sum)/sum(b.ts_cnt) Lock_time_avg,
                        max(b.Lock_time_max) Lock_time_max, min(b.Lock_time_min) Lock_time_min, sum(b.Lock_time_sum) Lock_time_sum
                 from mysql_web.mysql_slow_query_review_history b
                 where b.serverid_max={0} {1}
                 group by b.checksum
                 order by {2} desc
                 limit {3}, 15
             ) t1 left join mysql_web.mysql_slow_query_review t2 on t1.checksum=t2.checksum"""

    result = []
    sql = sql.format(server_id, where_sql, order_by_options[order_by_type], (page_number - 1) * 15)

    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        info = BaseClass(None)
        info.checksum = row["checksum"]
        info.fingerprint = row["fingerprint"]
        info.fingerprint_tmp = row["fingerprint"].decode("utf-8")[0:35]
        info.first_seen = row["first_seen"]
        info.last_seen = row["last_seen"]
        info.serverid_max = row["serverid_max"]
        info.db_max = row["db_max"]
        info.user_max = row["user_max"]
        info.ts_max = row["ts_max"]
        info.ts_cnt = get_sql_count_value(row["ts_cnt"])
        info.is_reviewed = row["is_reviewed"]
        info.Query_time_avg = get_float(row["Query_time_avg"])
        info.Query_time_max = get_float(row["Query_time_max"])
        info.Query_time_min = get_float(row["Query_time_min"])
        info.Query_time_sum = get_float(row["Query_time_sum"])
        info.Lock_time_max = get_float(row["Lock_time_max"])
        info.Lock_time_min = get_float(row["Lock_time_min"])
        info.Lock_time_sum = get_float(row["Lock_time_sum"])
        info.Lock_time_avg = get_float(row["Lock_time_avg"])
        result.append(info)
    return result


def get_slow_log_detail(checksum, server_id):
    sql = """select t1.checksum, ifnull(t2.ts_cnt, 1) as ts_cnt,  t1.first_seen, t1.last_seen, t1.fingerprint, t2.sample,
             t2.serverid_max, t2.db_max, t2.user_max,
             t2.Query_time_min, t2.Query_time_max, t2.Query_time_sum, t2.Query_time_pct_95,
             Lock_time_sum,Lock_time_min,Lock_time_max,Lock_time_pct_95,
             Rows_sent_sum,Rows_sent_min,Rows_sent_max,Rows_sent_pct_95,
             Rows_examined_sum,Rows_examined_min,Rows_examined_max,Rows_examined_pct_95
             from mysql_web.mysql_slow_query_review t1
             left join mysql_web.mysql_slow_query_review_history t2 on t1.checksum = t2.checksum and t2.serverid_max={0}
             where t1.checksum={1} limit 1;""".format(server_id, checksum)
    slow_log_detail = None
    for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        slow_log_detail = BaseClass(None)
        slow_log_detail.serverid_max = row["serverid_max"]
        slow_log_detail.db_max = row["db_max"]
        slow_log_detail.user_max = row["user_max"]
        slow_log_detail.checksum = row["checksum"]
        slow_log_detail.count = get_sql_count_value(row["ts_cnt"])
        slow_log_detail.query_time_sum = get_float(row["Query_time_sum"])
        slow_log_detail.query_time_max = get_float(row["Query_time_max"])
        slow_log_detail.query_time_min = get_float(row["Query_time_min"])
        slow_log_detail.query_time_pct_95 = get_float(row["Query_time_pct_95"])
        slow_log_detail.lock_time_sum = get_float(row["Lock_time_sum"])
        slow_log_detail.lock_time_max = get_float(row["Lock_time_max"])
        slow_log_detail.lock_time_min = get_float(row["Lock_time_min"])
        slow_log_detail.lock_time_pct_95 = get_float(row["Lock_time_pct_95"])
        slow_log_detail.rows_sent_sum = int(row["Rows_sent_sum"])
        slow_log_detail.rows_sent_max = int(row["Rows_sent_max"])
        slow_log_detail.rows_sent_min = int(row["Rows_sent_min"])
        slow_log_detail.rows_sent_pct_95 = int(row["Rows_sent_pct_95"])
        slow_log_detail.rows_examined_sum = int(row["Rows_examined_sum"])
        slow_log_detail.rows_examined_max = int(row["Rows_examined_max"])
        slow_log_detail.rows_examined_min = int(row["Rows_examined_min"])
        slow_log_detail.rows_examined_pct_95 = int(row["Rows_examined_pct_95"])
        slow_log_detail.first_seen = row["first_seen"]
        slow_log_detail.last_seen = row["last_seen"]
        slow_log_detail.fingerprint = row["fingerprint"].decode("utf-8")
        slow_log_detail.sample = sqlparse.format(row["sample"].decode("utf-8"), reindent=True, keyword_case='upper')
    slow_log_detail.table_infos = get_table_infos(server_id, slow_log_detail.db_max, slow_log_detail.sample)
    slow_log_detail.explain_infos = get_slow_log_explain(server_id, slow_log_detail.db_max, slow_log_detail.sample)
    return slow_log_detail


def get_slow_log_explain(server_id, db, sql):
    result = []
    connection, cursor = None, None
    host_info = cache.Cache().get_host_info(server_id)
    try:
        connection, cursor = db_util.DBUtil().get_conn_and_cur(host_info)
        cursor.execute("use {0};".format(db))
        cursor.execute("explain {0};".format(sql))
        for row in cursor.fetchall():
            info = BaseClass(None)
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
    except Exception, e:
        traceback.print_exc()
    finally:
        db_util.DBUtil().close(connection, cursor)
    return result


def update_review_detail(obj):
    sql = "update mysql_web.mysql_slow_query_review " \
          "set comments='{0}', is_reviewed=1 ,reviewed_id={1}, reviewed_on=now() " \
          "where checksum={2};".format(db_util.DBUtil().escape(obj.comments), obj.user_id, obj.checksum)
    db_util.DBUtil().fetchone(settings.MySQL_Host, sql)
    return "save success"


def get_review_detail_by_checksum(checksum):
    sql = "select is_reviewed, comments, reviewed_on, reviewed_id " \
          "from mysql_web.mysql_slow_query_review where checksum={0}".format(checksum)
    info = BaseClass(None)
    result = db_util.DBUtil().fetchone(settings.MySQL_Host, sql)
    info.checksum = checksum
    info.reviewed_id = result["reviewed_id"]
    info.is_reviewed = result["is_reviewed"]
    info.comments = result["comments"] if result["comments"] else ""
    info.reviewed_on = result["reviewed_on"].strftime('%Y-%m-%d %H:%M:%S') if result["reviewed_on"] else ""
    return json.dumps(info, default=lambda o: o.__dict__, skipkeys=True, ensure_ascii=False)


def get_float(value):
    if (value == None):
        return str(0)
    return str("%.5f" % value)


def get_sql_count_value(value):
    value = int(value)
    if (value <= 1000):
        return value
    if (value <= 10000):
        return str(round(float(value) / float(1000), 1)) + "k"
    return str(value / 1000) + "k"


def get_table_infos(host_id, db_name, sql):
    if (db_name == None):
        return None
    try:
        number = 1
        table_infos = []
        table_names = QueryTableParser().parse(sql)
        host_info = cache.Cache().get_host_info(host_id)
        for name in table_names:
            entity = BaseClass(None)
            values = name.split(".")
            if (len(values) > 1):
                db_name_tmp = values[0]
                table_name_tmp = values[1]
            else:
                db_name_tmp = db_name
                table_name_tmp = name
            entity.key = number
            entity.table_name_full = (db_name_tmp + "." + table_name_tmp).lower()
            entity.index_infos = get_show_index(host_info, entity.table_name_full)
            entity.status_info = get_show_table_status(host_info, db_name_tmp, table_name_tmp)
            entity.create_table_info = get_show_create_table(host_info, entity.table_name_full)
            table_infos.append(entity)
            number += 1
        return table_infos
    except:
        traceback.print_exc()
        return None


def get_show_index(host_info, table_name):
    index_infos = []
    rows = db_util.DBUtil().fetchall(host_info, "show index from {0};".format(table_name))
    for row_info in rows:
        index_infos.append(common.get_object(row_info))
    return index_infos


def get_show_create_table(host_info, table_name):
    return db_util.DBUtil().fetchone(host_info, "show create table {0};".format(table_name))["Create Table"]


def get_show_table_status(host_info, db_name, table_name):
    result = db_util.DBUtil().fetchone(host_info, "show table status from {0} like '{1}';".format(db_name, table_name))
    return common.get_object(result)


class QueryTableParser(object):
    """
    获取任意一个sql语句中使用到 有效表名
    默认返回 返回一个空的元组集合
    """

    def __init__(self):
        self.pos = 0
        self.len = 0
        self.query = ""
        self.flag = 0
        self.table_tokens = [
            'from',
            'join',
            'update',
            'into'
        ]
        self.table_filter_tokens = [
            'where',
            '(',
            ')'
        ]

    def parse(self, sql):
        """
        解析表名
        :param sql: 需要解析的 SQL 语句
        :return: 返回一个元组集合
        """
        # 替换 sql 文本中的任意空白字符为 空格, 并在逗号后面添加一个空格
        self.query = re.subn("\s+", " ", sql.upper())[0]
        self.query = re.subn("\s+,", ", ", self.query)[0]
        self.query = re.subn(",", ", ", self.query)[0]
        self.query = re.subn("\)", " ) ", self.query)[0]
        self.query = re.subn("\s+", " ", self.query)[0]
        self.query = re.subn("\s+\)", ")", self.query)[0]

        # 计算长度sql文本长度
        self.len = len(self.query)

        tables = []
        # 判断是否到了 SQL 文本末尾
        while self.has_next_token():
            # 获取两个空格之间的单词
            token = self.get_next_token()
            # 判断 token 是否在 table_tokens 中
            if self.table_tokens.count(token.lower()) or self.flag:
                # 如果在， 这边就开始获取表名

                # 这边处理别名问题
                if self.flag:
                    table_name = token
                else:
                    table_name = self.get_next_token()

                '''
                表名有个特性，字母开头，由下划线和数字组成， 这符合正则表达式中的 \w
                分隔出来的表名，可能是
                "table_name, table_name", "table_name", "table_name aa, table_name""
                "`table_name`, `table_name`", "`table_name`"
                '''
                # 匹配表名中有逗号
                if re.search(",", table_name):

                    # 表格式为 "table_name1, table_name2"
                    # 查找到 table_name1
                    while re.search(",", table_name):
                        if re.search('\w+', table_name.strip('`')):
                            table = re.sub('`', '', table_name.strip(','))
                            tables.append(table.strip(';'))
                        table_name = self.get_next_token()

                    # 查找到 table_name2
                    if re.search('\w+', table_name.strip('`')):
                        table = re.sub('`', '', table_name)
                        tables.append(table.strip(';'))
                # 匹配表名中没有逗号
                else:
                    # 判断表名是不是 where 和 ( 开头，是否继续下一个单词过滤
                    if self.table_filter_tokens.count(table_name.lower()) \
                            or table_name.startswith('('):
                        continue
                    if re.search('\w+', table_name.strip('`')):
                        table = re.sub('`', '', table_name)
                        tables.append(table.strip(';').strip(')'))

                    # 判断是否为别名
                    table_name = self.get_next_token()
                    if re.search(',', table_name):
                        self.flag = 1
                    else:
                        self.flag = 0
        if "DUAL" in tables:
            tables.remove("DUAL")
        return set(tables)

    def has_next_token(self):
        """
        判断是否已经全部检查完了
        :return: 返回 True or False
        """
        if self.pos >= self.len:
            return False
        return True

    def get_next_token(self):
        """
        获取按空格分隔后的每个单词，用于判断是否在self.table_tokens中
        :return: 返回两个空格之间的单词
        """
        # 从 sql 文本 self.pos 位置开始，搜索第一个空格
        # 比如 self.pos 为10， 那么是从 sql 文本中的第10个字符位置开始查找
        pos_flag = re.search("\s", self.query[self.pos:])

        # 没有搜索到，表示已经到sql文本末尾了
        if not pos_flag:
            pos = self.len
        else:
            # print(pos_flag)
            # --> <_sre.SRE_Match object; span=(5, 6), match=' '>
            # 这边表示搜索到的空格在原sql文本中的位置
            pos = pos_flag.span()[0] + self.pos
        start = self.pos
        end = pos
        self.pos = pos + 1
        return self.query[start:end]
