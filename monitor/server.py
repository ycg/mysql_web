# -*- coding: utf-8 -*-

import traceback
import cache, db_util, settings, base_class, mysql_branch, tablespace
import time, threadpool, threading, enum, paramiko, collections, pymysql

class MonitorEnum(enum.Enum):
    mysql = 4
    host = 3
    status = 0
    innodb = 1
    replication = 2

class MonitorServer(threading.Thread):
    __times = 1
    __cache = None
    __db_util = None
    __instance = None
    __thread_pool = None
    __ssh_client_dict = {}

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if (cls.__instance is None):
            MonitorServer.__instance = object.__new__(cls, *args, **kwargs)
        return MonitorServer.__instance

    def load(self):
        self.__cache = cache.Cache()
        self.__db_util = db_util.DBUtil()
        self.__thread_pool = threadpool.ThreadPool(settings.THREAD_POOL_SIZE)
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while (True):
            try:
                if (self.__times % settings.UPDATE_INTERVAL == 0):
                    self.__cache.join_thread_pool(self.get_mysql_status)
                if (self.__times % settings.UPDATE_INTERVAL == 0):
                    if (settings.LINUX_OS):
                        self.__cache.join_thread_pool(self.monitor_host_status)
                        self.__cache.join_thread_pool(self.monitor_host_for_cpu_and_io)
                if (self.__times % settings.TABLE_CHECK_INTERVAL == 0):
                    self.__cache.join_thread_pool(tablespace.get_tablespace_infos)
            except Exception as e:
                traceback.print_exc()
            time.sleep(1)
            self.__times += 1

    def invoke_check_tablespace_method(self):
        self.__cache.join_thread_pool(tablespace.get_tablespace_infos)

    def get_mysql_status(self, host_info):
        host_info.is_running = 1
        connection = self.__db_util.get_mysql_connection(host_info)
        cursor = connection.cursor()

        try:
            mysql_status_old = self.get_dic_data(cursor, show_global_status_sql)
        except pymysql.err.OperationalError:
            traceback.print_exc()
            host_info.is_running = 0
            return

        time.sleep(1)
        mysql_status_new = self.get_dic_data(cursor, show_global_status_sql)
        mysql_variables = self.get_dic_data(cursor, "show global variables where variable_name in ('datadir', 'pid_file', 'log_bin', 'log_bin_basename', "
                                                    "'max_connections', 'table_open_cache', 'table_open_cache_instances', 'innodb_buffer_pool_size', "
                                                    "'read_only', 'log_bin', 'innodb_spin_wait_delay', 'innodb_sync_spin_loops');")
        host_info.uptime = int(mysql_status_new["Uptime"]) / 60 / 60 / 24
        if (host_info.uptime == 0):
            host_info.uptime = 1

        # 1.---------------------------------------------------------获取mysql global status--------------------------------------------------------
        status_info = self.__cache.get_status_info(host_info.key)
        status_info.open_files = int(mysql_status_new["Open_files"])
        status_info.opened_files = int(mysql_status_new["Opened_files"])
        status_info.send_bytes_bigint = int(mysql_status_new["Bytes_sent"]) - int(mysql_status_old["Bytes_sent"])
        status_info.receive_bytes_bigint = int(mysql_status_new["Bytes_received"]) - int(mysql_status_old["Bytes_received"])
        status_info.send_bytes = self.get_data_length(int(mysql_status_new["Bytes_sent"]) - int(mysql_status_old["Bytes_sent"]))
        status_info.receive_bytes = self.get_data_length(int(mysql_status_new["Bytes_received"]) - int(mysql_status_old["Bytes_received"]))

        # tps and qps
        status_info.qps = int(mysql_status_new["Questions"]) - int(mysql_status_old["Questions"])
        status_info.select_count = int(mysql_status_new["Com_select"]) - int(mysql_status_old["Com_select"])
        status_info.insert_count = int(mysql_status_new["Com_insert"]) - int(mysql_status_old["Com_insert"])
        status_info.update_count = int(mysql_status_new["Com_update"]) - int(mysql_status_old["Com_update"])
        status_info.delete_count = int(mysql_status_new["Com_delete"]) - int(mysql_status_old["Com_delete"])
        status_info.commit = int(mysql_status_new["Com_commit"]) - int(mysql_status_old["Com_commit"])
        status_info.rollback = int(mysql_status_new["Com_rollback"]) - int(mysql_status_old["Com_rollback"])
        status_info.tps = status_info.insert_count + status_info.update_count + status_info.delete_count
        if (mysql_status_new.get("Innodb_max_trx_id") != None):
            # percona
            status_info.trx_count = int(mysql_status_new["Innodb_max_trx_id"]) - int(mysql_status_old["Innodb_max_trx_id"])
        status_info.slow_queries = int(mysql_status_new["Slow_queries"]) - int(mysql_status_old["Slow_queries"])

        # thread and connection
        status_info.connections = int(mysql_status_new["Connections"])
        status_info.thread_created = int(mysql_status_new["Threads_created"])
        status_info.threads_count = int(mysql_status_new["Threads_connected"])
        status_info.threads_run_count = int(mysql_status_new["Threads_running"])
        status_info.thread_cache_hit = (1 - status_info.thread_created / status_info.connections) * 100
        status_info.connections_per = int(mysql_status_new["Connections"]) - int(mysql_status_old["Connections"])
        status_info.connections_usage_rate = status_info.threads_count * 100 / int(mysql_variables["max_connections"])
        status_info.aborted_clients = int(mysql_status_new["Aborted_clients"]) - int(mysql_status_old["Aborted_clients"])
        status_info.aborted_connects = int(mysql_status_new["Aborted_connects"]) - int(mysql_status_old["Aborted_connects"])

        # 监控time>1的线程数量
        result = self.__db_util.fetchone(host_info, "select count(1) as t_count from information_schema.processlist where length(state) > 0 and length(info) > 0 and time > 1;")
        if (len(result) > 0):
            status_info.thread_waits_count = int(result["t_count"])

        # binlog cache
        status_info.binlog_cache_use = int(mysql_status_new["Binlog_cache_use"])
        status_info.binlog_cache_disk_use = int(mysql_status_new["Binlog_cache_disk_use"])
        if (status_info.binlog_cache_use > 0):
            # 从库没有写binlog，所以这边要判断下
            status_info.binlog_cache_hit = (1 - status_info.binlog_cache_disk_use / status_info.binlog_cache_use) * 100
        else:
            status_info.binlog_cache_hit = 0

        # Handler_read
        status_info.handler_commit = int(mysql_status_new["Handler_commit"]) - int(mysql_status_old["Handler_commit"])
        status_info.handler_rollback = int(mysql_status_new["Handler_rollback"]) - int(mysql_status_old["Handler_rollback"])
        status_info.handler_read_first = int(mysql_status_new["Handler_read_first"]) - int(mysql_status_old["Handler_read_first"])
        status_info.handler_read_key = int(mysql_status_new["Handler_read_key"]) - int(mysql_status_old["Handler_read_key"])
        status_info.handler_read_next = int(mysql_status_new["Handler_read_next"]) - int(mysql_status_old["Handler_read_next"])
        status_info.handler_read_last = int(mysql_status_new["Handler_read_last"]) - int(mysql_status_old["Handler_read_last"])
        status_info.handler_read_rnd = int(mysql_status_new["Handler_read_rnd"]) - int(mysql_status_old["Handler_read_rnd"])
        status_info.handler_read_rnd_next = int(mysql_status_new["Handler_read_rnd_next"]) - int(mysql_status_old["Handler_read_rnd_next"])
        status_info.handler_update = int(mysql_status_new["Handler_update"]) - int(mysql_status_old["Handler_update"])
        status_info.handler_write = int(mysql_status_new["Handler_write"]) - int(mysql_status_old["Handler_write"])
        status_info.handler_delete = int(mysql_status_new["Handler_delete"]) - int(mysql_status_old["Handler_delete"])

        # open table cache
        status_info.table_open_cache = int(mysql_variables["table_open_cache"])
        status_info.table_open_cache_instances = int(mysql_variables["table_open_cache_instances"])
        status_info.open_tables = int(mysql_status_new["Open_tables"])
        status_info.openend_tables = int(mysql_status_new["Opened_tables"]) - int(mysql_status_old["Opened_tables"])
        status_info.table_open_cache_hits = int(mysql_status_new["Table_open_cache_hits"]) - int(mysql_status_old["Table_open_cache_hits"])
        status_info.table_open_cache_misses = int(mysql_status_new["Table_open_cache_misses"]) - int(mysql_status_old["Table_open_cache_misses"])
        status_info.table_open_cache_overflows = int(mysql_status_new["Table_open_cache_overflows"]) - int(mysql_status_old["Table_open_cache_overflows"])
        status_info.open_files = int(mysql_status_new["Open_files"])
        status_info.opened_files = int(mysql_status_new["Opened_files"]) - int(mysql_status_old["Opened_files"])

        # tmp table create
        status_info.create_tmp_files = int(mysql_status_new["Created_tmp_files"]) - int(mysql_status_old["Created_tmp_files"])
        status_info.create_tmp_table_count = int(mysql_status_new["Created_tmp_tables"]) - int(mysql_status_old["Created_tmp_tables"])
        status_info.create_tmp_disk_table_count = int(mysql_status_new["Created_tmp_disk_tables"]) - int(mysql_status_old["Created_tmp_disk_tables"])

        # table lock
        status_info.table_locks_immediate = int(mysql_status_new["Table_locks_immediate"]) - int(mysql_status_old["Table_locks_immediate"])
        status_info.table_locks_waited = int(mysql_status_new["Table_locks_waited"]) - int(mysql_status_old["Table_locks_waited"])

        # select sort
        status_info.select_full_join = int(mysql_status_new["Select_full_join"]) - int(mysql_status_old["Select_full_join"])
        status_info.select_scan = int(mysql_status_new["Select_scan"]) - int(mysql_status_old["Select_scan"])
        status_info.select_full_range_join = int(mysql_status_new["Select_full_range_join"]) - int(mysql_status_old["Select_full_range_join"])
        status_info.select_range_check = int(mysql_status_new["Select_range_check"]) - int(mysql_status_old["Select_range_check"])
        status_info.select_range = int(mysql_status_new["Select_range"]) - int(mysql_status_old["Select_range"])
        status_info.sort_merge_passes = int(mysql_status_new["Sort_merge_passes"]) - int(mysql_status_old["Sort_merge_passes"])
        status_info.sort_range = int(mysql_status_new["Sort_range"]) - int(mysql_status_old["Sort_range"])
        status_info.sort_scan = int(mysql_status_new["Sort_scan"]) - int(mysql_status_old["Sort_scan"])

        # 2.---------------------------------------------------------获取innodb的相关数据-------------------------------------------------------------------
        innodb_info = self.__cache.get_innodb_info(host_info.key)
        innodb_info.commit = status_info.commit
        innodb_info.rollback = status_info.rollback
        innodb_info.trx_count = status_info.trx_count

        # row locks
        if (mysql_status_new.get("Innodb_history_list_length") != None):
            # percona
            innodb_info.history_list_length = int(mysql_status_new["Innodb_history_list_length"])
        if (mysql_status_new.get("Innodb_current_row_locks") != None):
            # percona
            innodb_info.current_row_locks = mysql_status_new["Innodb_current_row_locks"]
        elif (mysql_status_new.get("Innodb_row_lock_current_waits") != None):
            # mysql
            innodb_info.current_row_locks = mysql_status_new["Innodb_row_lock_current_waits"]
        innodb_info.innodb_row_lock_waits = int(mysql_status_new["Innodb_row_lock_waits"]) - int(mysql_status_old["Innodb_row_lock_waits"])
        innodb_info.innodb_row_lock_time = int(mysql_status_new["Innodb_row_lock_time"]) - int(mysql_status_old["Innodb_row_lock_time"])
        innodb_info.innodb_row_lock_time_avg = int(mysql_status_new["Innodb_row_lock_time_avg"])
        innodb_info.innodb_row_lock_time_max = int(mysql_status_new["Innodb_row_lock_time_max"])
        if (mysql_status_new.get("Innodb_deadlocks") == None):
            innodb_info.innodb_deadlocks = 0
        else:
            innodb_info.innodb_deadlocks = int(mysql_status_new["Innodb_deadlocks"]) - int(mysql_status_old["Innodb_deadlocks"])

        # innodb redo log info
        innodb_info.innodb_log_waits = int(mysql_status_new["Innodb_log_waits"])
        innodb_info.innodb_log_writes = int(mysql_status_new["Innodb_log_writes"]) - int(mysql_status_old["Innodb_log_writes"])
        innodb_info.innodb_log_write_requests = int(mysql_status_new["Innodb_log_write_requests"]) - int(mysql_status_old["Innodb_log_write_requests"])
        innodb_info.innodb_os_log_pending_fsyncs = int(mysql_status_new["Innodb_os_log_pending_fsyncs"])
        innodb_info.innodb_os_log_pending_writes = int(mysql_status_new["Innodb_os_log_pending_writes"])
        innodb_info.innodb_os_log_written = int(mysql_status_new["Innodb_os_log_written"]) - int(mysql_status_old["Innodb_os_log_written"])

        # buffer pool page
        innodb_info.page_data_count = int(mysql_status_new["Innodb_buffer_pool_pages_data"])
        innodb_info.page_dirty_count = int(mysql_status_new["Innodb_buffer_pool_pages_dirty"])
        innodb_info.page_free_count = int(mysql_status_new["Innodb_buffer_pool_pages_free"])
        innodb_info.page_total_count = int(mysql_status_new["Innodb_buffer_pool_pages_total"])
        innodb_info.page_dirty_pct = round(float(innodb_info.page_dirty_count) / float(innodb_info.page_total_count) * 100, 2)
        innodb_info.page_flush_persecond = int(mysql_status_new["Innodb_buffer_pool_pages_flushed"]) - int(mysql_status_old["Innodb_buffer_pool_pages_flushed"])
        innodb_info.page_usage = round((1 - float(innodb_info.page_free_count) / float(innodb_info.page_total_count)) * 100, 2)
        innodb_info.data_page_usage = round(float(innodb_info.page_data_count) / float(innodb_info.page_total_count) * 100, 2)
        innodb_info.dirty_page_usage = round(float(innodb_info.page_dirty_count) / float(innodb_info.page_total_count) * 100, 2)
        innodb_info.innodb_buffer_pool_wait_free = int(mysql_status_new["Innodb_buffer_pool_wait_free"])

        # buffer pool rows
        innodb_info.rows_read = int(mysql_status_new["Innodb_rows_read"]) - int(mysql_status_old["Innodb_rows_read"])
        innodb_info.rows_updated = int(mysql_status_new["Innodb_rows_updated"]) - int(mysql_status_old["Innodb_rows_updated"])
        innodb_info.rows_deleted = int(mysql_status_new["Innodb_rows_deleted"]) - int(mysql_status_old["Innodb_rows_deleted"])
        innodb_info.rows_inserted = int(mysql_status_new["Innodb_rows_inserted"]) - int(mysql_status_old["Innodb_rows_inserted"])

        # buffer pool
        innodb_info.buffer_pool_hit = (1 - int(mysql_status_new["Innodb_buffer_pool_reads"]) / (int(mysql_status_new["Innodb_buffer_pool_read_requests"]) + int(mysql_status_new["Innodb_buffer_pool_reads"]))) * 100
        innodb_info.buffer_pool_write_requests = int(mysql_status_new["Innodb_buffer_pool_write_requests"]) - int(mysql_status_old["Innodb_buffer_pool_write_requests"])
        innodb_info.buffer_pool_reads = int(mysql_status_new["Innodb_buffer_pool_reads"]) - int(mysql_status_old["Innodb_buffer_pool_reads"])
        innodb_info.buffer_pool_read_requests = int(mysql_status_new["Innodb_buffer_pool_read_requests"]) - int(mysql_status_old["Innodb_buffer_pool_read_requests"])

        # innodb data
        innodb_info.innodb_data_read = int(mysql_status_new["Innodb_data_read"]) - int(mysql_status_old["Innodb_data_read"])
        innodb_info.innodb_data_reads = int(mysql_status_new["Innodb_data_reads"]) - int(mysql_status_old["Innodb_data_reads"])
        innodb_info.innodb_data_writes = int(mysql_status_new["Innodb_data_writes"]) - int(mysql_status_old["Innodb_data_writes"])
        innodb_info.innodb_data_written = int(mysql_status_new["Innodb_data_written"]) - int(mysql_status_old["Innodb_data_written"])
        innodb_info.innodb_data_fsyncs = int(mysql_status_new["Innodb_data_fsyncs"]) - int(mysql_status_old["Innodb_data_fsyncs"])
        innodb_info.innodb_data_pending_fsyncs = int(mysql_status_new["Innodb_data_pending_fsyncs"])
        innodb_info.innodb_data_pending_reads = int(mysql_status_new["Innodb_data_pending_reads"])
        innodb_info.innodb_data_pending_writes = int(mysql_status_new["Innodb_data_pending_writes"])

        # innodb page
        innodb_info.innodb_page_size = int(mysql_status_new["Innodb_page_size"]) / 1024
        innodb_info.innodb_pages_read = int(mysql_status_new["Innodb_pages_read"]) - int(mysql_status_old["Innodb_pages_read"])
        innodb_info.innodb_pages_created = int(mysql_status_new["Innodb_pages_created"]) - int(mysql_status_old["Innodb_pages_created"])
        innodb_info.innodb_pages_written = int(mysql_status_new["Innodb_pages_written"]) - int(mysql_status_old["Innodb_pages_written"])

        # change(insert) buffer
        if (mysql_status_old.has_key("Innodb_ibuf_size")):
            innodb_info.innodb_ibuf_size = int(mysql_status_new["Innodb_ibuf_size"])
            innodb_info.innodb_ibuf_free_list = int(mysql_status_new["Innodb_ibuf_free_list"])
            innodb_info.innodb_ibuf_merges = int(mysql_status_new["Innodb_ibuf_merges"]) - int(mysql_status_old["Innodb_ibuf_merges"])
            innodb_info.innodb_ibuf_merged_inserts = int(mysql_status_new["Innodb_ibuf_merged_inserts"]) - int(mysql_status_old["Innodb_ibuf_merged_inserts"])
            innodb_info.innodb_ibuf_merged_deletes = int(mysql_status_new["Innodb_ibuf_merged_deletes"]) - int(mysql_status_old["Innodb_ibuf_merged_deletes"])
            innodb_info.innodb_ibuf_merged_delete_marks = int(mysql_status_new["Innodb_ibuf_merged_delete_marks"]) - int(mysql_status_old["Innodb_ibuf_merged_delete_marks"])

        # innodb mutex share excl lock
        innodb_info.innodb_spin_wait_delay = mysql_variables["innodb_spin_wait_delay"]
        innodb_info.innodb_sync_spin_loops = mysql_variables["innodb_sync_spin_loops"]
        if (mysql_status_old.has_key("Innodb_mutex_os_waits")):
            innodb_info.innodb_mutex_os_waits = int(mysql_status_new["Innodb_mutex_os_waits"]) - int(mysql_status_old["Innodb_mutex_os_waits"])
            innodb_info.innodb_mutex_spin_rounds = int(mysql_status_new["Innodb_mutex_spin_rounds"]) - int(mysql_status_old["Innodb_mutex_spin_rounds"])
            innodb_info.innodb_mutex_spin_waits = int(mysql_status_new["Innodb_mutex_spin_waits"]) - int(mysql_status_old["Innodb_mutex_spin_waits"])
            innodb_info.innodb_s_lock_os_waits = int(mysql_status_new["Innodb_s_lock_os_waits"]) - int(mysql_status_old["Innodb_s_lock_os_waits"])
            innodb_info.innodb_s_lock_spin_rounds = int(mysql_status_new["Innodb_s_lock_spin_rounds"]) - int(mysql_status_old["Innodb_s_lock_spin_rounds"])
            innodb_info.innodb_s_lock_spin_waits = int(mysql_status_new["Innodb_s_lock_spin_waits"]) - int(mysql_status_old["Innodb_s_lock_spin_waits"])
            innodb_info.innodb_x_lock_os_waits = int(mysql_status_new["Innodb_x_lock_os_waits"]) - int(mysql_status_old["Innodb_x_lock_os_waits"])
            innodb_info.innodb_x_lock_spin_rounds = int(mysql_status_new["Innodb_x_lock_spin_rounds"]) - int(mysql_status_old["Innodb_x_lock_spin_rounds"])
            innodb_info.innodb_x_lock_spin_waits = int(mysql_status_new["Innodb_x_lock_spin_waits"]) - int(mysql_status_old["Innodb_x_lock_spin_waits"])

        if (innodb_info.innodb_mutex_spin_rounds == 0):
            innodb_info.innodb_mutex_ratio = 0
        else:
            innodb_info.innodb_mutex_ratio = round(float(innodb_info.innodb_mutex_os_waits) / float(innodb_info.innodb_mutex_spin_rounds) * 100, 2)

        if (innodb_info.innodb_s_lock_spin_rounds == 0):
            innodb_info.innodb_s_ratio = 0
        else:
            innodb_info.innodb_s_ratio = round(float(innodb_info.innodb_s_lock_os_waits) / float(innodb_info.innodb_s_lock_spin_rounds) * 100, 2)

        if (innodb_info.innodb_x_lock_spin_rounds == 0):
            innodb_info.innodb_x_ratio = 0
        else:
            innodb_info.innodb_x_ratio = round(float(innodb_info.innodb_x_lock_os_waits) / float(innodb_info.innodb_x_lock_spin_rounds) * 100, 2)

        # 3.-----------------------------------------------------获取replcation status-------------------------------------------------------------------
        repl_info = self.__cache.get_repl_info(host_info.key)
        result = self.__db_util.fetchone_for_cursor("show slave status;", cursor=cursor)
        self.get_binlog_size_total(mysql_variables["log_bin"], status_info, cursor)
        if (host_info.is_slave):
            repl_info.read_only = mysql_variables["read_only"]
            repl_info.error_message = result["Last_Error"]
            repl_info.io_status = result["Slave_IO_Running"]
            repl_info.sql_status = result["Slave_SQL_Running"]
            repl_info.master_log_file = result["Master_Log_File"]
            repl_info.master_log_pos = int(result["Read_Master_Log_Pos"])
            repl_info.slave_log_file = result["Relay_Master_Log_File"]
            repl_info.slave_log_pos = int(result["Exec_Master_Log_Pos"])
            repl_info.slave_retrieved_gtid_set = result["Retrieved_Gtid_Set"].split(",")
            repl_info.slave_execute_gtid_set = result["Executed_Gtid_Set"].split(",")
            repl_info.seconds_behind_master = result["Seconds_Behind_Master"] if result["Seconds_Behind_Master"] else 0
            repl_info.delay_pos_count = repl_info.master_log_pos - repl_info.slave_log_pos
            host_info.io_status = repl_info.io_status
            host_info.sql_status = repl_info.sql_status
            # 获取对应主库的show master status信息
            if (hasattr(repl_info, "master_host_id")):
                master_status = self.__db_util.fetchone(self.__cache.get_host_info(repl_info.master_host_id), "show master status;")
                if (master_status != None):
                    repl_info.new_master_log_file = master_status["File"]
                    repl_info.new_master_log_pos = master_status["Position"]
            else:
                repl_info.new_master_log_pos = ""
                repl_info.new_master_log_file = ""

        # 4.-----------------------------------------------------获取replcation semi_sync-------------------------------------------------------------------
        if (mysql_status_new.has_key("Rpl_semi_sync_master_status")):
            repl_info.rpl_semi_sync = 1
            repl_info.rpl_semi_sync_slave_status = mysql_status_new["Rpl_semi_sync_slave_status"]
            repl_info.rpl_semi_sync_master_status = mysql_status_new["Rpl_semi_sync_master_status"]
            repl_info.rpl_semi_sync_master_clients = int(mysql_status_new["Rpl_semi_sync_master_clients"])

            repl_info.rpl_semi_sync_master_net_waits = int(mysql_status_new["Rpl_semi_sync_master_net_waits"])
            repl_info.rpl_semi_sync_master_net_wait_time = int(mysql_status_new["Rpl_semi_sync_master_net_wait_time"]) - int(mysql_status_old["Rpl_semi_sync_master_net_wait_time"])
            repl_info.rpl_semi_sync_master_net_avg_wait_time = int(mysql_status_new["Rpl_semi_sync_master_net_avg_wait_time"])

            repl_info.rpl_semi_sync_master_tx_waits = int(mysql_status_new["Rpl_semi_sync_master_tx_waits"])
            repl_info.rpl_semi_sync_master_tx_wait_time = int(mysql_status_new["Rpl_semi_sync_master_tx_wait_time"]) - int(mysql_status_old["Rpl_semi_sync_master_tx_wait_time"])
            repl_info.rpl_semi_sync_master_tx_avg_wait_time = int(mysql_status_new["Rpl_semi_sync_master_tx_avg_wait_time"])

            # 主库收到正常确认以及超时未成功确认的事务个数
            repl_info.rpl_semi_sync_master_no_tx = int(mysql_status_new["Rpl_semi_sync_master_no_tx"])
            repl_info.rpl_semi_sync_master_yes_tx = int(mysql_status_new["Rpl_semi_sync_master_yes_tx"])
            repl_info.rpl_semi_sync_master_no_times = int(mysql_status_new["Rpl_semi_sync_master_no_times"])

            repl_info.rpl_semi_sync_master_wait_sessions = int(mysql_status_new["Rpl_semi_sync_master_wait_sessions"])
        else:
            repl_info.rpl_semi_sync = 0

        self.__db_util.close(connection, cursor)
        self.read_innodb_status(host_info)
        # self.analyze_mysql_status(status_info)
        self.insert_status_log(status_info, innodb_info)

        host_info.tps = status_info.tps
        host_info.qps = status_info.qps
        host_info.trxs = innodb_info.trx_count
        host_info.threads = status_info.threads_count
        host_info.threads_running = status_info.threads_run_count
        host_info.send_bytes = status_info.send_bytes
        host_info.receive_bytes = status_info.receive_bytes

    def get_data_length(self, data_length):
        value = float(1024)
        if (data_length > value):
            result = round(data_length / value, 0)
            if (result > value):
                return str(int(round(result / value, 0))) + "M"
            else:
                return str(int(result)) + "K"
        else:
            return str(data_length) + "KB"

    def get_binlog_size_total(self, log_bin, status_info, cursor):
        if (log_bin == "ON"):
            total_size = 0
            for row in self.__db_util.fetchall_for_cursor("show master logs;", cursor=cursor):
                total_size += int(row["File_size"])
            status_info.binlog_size_total = tablespace.get_data_length(total_size)
        else:
            status_info.binlog_size_total = 0

    def get_dic_data(self, cursor, sql):
        data = {}
        for row in self.__db_util.fetchall_for_cursor(sql, cursor=cursor):
            data[row.get("Variable_name")] = row.get("Value")
        return data

    def get_cache_by_type(self, monitor_type):
        if (monitor_type == MonitorEnum.Host):
            return self.__cache.get_all_linux_infos()
        elif (monitor_type == MonitorEnum.Status):
            return self.__cache.get_all_status_infos()
        elif (monitor_type == MonitorEnum.Innodb):
            return self.__cache.get_all_innodb_infos()
        elif (monitor_type == MonitorEnum.Replication):
            return self.__cache.get_all_repl_infos()

    def insert_status_log(self, status_info, innodb_info):
        sql = "insert into mysql_web.mysql_status_log(host_id, qps, tps, commit, rollback, connections, " \
              "thread_count, thread_running_count, tmp_tables, tmp_disk_tables, send_bytes, receive_bytes, `trxs`) VALUES " \
              "({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, \'{10}\', \'{11}\', {12})" \
            .format(status_info.host_info.host_id, status_info.qps, status_info.tps, status_info.commit, status_info.rollback, status_info.connections_per,
                    status_info.threads_count, status_info.threads_run_count, status_info.create_tmp_table_count, status_info.create_tmp_disk_table_count,
                    status_info.send_bytes_bigint, status_info.receive_bytes_bigint, innodb_info.trx_count)
        self.__db_util.execute(settings.MySQL_Host, sql)

    def insert_os_monitor_log(self, linux_info):
        sql = """INSERT INTO `mysql_web`.`os_monitor_data`
                 (`host_id`,`cpu1`,`cpu5`,`cpu15`,`cpu_user`,`cpu_sys`,`cpu_iowait`,`mysql_cpu`,`mysql_memory`,`mysql_size`,`io_qps`,`io_tps`,`io_read`,`io_write`,`io_util`)
                 VALUES
                 ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14});""" \
            .format(linux_info.host_info.host_id, linux_info.cpu_1, linux_info.cpu_5, linux_info.cpu_15, linux_info.cpu_user, linux_info.cpu_system, linux_info.cpu_iowait,
                    linux_info.mysql_cpu, linux_info.mysql_memory, linux_info.mysql_data_size,
                    linux_info.io_qps, linux_info.io_tps, linux_info.io_read, linux_info.io_write, linux_info.util)
        self.__db_util.execute(settings.MySQL_Host, sql)

    def monitor_host_status(self, host_info):
        linux_info = self.__cache.get_linux_info(host_info.key)
        # 监测CPU负载
        self.monitor_host_for_cpu_load(linux_info)
        # 监测网卡流量
        self.monitor_host_for_net(linux_info)
        # 监测硬盘空间
        self.monitor_host_for_disk(linux_info)
        # 监测linux内存使用情况
        self.monitor_host_for_memory(linux_info)
        # 监控mysql的cpu和memory以及data大小
        self.monitor_host_for_mysql_cpu_and_memory(host_info, linux_info)

    def monitor_host_for_cpu_and_io(self, host_info):
        linux_info = self.__cache.get_linux_info(host_info.key)
        result_list = self.get_remote_command_result(host_info, "iostat -xk 1 2")

        io_flag = "Device"
        cpu_flag = "avg-cpu"
        number = 1
        io_flag_index = 0
        cpu_flag_index = 0
        for line in result_list:
            if (line.find(io_flag) >= 0):
                io_flag_index = number
            elif (line.find(cpu_flag) >= 0):
                cpu_flag_index = number
            number += 1

        io_list = result_list[io_flag_index:]
        cpu_list = result_list[cpu_flag_index:]
        io_column_names = self.remove_empty_string(result_list[io_flag_index - 1])

        # 解析io数据
        util = 0
        await = 0
        svctm = 0
        io_qps = 0
        io_tps = 0
        io_read = 0
        io_write = 0
        for str in io_list:
            number_tmp = 0
            io_tmp = self.remove_empty_string(str)

            if (len(io_tmp) <= 0):
                continue
            for column_name in io_column_names:
                if (column_name == "%util"):
                    util += float(io_tmp[number_tmp])
                if (column_name == "await"):
                    await += float(io_tmp[number_tmp])
                if (column_name == "svctm"):
                    svctm += float(io_tmp[number_tmp])
                if (column_name == "r/s"):
                    io_qps += float(io_tmp[number_tmp])
                if (column_name == "w/s"):
                    io_tps += float(io_tmp[number_tmp])
                if (column_name == "rkB/s"):
                    io_read += float(io_tmp[number_tmp])
                if (column_name == "wkB/s"):
                    io_write += float(io_tmp[number_tmp])
                number_tmp += 1
        linux_info.util = util
        linux_info.await = await
        linux_info.svctm = svctm
        linux_info.io_qps = int(io_qps)
        linux_info.io_tps = int(io_tps)
        linux_info.io_read = int(io_read)
        linux_info.io_write = int(io_write)

        # 解析cpu数据，因为cpu只有一行数据
        cpu_tmp = self.remove_empty_string(cpu_list[0])
        linux_info.cpu_user = float(cpu_tmp[0])
        linux_info.cpu_nice = float(cpu_tmp[1])
        linux_info.cpu_system = float(cpu_tmp[2])
        linux_info.cpu_iowait = float(cpu_tmp[3])
        linux_info.cpu_steal = float(cpu_tmp[4])
        linux_info.cpu_idle = float(cpu_tmp[5])

        # self.analyze_os_status(linux_info)
        # 插入os系统监控数据
        self.insert_os_monitor_log(linux_info)

    def remove_empty_string(self, str):
        result = []
        st_list = str.replace("\n", "").split(" ")
        for value in st_list:
            if (len(value) > 0):
                result.append(value)
        return result

    def monitor_host_for_cpu_load(self, linux_info):
        cpu_value = self.get_remote_command_result(linux_info.host_info, "cat /proc/loadavg")[0].split()
        linux_info.cpu_1 = cpu_value[0]
        linux_info.cpu_5 = cpu_value[1]
        linux_info.cpu_15 = cpu_value[2]

    def monitor_host_for_net(self, linux_info):
        net_send_byte, net_receive_byte, number = 0, 0, 0
        result = self.get_remote_command_result(linux_info.host_info, "cat /proc/net/dev")
        for line in result:
            number += 1
            if (number >= 3):
                new_list = [x for x in line.split(" ") if x != ""]
                net_send_byte += long(new_list[9])
                net_receive_byte += long(new_list[1])

        linux_info.net_send_old = linux_info.net_send_new
        linux_info.net_receive_old = linux_info.net_receive_new
        linux_info.net_send_new = net_send_byte
        linux_info.net_receive_new = net_receive_byte

        linux_info.net_send_byte = self.get_data_length(linux_info.net_send_new - linux_info.net_send_old)
        linux_info.net_receive_byte = self.get_data_length(linux_info.net_receive_new - linux_info.net_receive_old)

    def monitor_host_for_disk(self, linux_info):
        id_tmp = 0
        max_disk_value = 0
        total_disk_value = 0
        result = self.get_remote_command_result(linux_info.host_info, "df | grep -v 'tmpfs'")
        for line in result:
            id_tmp += 1
            if (id_tmp == 1):
                continue
            values = line.split()
            for value in values:
                if (value.find("%") >= 0):
                    disk_value_int = int(value.replace("%", ""))
                    if (max_disk_value == 0):
                        max_disk_value = disk_value_int
                    else:
                        if (disk_value_int > max_disk_value):
                            max_disk_value = disk_value_int

            list_len = len(values)
            if (list_len >= 3):
                if (list_len == 6):
                    total_disk_value += int(values[1])
                elif (list_len == 5):
                    total_disk_value += int(values[0])
        linux_info.disk_value = int(max_disk_value)
        linux_info.total_disk_value = int(total_disk_value / 1024 / 1024)

    def monitor_host_for_memory(self, linux_info):
        memory_free_total = 0
        result = self.get_remote_command_result(linux_info.host_info, "cat /proc/meminfo")
        for line in result:
            values = line.split(":")
            if (len(values) >= 2):
                value_tmp = int(values[1].replace("kB", "")) * 1024
                if (values[0].find("MemTotal") >= 0):
                    linux_info.memory_total = tablespace.get_data_length(value_tmp)
                elif (values[0].find("MemFree") >= 0):
                    memory_free_total += value_tmp
                    linux_info.memory_free = tablespace.get_data_length(value_tmp)
                elif (values[0].strip().lstrip() == "Buffers"):
                    memory_free_total += value_tmp
                    linux_info.memory_buffers = tablespace.get_data_length(value_tmp)
                elif (values[0].strip().lstrip() == "Cached"):
                    memory_free_total += value_tmp
                    linux_info.memory_cache = tablespace.get_data_length(value_tmp)
                elif (values[0].find("SwapTotal") >= 0):
                    linux_info.swap_total = tablespace.get_data_length(value_tmp)
                elif (values[0].find("SwapFree") >= 0):
                    linux_info.swap_free = tablespace.get_data_length(value_tmp)
        linux_info.memory_free_total = tablespace.get_data_length(memory_free_total)

    def monitor_host_for_mysql_cpu_and_memory(self, host_info, linux_info):
        result = self.get_remote_command_result(host_info, "cat %s" % host_info.mysql_pid_file)
        linux_info.mysql_pid = int(result[0])

        result = self.get_remote_command_result(host_info, "top -b -n1 | grep mysql")
        for line in result:
            values = line.split()
            if (int(values[0]) == linux_info.mysql_pid):
                linux_info.mysql_cpu = float(values[8])
                linux_info.mysql_memory = float(values[9])
                break

        # 监测MySQL数据目录大小
        result = self.get_remote_command_result(host_info, "du -h %s | tail -n1 | awk '{print $1'}" % host_info.mysql_data_dir)
        linux_info.mysql_data_size = result[0].replace("\n", "").replace("G", "")

    def get_remote_command_result(self, host_info, command):
        key = host_info.host + str(host_info.port)
        if (key in self.__ssh_client_dict.keys()):
            host_client = self.__ssh_client_dict[key]
        else:
            host_client = paramiko.SSHClient()
            host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            host_client.connect(host_info.host, port=host_info.ssh_port, username="root")
            host_client.get_transport().set_keepalive(1)
            self.__ssh_client_dict[key] = host_client
        stdin, stdout, stderr = host_client.exec_command(command)
        return stdout.readlines()

    def read_innodb_status(self, host_info):
        innodb_status = self.get_innodb_status_infos(host_info)
        if (innodb_status.has_key("LOG") == True):
            self.get_lsn_info(host_info, innodb_status["LOG"])
        if (innodb_status.has_key("INDIVIDUAL BUFFER POOL INFO") == True):
            self.get_buffer_pool_infos(host_info, innodb_status["INDIVIDUAL BUFFER POOL INFO"])
        if (innodb_status.has_key("LATEST DETECTED DEADLOCK") == True):
            self.get_latest_deadlock(host_info, innodb_status["LATEST DETECTED DEADLOCK"])
        if (innodb_status.has_key("TRANSACTIONS") == True):
            self.get_transactions_info(host_info, innodb_status["TRANSACTIONS"])
        if (innodb_status.has_key("INSERT BUFFER AND ADAPTIVE HASH INDEX")):
            self.get_change_buffer_infos(host_info, innodb_status["INSERT BUFFER AND ADAPTIVE HASH INDEX"])
        if (innodb_status.has_key("SEMAPHORES")):
            self.get_innodb_lock_infos(host_info, innodb_status["SEMAPHORES"])

    def get_lsn_info(self, host_info, values):
        info_tmp = self.__cache.get_engine_innodb_status_infos(host_info.key)
        num = 0
        for line in values:
            line_split = line.split(" ")
            split_value = line_split[len(line_split) - 1]
            if (num == 1):
                info_tmp.log_lsn = split_value
            elif (num == 2):
                info_tmp.log_flush_lsn = split_value
            elif (num == 3):
                info_tmp.page_flush_lsn = split_value
            elif (num == 4):
                info_tmp.checkpoint_lsn = split_value
            num = num + 1
        info_tmp.log_flush_diff = int(info_tmp.log_lsn) - int(info_tmp.log_flush_lsn)
        info_tmp.page_flush_diff = int(info_tmp.log_lsn) - int(info_tmp.page_flush_lsn)
        info_tmp.checkpoint_diff = int(info_tmp.log_lsn) - int(info_tmp.checkpoint_lsn)

    def get_buffer_pool_infos(self, host_info, values):
        buffer_pool_key = ""
        buffer_pool_infos = collections.OrderedDict()

        for line in values:
            str_value = line.replace("\n", "")
            if (len(str_value) > 0):
                if (str_value.find("---BUFFER POOL") >= 0):
                    buffer_pool_key = str_value
                    buffer_pool_infos[buffer_pool_key] = []
                else:
                    if (len(buffer_pool_key) > 0):
                        buffer_pool_infos[buffer_pool_key].append(str_value)

        for key, value_list in buffer_pool_infos.items():
            num = 0
            info_tmp = base_class.BaseClass(None)
            buffer_pool_name = key.replace("-", "")
            info_tmp.name = buffer_pool_name
            for line in value_list:
                line_split = line.split(" ")
                split_value = line_split[len(line_split) - 1].replace(",", "")
                if (line.find("unzip_LRU") >= 0):
                    info_tmp.unzip_lur = split_value
                elif (line.find("Free buffers") >= 0):
                    info_tmp.free_pages = split_value
                elif (line.find("Buffer pool size ") >= 0):
                    info_tmp.total_pages = split_value
                elif (line.find("Database pages") >= 0):
                    info_tmp.lru_pages = split_value
                elif (line.find("Old database pages") >= 0):
                    info_tmp.old_pages = split_value
                elif (line.find("Modified db pages") >= 0):
                    info_tmp.dirty_pages = split_value
                elif (line.find("Buffer pool hit rate") >= 0):
                    info_tmp.buffer_pool_hit = int(line_split[4].replace(",", "")) / int(line_split[6].replace(",", "")) * 100
                elif (line.find("reads") >= 0 and line.find("creates") >= 0 and line.find("writes") >= 0):
                    info_tmp.reads_per = line_split[0]
                    info_tmp.creates_per = line_split[2]
                    info_tmp.writes_per = line_split[4]
                elif (line.find("Pending reads") >= 0):
                    info_tmp.pending_reads = split_value
                num += 1
                cache.Cache().get_engine_innodb_status_infos(host_info.key).buffer_pool_infos[buffer_pool_name] = info_tmp

    def get_latest_deadlock(self, host_info, values):
        info_tmp = self.__cache.get_engine_innodb_status_infos(host_info.key)
        if (len(values) > 5):
            # 因为返回的数组有个[----]的表示，所以永远都是大于0的，所以要判断下
            info_tmp.latest_deadlock = values
        else:
            info_tmp.latest_deadlock = None

    def get_transactions_info(self, host_info, values):
        status_info = self.__cache.get_status_info(host_info.key)
        innodb_info = self.__cache.get_innodb_info(host_info.key)
        info_tmp = self.__cache.get_engine_innodb_status_infos(host_info.key)
        for line in values:
            line_split = line.split(" ")
            split_value = line_split[len(line_split) - 1].replace(",", "")
            if (line.find("History list length") >= 0):
                # 官方status也没有undo list值
                if (host_info.branch == mysql_branch.MySQLBranch.MySQL):
                    info_tmp.undo_history_list_len = int(split_value)
                    innodb_info.history_list_length = int(split_value)
                else:
                    info_tmp.undo_history_list_len = innodb_info.history_list_length
            elif (line.find("Trx id counter") >= 0):
                # 因为官方mysql版本没有Innodb_max_trx_id状态值
                # 需要去show engine innodb status去进行计算
                if (host_info.branch == mysql_branch.MySQLBranch.MySQL):
                    status_info.old_trx_count = status_info.new_trx_count
                    status_info.new_trx_count = int(split_value)
                    status_info.trx_count = (status_info.new_trx_count - status_info.old_trx_count) / settings.UPDATE_INTERVAL
                    innodb_info.trx_count = status_info.trx_count
                    info_tmp.trx_count = status_info.trx_count

    def get_innodb_status_infos(self, host_info):
        flag_list = []
        flag_list.append("BACKGROUND THREAD")
        flag_list.append("SEMAPHORES")
        flag_list.append("LATEST DETECTED DEADLOCK")
        flag_list.append("TRANSACTIONS")
        flag_list.append("FILE I/O")
        flag_list.append("INSERT BUFFER AND ADAPTIVE HASH INDEX")
        flag_list.append("LOG")
        flag_list.append("BUFFER POOL AND MEMORY")
        flag_list.append("INDIVIDUAL BUFFER POOL INFO")
        flag_list.append("ROW OPERATIONS")
        flag_list.append("LATEST DETECTED DEADLOCK")
        flag_list.append("TRANSACTIONS")
        flag_list.append("END OF INNODB MONITOR OUTPUT")
        innodb_status_infos = collections.OrderedDict()

        innodb_status = self.__db_util.fetchone(host_info, "show engine innodb status;")
        key_name = ""
        for line in innodb_status["Status"].split("\n"):
            str_value = line.replace("\n", "")
            if (len(str_value) > 0):
                if (str_value in flag_list):
                    key_name = str_value
                    innodb_status_infos[key_name] = []
                else:
                    if (len(key_name) > 0):
                        innodb_status_infos[key_name].append(str_value)
        return innodb_status_infos

    def get_change_buffer_infos(self, host_info, values):
        # 为数组的倒数第二行
        # 373422000.00 hash searches/s, 43560000.00 non-hash searches/s
        line_value = values[-2]
        lst = line_value.split(",")
        innodb_info = self.__cache.get_innodb_info(host_info.key)
        innodb_info.hash_searches = float(lst[0].split(" ")[0])
        innodb_info.non_hash_searches = float(lst[1].split(" ")[1])
        if (innodb_info.hash_searches <= 0 and innodb_info.non_hash_searches <= 0):
            innodb_info.hash_search_ratio = 0
        else:
            innodb_info.hash_search_ratio = round(innodb_info.hash_searches / (innodb_info.non_hash_searches + innodb_info.hash_searches) * 100, 2)

        if (host_info.branch == mysql_branch.MySQLBranch.MySQL):
            row_number = 1
            innodb_info = self.__cache.get_innodb_info(host_info.key)
            for line in values:
                if ("Ibuf" in line):
                    # 第一行格式
                    # Ibuf: size 1, free list len 461392, seg size 461394, 8352044 merges
                    lst = line.split(",")
                    for value in lst:
                        lst_tmp = value.split(" ")
                        if ("Ibuf" in value):
                            innodb_info.innodb_ibuf_size = int(lst_tmp[-1])
                        elif ("free" in value):
                            innodb_info.innodb_ibuf_free_list = int(lst_tmp[-1])
                        elif ("merges" in value):
                            innodb_info.innodb_ibuf_merges_old = innodb_info.innodb_ibuf_merges_new
                            innodb_info.innodb_ibuf_merges_new = int(lst_tmp[1])
                            innodb_info.innodb_ibuf_merges = innodb_info.innodb_ibuf_merges_new - innodb_info.innodb_ibuf_merges_old

                if (row_number == 4):
                    # 第四行格式
                    # insert 35002969, delete mark 12861407, delete 1301010
                    lst = line.split(",")

                    # insert
                    lst_tmp = lst[0].split(" ")
                    innodb_info.innodb_ibuf_merged_inserts_old = innodb_info.innodb_ibuf_merged_inserts_new
                    innodb_info.innodb_ibuf_merged_inserts_new = int(lst_tmp[-1])
                    innodb_info.innodb_ibuf_merged_inserts = innodb_info.innodb_ibuf_merged_inserts_new - innodb_info.innodb_ibuf_merged_inserts_old

                    # delete
                    lst_tmp = lst[2].split(" ")
                    innodb_info.innodb_ibuf_merged_deletes_old = innodb_info.innodb_ibuf_merged_deletes_new
                    innodb_info.innodb_ibuf_merged_deletes_new = int(lst_tmp[-1])
                    innodb_info.innodb_ibuf_merged_deletes = innodb_info.innodb_ibuf_merged_deletes_new - innodb_info.innodb_ibuf_merged_deletes_old

                    # delete mark
                    lst_tmp = lst[1].split(" ")
                    innodb_info.innodb_ibuf_merged_delete_marks_old = innodb_info.innodb_ibuf_merged_delete_marks_new
                    innodb_info.innodb_ibuf_merged_delete_marks_new = int(lst_tmp[-1])
                    innodb_info.innodb_ibuf_merged_delete_marks = innodb_info.innodb_ibuf_merged_delete_marks_new - innodb_info.innodb_ibuf_merged_delete_marks_old

                row_number += 1

    def get_innodb_lock_infos(self, host_info, values):
        if (host_info.branch == mysql_branch.MySQLBranch.MySQL):
            row_number = 1
            innodb_info = self.__cache.get_innodb_info(host_info.key)
            for line in values:
                lst = line.split(",")
                if (row_number == 4):
                    # Mutex spin waits 4028500577, rounds 3985916509, OS waits 52752390
                    innodb_info.innodb_mutex_spin_waits_old = innodb_info.innodb_mutex_spin_waits_new
                    innodb_info.innodb_mutex_spin_waits_new = self.get_last_value_for_array(lst, 0)
                    innodb_info.innodb_mutex_spin_waits = innodb_info.innodb_mutex_spin_waits_new - innodb_info.innodb_mutex_spin_waits_old

                    innodb_info.innodb_mutex_spin_rounds_old = innodb_info.innodb_mutex_spin_rounds_new
                    innodb_info.innodb_mutex_spin_rounds_new = self.get_last_value_for_array(lst, 1)
                    innodb_info.innodb_mutex_spin_rounds = innodb_info.innodb_mutex_spin_rounds_new - innodb_info.innodb_mutex_spin_rounds_old

                    innodb_info.innodb_mutex_os_waits_old = innodb_info.innodb_mutex_os_waits_new
                    innodb_info.innodb_mutex_os_waits_new = self.get_last_value_for_array(lst, 2)
                    innodb_info.innodb_mutex_os_waits = innodb_info.innodb_mutex_os_waits_new - innodb_info.innodb_mutex_os_waits_old
                if (row_number == 5):
                    # RW-shared spins 6397297650, rounds 57823195252, OS waits 1223146785
                    innodb_info.innodb_s_lock_spin_waits_old = innodb_info.innodb_s_lock_spin_waits_new
                    innodb_info.innodb_s_lock_spin_waits_new = self.get_last_value_for_array(lst, 0)
                    innodb_info.innodb_s_lock_spin_waits = innodb_info.innodb_s_lock_spin_waits_new - innodb_info.innodb_s_lock_spin_waits_old

                    innodb_info.innodb_s_lock_spin_rounds_old = innodb_info.innodb_s_lock_spin_rounds_new
                    innodb_info.innodb_s_lock_spin_rounds_new = self.get_last_value_for_array(lst, 1)
                    innodb_info.innodb_s_lock_spin_rounds = innodb_info.innodb_s_lock_spin_rounds_new - innodb_info.innodb_s_lock_spin_rounds_old

                    innodb_info.innodb_s_lock_os_waits_old = innodb_info.innodb_s_lock_os_waits_new
                    innodb_info.innodb_s_lock_os_waits_new = self.get_last_value_for_array(lst, 2)
                    innodb_info.innodb_s_lock_os_waits = innodb_info.innodb_s_lock_os_waits_new - innodb_info.innodb_s_lock_os_waits_old
                if (row_number == 6):
                    # RW-excl spins 912418176, rounds 42146038659, OS waits 552132933
                    innodb_info.innodb_x_lock_spin_waits_old = innodb_info.innodb_x_lock_spin_waits_new
                    innodb_info.innodb_x_lock_spin_waits_new = self.get_last_value_for_array(lst, 0)
                    innodb_info.innodb_x_lock_spin_waits = innodb_info.innodb_x_lock_spin_waits_new - innodb_info.innodb_x_lock_spin_waits_old

                    innodb_info.innodb_x_lock_spin_rounds_old = innodb_info.innodb_x_lock_spin_rounds_new
                    innodb_info.innodb_x_lock_spin_rounds_new = self.get_last_value_for_array(lst, 1)
                    innodb_info.innodb_x_lock_spin_rounds = innodb_info.innodb_x_lock_spin_rounds_new - innodb_info.innodb_x_lock_spin_rounds_old

                    innodb_info.innodb_x_lock_os_waits_old = innodb_info.innodb_x_lock_os_waits_new
                    innodb_info.innodb_x_lock_os_waits_new = self.get_last_value_for_array(lst, 2)
                    innodb_info.innodb_x_lock_os_waits = innodb_info.innodb_x_lock_os_waits_new - innodb_info.innodb_x_lock_os_waits_old

                row_number += 1

    def get_last_value_for_array(self, array, index):
        return int(array[index].split(" ")[-1])

    def analyze_os_status(self, os_info):
        self.analyze_data(os_info, cache.Analyze_OS_Key)

    def analyze_mysql_status(self, status_info):
        self.analyze_data(status_info, cache.Analyze_MySQL_Key)

    def analyze_data(self, obj, analyze_key):
        analyze_info = self.__cache.get_analyze_info(obj.host_info.host_id)
        for key in analyze_key:
            value = getattr(obj, key)
            value_min = getattr(analyze_info, key + cache.Value_Min)
            value_max = getattr(analyze_info, key + cache.Value_Max)
            value_sum = getattr(analyze_info, key + cache.Value_Sum)
            value_count = getattr(analyze_info, key + cache.Value_Count)

            if (value < value_min or value_min == 0):
                value_min = value
            if (value > value_max or value_max == 0):
                value_max = value

            value_count += 1
            value_sum = value_sum + value
            value_avg = round(float(value_sum) / float(value_count) * 100, 2)

            setattr(analyze_info, key + cache.Value_Min, value_min)
            setattr(analyze_info, key + cache.Value_Max, value_max)
            setattr(analyze_info, key + cache.Value_Avg, value_avg)
            setattr(analyze_info, key + cache.Value_Sum, value_sum)
            setattr(analyze_info, key + cache.Value_Count, value_count)


