# -*- coding: utf-8 -*-

import time, threadpool, cache, threading, db_util, enum, host_info

class MonitorEnum(enum.Enum):
    Status = 0
    Innodb = 1
    Replication = 2

class MonitorServer(threading.Thread):
    __cache = None
    __db_util = None
    __instance = None
    __thread_pool = None

    def __init__(self):
        self.__cache = cache.Cache()
        self.__db_util = db_util.DBUtil()
        self.__thread_pool = threadpool.ThreadPool(36)
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def __new__(cls, *args, **kwargs):
        if(MonitorServer.__instance is None):
            MonitorServer.__instance = object.__new__(cls, *args, **kwargs)
        return MonitorServer.__instance

    def run(self):
        while (True):
            requests = threadpool.makeRequests(self.get_mysql_status, list(self.__cache.get_all_host_infos()), None)
            for request in requests:
                self.__thread_pool.putRequest(request)
            self.__thread_pool.poll()
            time.sleep(1)

    def get_mysql_status(self, host_info):
        aa = time.time()
        mysql_status_old = self.get_dic_data(host_info, "show global status;")
        time.sleep(1)
        mysql_status_new = self.get_dic_data(host_info, "show global status;")
        mysql_variables = self.get_dic_data(host_info, "show global variables;")

        #1.---------------------------------------------------------获取mysql global status--------------------------------------------------------
        status_info = self.__cache.get_status_infos(host_info.key)
        status_info.binlog_cache_hit = 0
        status_info.connections = int(mysql_status_new["Connections"])
        status_info.open_files = int(mysql_status_new["Open_files"])
        status_info.opened_files = int(mysql_status_new["Opened_files"])
        status_info.open_tables = int(mysql_status_new["Open_tables"])
        status_info.openend_tables = int(mysql_status_new["Opened_tables"])
        status_info.thread_created = int(mysql_status_new["Threads_created"])
        status_info.threads_count = int(mysql_status_new["Threads_connected"])
        status_info.threads_run_count = int(mysql_status_new["Threads_running"])
        status_info.binlog_cache_use = int(mysql_status_new["Binlog_cache_use"])
        status_info.binlog_cache_disk_use = int(mysql_status_new["Binlog_cache_disk_use"])
        status_info.qps = int(mysql_status_new["Questions"]) - int(mysql_status_old["Questions"])
        status_info.select_count = int(mysql_status_new["Com_select"]) - int(mysql_status_old["Com_select"])
        status_info.insert_count = int(mysql_status_new["Com_insert"]) - int(mysql_status_old["Com_insert"])
        status_info.update_count = int(mysql_status_new["Com_update"]) - int(mysql_status_old["Com_update"])
        status_info.delete_count = int(mysql_status_new["Com_delete"]) - int(mysql_status_old["Com_delete"])
        status_info.commit = int(mysql_status_new["Com_commit"]) - int(mysql_status_old["Com_commit"])
        status_info.rollback = int(mysql_status_new["Com_rollback"]) - int(mysql_status_old["Com_rollback"])
        status_info.connections_per = int(mysql_status_new["Connections"]) - int(mysql_status_old["Connections"])
        status_info.create_tmp_files = int(mysql_status_new["Created_tmp_files"]) - int(mysql_status_old["Created_tmp_files"])
        status_info.create_tmp_table_count = int(mysql_status_new["Created_tmp_tables"]) - int(mysql_status_old["Created_tmp_tables"])
        status_info.create_tmp_disk_table_count = int(mysql_status_new["Created_tmp_disk_tables"]) - int(mysql_status_old["Created_tmp_disk_tables"])
        status_info.thread_cache_hit = (1 - status_info.thread_created / status_info.connections) * 100
        status_info.connections_usage_rate = status_info.threads_count * 100 / int(mysql_variables["max_connections"])
        status_info.send_bytes = self.get_data_length(int(mysql_status_new["Bytes_sent"]) - int(mysql_status_old["Bytes_sent"]))
        status_info.receive_bytes = self.get_data_length(int(mysql_status_new["Bytes_received"])  - int(mysql_status_old["Bytes_received"]))
        status_info.tps = (int(mysql_status_new["Com_commit"]) + int(mysql_status_new["Com_rollback"])) - (int(mysql_status_old["Com_commit"]) + int(mysql_status_old["Com_rollback"]))
        if(status_info.binlog_cache_use > 0):
            #从库没有写binlog，所以这边要判断下
            status_info.binlog_cache_hit = (1 - status_info.binlog_cache_disk_use / status_info.binlog_cache_use) * 100
        #Handler_read
        status_info.handler_read_first = int(mysql_status_new["Handler_read_first"]) - int(mysql_status_old["Handler_read_first"])
        status_info.handler_read_key = int(mysql_status_new["Handler_read_key"]) - int(mysql_status_old["Handler_read_key"])
        status_info.handler_read_next = int(mysql_status_new["Handler_read_next"]) - int(mysql_status_old["Handler_read_next"])
        status_info.handler_read_last = int(mysql_status_new["Handler_read_last"]) - int(mysql_status_old["Handler_read_last"])
        status_info.handler_read_rnd = int(mysql_status_new["Handler_read_rnd"]) - int(mysql_status_old["Handler_read_rnd"])
        status_info.handler_read_rnd_next = int(mysql_status_new["Handler_read_rnd_next"]) - int(mysql_status_old["Handler_read_rnd_next"])

        #2.---------------------------------------------------------获取innodb的相关数据-------------------------------------------------------------------
        innodb_info = self.__cache.get_innodb_infos(host_info.key)
        innodb_info.trxs = 0
        innodb_info.current_row_locks = 0
        innodb_info.history_list_length = 0
        innodb_info.buffer_pool_reads = int(mysql_status_new["Innodb_buffer_pool_reads"])
        innodb_info.buffer_pool_read_requests = int(mysql_status_new["Innodb_buffer_pool_read_requests"])
        innodb_info.rows_read = int(mysql_status_new["Innodb_rows_read"]) - int(mysql_status_old["Innodb_rows_read"])
        innodb_info.rows_updated = int(mysql_status_new["Innodb_rows_updated"]) - int(mysql_status_old["Innodb_rows_updated"])
        innodb_info.rows_deleted = int(mysql_status_new["Innodb_rows_deleted"]) - int(mysql_status_old["Innodb_rows_deleted"])
        innodb_info.rows_inserted = int(mysql_status_new["Innodb_rows_inserted"]) - int(mysql_status_old["Innodb_rows_inserted"])
        innodb_info.page_dirty_count = int(mysql_status_new["Innodb_buffer_pool_pages_dirty"])
        innodb_info.page_free_count = int(mysql_status_new["Innodb_buffer_pool_pages_free"])
        innodb_info.page_total_count = int(mysql_status_new["Innodb_buffer_pool_pages_total"])
        innodb_info.page_flush_persecond = int(mysql_status_new["Innodb_buffer_pool_pages_flushed"]) - int(mysql_status_old["Innodb_buffer_pool_pages_flushed"])
        innodb_info.commit = int(mysql_status_new["Com_commit"]) - int(mysql_status_old["Com_commit"])
        innodb_info.rollback = int(mysql_status_new["Com_rollback"]) - int(mysql_status_old["Com_rollback"])
        innodb_info.buffer_pool_hit = (1 - innodb_info.buffer_pool_reads / innodb_info.buffer_pool_read_requests) * 100
        if(mysql_status_new.get("Innodb_history_list_length") != None):
            #percona
            innodb_info.history_list_length = int(mysql_status_new["Innodb_history_list_length"])
        if(mysql_status_new.get("Innodb_current_row_locks") != None):
            #percona
            innodb_info.current_row_locks = mysql_status_new["Innodb_current_row_locks"]
        elif(mysql_status_new.get("Innodb_row_lock_current_waits") != None):
            #mysql
            innodb_info.current_row_locks = mysql_status_new["Innodb_row_lock_current_waits"]
        #innodb log info
        innodb_info.innodb_log_writes = int(mysql_status_new["Innodb_log_writes"]) - int(mysql_status_old["Innodb_log_writes"])
        innodb_info.innodb_log_waits = int(mysql_status_new["Innodb_log_waits"])
        innodb_info.innodb_os_log_pending_fsyncs = int(mysql_status_new["Innodb_os_log_pending_fsyncs"])
        innodb_info.innodb_os_log_pending_writes = int(mysql_status_new["Innodb_os_log_pending_writes"])
        innodb_info.innodb_os_log_written = int(mysql_status_new["Innodb_os_log_written"]) - int(mysql_status_old["Innodb_os_log_written"])
        innodb_info.innodb_row_lock_waits = int(mysql_status_new["Innodb_row_lock_waits"]) - int(mysql_status_old["Innodb_row_lock_waits"])

        #3.-----------------------------------------------------获取replcation status-------------------------------------------------------------------
        #if (host_info.is_slave > 0):
        result = self.__db_util.fetchone(host_info, "show slave status;")
        if(result != None):
            repl_info = self.__cache.get_repl_info(host_info.key)
            repl_info.error_message = result["Last_Error"]
            repl_info.io_status = result["Slave_IO_Running"]
            repl_info.sql_status = result["Slave_SQL_Running"]
            repl_info.master_log_file = result["Master_Log_File"]
            repl_info.master_log_pos = int(result["Read_Master_Log_Pos"])
            repl_info.slave_log_file = result["Relay_Master_Log_File"]
            repl_info.slave_log_pos = int(result["Exec_Master_Log_Pos"])
            repl_info.slave_retrieved_gtid_set = result["Retrieved_Gtid_Set"]
            repl_info.slave_execute_gtid_set = result["Executed_Gtid_Set"]
            repl_info.delay_pos_count = repl_info.master_log_pos - repl_info.slave_log_pos

        self.insert_status_log(status_info)
        bb = time.time()
        print(bb - aa - 1)

    def get_data_length(self, data_length):
        value = float(1024)
        if(data_length > value):
            result = round(data_length / value, 0)
            if(result > value):
                return str(int(round(result / value, 0))) + "M"
            else:
                return str(int(result)) + "K"
        else:
            return str(data_length) + "KB"

    def get_dic_data(self, host_info, sql):
        data = {}
        for row in self.__db_util.fetchall(host_info, sql):
             data[row.get("Variable_name")] = row.get("Value")
        return data

    def get_cache_by_type(self, monitor_type):
        if(monitor_type == MonitorEnum.Status):
            return self.__cache.get_all_status_infos()
        elif(monitor_type == MonitorEnum.Innodb):
            return self.__cache.get_all_innodb_infos()
        elif(monitor_type == MonitorEnum.Replication):
            return self.__cache.get_all_repl_infos()

    def insert_status_log(self, status_info):
        monitor_host_info = host_info.HoseInfo(host="192.168.11.128", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")
        sql = "insert into mysql_web.mysql_status_log(host_id, qps, tps, commit, rollback, connections, " \
              "thread_count, thread_running_count, tmp_tables, tmp_disk_tables, send_bytes, receive_bytes) VALUES " \
              "({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, \'{10}\', \'{11}\')"\
              .format(status_info.host_info.id, status_info.qps, status_info.tps, status_info.commit, status_info.rollback, status_info.connections_per,
                      status_info.threads_count, status_info.threads_run_count, status_info.create_tmp_table_count, status_info.create_tmp_disk_table_count,
                      status_info.send_bytes, status_info.receive_bytes)
        self.__db_util.execute(monitor_host_info, sql)