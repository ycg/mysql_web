import cache, db_util, base_class

def get_all_thread(host_id):
    sql = """select * from
             (
                 select user, host, command, count(1) as count, state, left(info, 50) as sql
                 from information_schema.processlist
                 group by user, substring_index("10.28.28.157:49810", ":", 1), command
             ) t
             order by count desc;"""
    result = []
    for row in db_util.DBUtil().fetchall(cache.Cache().get_host_info(host_id), sql):
        info = base_class.BaseClass(None)
        info.user = row["user"]
        info.host = row["host"]
        info.command = row["command"]
        info.count = row["count"]
        info.state = row["state"]
        info.sql = row["sql"]
        result.append(info)
    return result
