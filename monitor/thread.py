import cache, db_util, base_class

def get_all_thread(host_id, query_type):
    sql = """select * from
             (
                 select user, host, command, count(1) as count, state, info as sql_value
                 from information_schema.processlist where 1 = 1 {0}
                 group by user, substring_index(host, ':', 1), command
             ) t
             order by count desc;"""
    where_sql = ""
    if(query_type == 2):
        where_sql = "and command = 'Sleep'"
    elif(query_type == 3):
        where_sql = "and command != 'Sleep'"
    result = []
    for row in db_util.DBUtil().fetchall(cache.Cache().get_host_info(host_id), sql.format(where_sql)):
        info = base_class.BaseClass(None)
        info.user = row["user"]
        info.host = row["host"]
        info.command = row["command"]
        info.count = row["count"]
        info.state = row["state"]
        info.sql = row["sql_value"]
        result.append(info)
    return result