# region show global status sql

show_global_status_sql = """
show global status where variable_name in
(
'Uptime',
'Open_files',
'Opened_files',
'Bytes_sent',
'Bytes_received',
'Questions',
'Com_select',
'Com_insert',
'Com_update',
'Com_delete',
'Com_commit',
'Com_rollback',
'Innodb_max_trx_id',
'Connections',
'Threads_created',
'Threads_connected',
'Threads_running',
'Aborted_clients',
'Aborted_connects',
'Binlog_cache_use',
'Binlog_cache_disk_use',
'Handler_commit',
'Handler_rollback',
'Handler_read_first',
'Handler_read_key',
'Handler_read_next',
'Handler_read_last',
'Handler_read_rnd',
'Handler_read_rnd_next',
'Handler_update',
'Handler_write',
'Handler_delete',
'table_open_cache',
'table_open_cache_instances',
'Open_tables',
'Opened_tables',
'Table_open_cache_hits',
'Table_open_cache_misses',
'Table_open_cache_overflows',
'Open_files',
'Opened_files',
'Created_tmp_files',
'Created_tmp_tables',
'Created_tmp_disk_tables',
'Table_locks_immediate',
'Table_locks_waited',
'Select_full_join',
'Select_scan',
'Select_full_range_join',
'Select_range_check',
'Select_range',
'Sort_merge_passes',
'Sort_range',
'Sort_scan',
'Innodb_deadlocks',
'Innodb_history_list_length',
'Innodb_current_row_locks',
'Innodb_row_lock_current_waits',
'Innodb_log_writes',
'Innodb_log_write_requests',
'Innodb_os_log_pending_fsyncs',
'Innodb_os_log_pending_writes',
'Innodb_os_log_written',
'Innodb_log_waits',
'Innodb_buffer_pool_wait_free',
'Innodb_row_lock_waits',
'Innodb_row_lock_time',
'Innodb_row_lock_time_avg',
'Innodb_row_lock_time_max',
'Innodb_buffer_pool_pages_data',
'Innodb_buffer_pool_pages_dirty',
'Innodb_buffer_pool_pages_free',
'Innodb_buffer_pool_pages_total',
'Innodb_buffer_pool_pages_flushed',
'Innodb_rows_read',
'Innodb_rows_updated',
'Innodb_rows_deleted',
'Innodb_rows_inserted',
'Innodb_buffer_pool_reads',
'Innodb_buffer_pool_write_requests',
'Innodb_buffer_pool_reads',
'Innodb_buffer_pool_read_requests',
'Innodb_data_read',
'Innodb_data_reads',
'Innodb_data_writes',
'Innodb_data_written',
'Innodb_data_fsyncs',
'Innodb_data_pending_fsyncs',
'Innodb_data_pending_reads',
'Innodb_data_pending_writes',
'Innodb_page_size',
'Innodb_pages_read',
'Innodb_pages_created',
'Innodb_pages_written',
'Innodb_ibuf_free_list',
'Innodb_ibuf_size',
'Innodb_ibuf_free_list',
'Innodb_ibuf_merges',
'Innodb_ibuf_merged_inserts',
'Innodb_ibuf_merged_deletes',
'Innodb_ibuf_merged_delete_marks',
'Rpl_semi_sync_master_status',
'Rpl_semi_sync_slave_status',
'Rpl_semi_sync_master_status',
'Rpl_semi_sync_master_clients',
'Rpl_semi_sync_master_net_waits',
'Rpl_semi_sync_master_net_wait_time',
'Rpl_semi_sync_master_net_avg_wait_time',
'Rpl_semi_sync_master_tx_waits',
'Rpl_semi_sync_master_tx_wait_time',
'Rpl_semi_sync_master_tx_avg_wait_time',
'Rpl_semi_sync_master_no_tx',
'Rpl_semi_sync_master_yes_tx',
'Rpl_semi_sync_master_no_times',
'Rpl_semi_sync_master_wait_sessions',
'Innodb_mutex_os_waits',
'Innodb_mutex_spin_rounds',
'Innodb_mutex_spin_waits',
'Innodb_s_lock_os_waits',
'Innodb_s_lock_spin_rounds',
'Innodb_s_lock_spin_waits',
'Innodb_x_lock_os_waits',
'Innodb_x_lock_spin_rounds',
'Innodb_x_lock_spin_waits',
'Slow_queries'
);
"""
# endregion

# region show global variables sql

show_global_variables_sql = """
show global variables where variable_name in
(
'',
'',
'',
'',
'',
'',
'',
'',
'',
'',
'',
'',
'',
'',
'',
''
);
"""
# endregion
