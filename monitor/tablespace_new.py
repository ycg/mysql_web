# -*- coding: utf-8 -*-

import time
import db_util, settings, cache, common, entitys


def get_table_infos(host_info):
    table_infos = {}
    db_names = db_util.DBUtil().fetchall(host_info, "show databases;")
    for db_name in db_names:
        sql = """select table_schema, table_name, DATA_LENGTH, INDEX_LENGTH, TABLE_ROWS, AUTO_INCREMENT, create_time, engine, update_time
                 from information_schema.tables
                 where table_schema = '{0}'
                 and table_schema != 'mysql' and table_schema != 'information_schema' and table_schema != 'performance_schema' and table_schema != 'sys'""".format(db_name["Database"])
        for row in db_util.DBUtil().fetchall(host_info, sql):
            table_info = entitys.Entity()
            table_info.schema = row["table_schema"]
            table_info.t_name = row["table_name"]
            table_info.rows = row["TABLE_ROWS"]
            table_info.data_size = row["DATA_LENGTH"] if row["DATA_LENGTH"] else 0
            table_info.index_size = row["INDEX_LENGTH"] if row["INDEX_LENGTH"] else 0
            table_info.auto_increment = row["AUTO_INCREMENT"] if row["AUTO_INCREMENT"] else 0
            table_info.total_size = long(table_info.data_size) + long(table_info.index_size)
            table_info.create_time = row["create_time"]
            table_info.update_time = row["update_time"] if row["update_time"] else ''
            table_info.engine = row["engine"]
            table_name = row["table_schema"] + "." + row["table_name"]
            table_infos[table_name] = table_info
    return table_infos
