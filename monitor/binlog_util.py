import cache
import datetime, random, time
from entitys import Entity
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent

connection_settings = {}
insert_sql = "INSERT INTO `{0}`.`{1}` ({2}) VALUES ({3});"
update_sql = "UPDATE `{0}`.`{1}` set {2} WHERE {3};"
delete_sql = "DELETE FROM `{0}`.`{1}` WHERE {2};"


def sql_format(dic, split_value):
    list = []
    for key, value in dic.items():
        if (value == None):
            list.append("`%s`=null" % key)
            continue
        if (isinstance(value, int)):
            list.append("`%s`=%d" % (key, value))
        else:
            list.append("`%s`='%s'" % (key, value))
    return split_value.join(list)


def sql_format_for_insert(values):
    list = []
    for value in values:
        if (value == None):
            list.append("null")
            continue
        if (isinstance(value, int)):
            list.append('%d' % value)
        else:
            list.append('\'%s\'' % value)
    return ', '.join(list)


def get_binlog(obj):
    args = Entity()
    args.flashback = False
    args.log_file = obj.log_file
    args.server_id = random.randrange(66666, 99999)
    args.start_pos = obj.start_pos if obj.start_pos else 4
    args.stop_pos = obj.stop_pos if obj.stop_pos else None
    args.stop_datetime = datetime.datetime.strptime(obj.stop_datetime, "%Y-%m-%d %H:%M:%S") if obj.stop_datetime else None
    args.start_datetime = datetime.datetime.strptime(obj.start_datetime, "%Y-%m-%d %H:%M:%S") if obj.start_datetime else None
    args.stop_datetime_timestamp = time.mktime(args.stop_datetime.timetuple()) if obj.stop_datetime else 0
    args.start_datetime_timestamp = time.mktime(args.start_datetime.timetuple()) if obj.start_datetime else 0
    host_info = cache.Cache().get_host_info(obj.host_id)
    args.connection_settings = {"host": host_info.host, "port": host_info.port, "user": host_info.user, "passwd": host_info.password}
    return binlog_process(args)


def binlog_process(args):
    stream = None
    sql_list = []
    try:
        stream = BinLogStreamReader(connection_settings=args.connection_settings, log_file=args.log_file, log_pos=args.start_pos, resume_stream=True, server_id=args.server_id)

        for binlogevent in stream:
            if (args.log_file != stream.log_file):
                break

            if (args.stop_pos != None):
                if (int(binlogevent.packet.log_pos) > int(args.stop_pos)):
                    break

            if (args.start_datetime != None):
                if (binlogevent.timestamp < args.start_datetime_timestamp):
                    continue

            if (args.stop_datetime != None):
                if (binlogevent.timestamp > args.stop_datetime_timestamp):
                    break

            print(binlogevent)
            if (isinstance(binlogevent, WriteRowsEvent)):
                for row in binlogevent.rows:
                    if (args.flashback):
                        sql_list.append(delete_to_sql(row, binlogevent) + "\n")
                    else:
                        sql_list.append(insert_to_sql(row, binlogevent) + "\n")
            elif (isinstance(binlogevent, DeleteRowsEvent)):
                for row in binlogevent.rows:
                    if (args.flashback):
                        sql_list.append(insert_to_sql(row, binlogevent) + "\n")
                    else:
                        sql_list.append(delete_to_sql(row, binlogevent) + "\n")
            elif (isinstance(binlogevent, UpdateRowsEvent)):
                for row in binlogevent.rows:
                    sql_list.append(update_to_sql(row, binlogevent, args.flashback) + "\n")
    finally:
        if (stream != None):
            stream.close()
    return "".join(sql_list)


def insert_to_sql(row, binlogevent):
    return insert_sql.format(binlogevent.schema, binlogevent.table, ', '.join(map(lambda k: '`%s`' % k, row['values'].keys())), sql_format_for_insert(row["values"].values()))


def delete_to_sql(row, binlogevent):
    return delete_sql.format(binlogevent.schema, binlogevent.table, sql_format(row['values'], " AND "))


def update_to_sql(row, binlogevent, flashback):
    if (flashback):
        return update_sql.format(binlogevent.schema, binlogevent.table, sql_format(row['before_values'], ", "), sql_format(row['after_values'], " AND "))
    else:
        return update_sql.format(binlogevent.schema, binlogevent.table, sql_format(row['after_values'], ", "), sql_format(row['before_values'], " AND "))
