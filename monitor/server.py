# -*- coding: utf-8 -*-

import time, threadpool, cache, threading, db_util, enum, settings, paramiko, collections, base_class

class MonitorEnum(enum.Enum):
    Host = 3
    Status = 0
    Innodb = 1
    Replication = 2

class MonitorServer(threading.Thread):
    __times = 1
    __cache = None
    __db_util = None
    __instance = None
    __thread_pool = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if(cls.__instance is None):
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
            if(self.__times % settings.UPDATE_INTERVAL == 0):
                self.join_thread_pool(self.get_mysql_status)
            if(self.__times % settings.LINUX_UPDATE_INTERVAL == 0):
                pass
                #self.join_thread_pool(self.monitor_host_status)
            if(self.__times % settings.TABLE_CHECK_INTERVAL == 0):
                pass
            if(self.__times % settings.INNODB_UPDATE_INTERVAL == 0):
                self.join_thread_pool(self.read_innodb_status)
            time.sleep(1)
            self.__times = self.__times + 1

    def join_thread_pool(self, method_name):
        requests = threadpool.makeRequests(method_name, list(self.__cache.get_all_host_infos()), None)
        for request in requests:
            self.__thread_pool.putRequest(request)
        self.__thread_pool.poll()

    def get_mysql_status(self, host_info):
        aa = time.time()
        mysql_status_old = self.get_dic_data(host_info, "show global status;")
        time.sleep(1)
        mysql_status_new = self.get_dic_data(host_info, "show global status;")
        #mysql_variables = self.get_dic_data(host_info, "show global variables;")
        mysql_variables = self.get_dic_data(host_info, "show global variables where variable_name in ('datadir', 'pid_file', 'log_bin', 'log_bin_basename', "
                                                       "'max_connections', 'table_open_cache', 'table_open_cache_instances');")
        host_info.mysql_data_dir = mysql_variables["datadir"]
        host_info.mysql_pid_file = mysql_variables["pid_file"]

        #1.---------------------------------------------------------获取mysql global status--------------------------------------------------------
        status_info = self.__cache.get_status_infos(host_info.key)
        status_info.open_files = int(mysql_status_new["Open_files"])
        status_info.opened_files = int(mysql_status_new["Opened_files"])
        status_info.send_bytes = self.get_data_length(int(mysql_status_new["Bytes_sent"]) - int(mysql_status_old["Bytes_sent"]))
        status_info.receive_bytes = self.get_data_length(int(mysql_status_new["Bytes_received"])  - int(mysql_status_old["Bytes_received"]))

        #tps and qps
        status_info.qps = int(mysql_status_new["Questions"]) - int(mysql_status_old["Questions"])
        status_info.select_count = int(mysql_status_new["Com_select"]) - int(mysql_status_old["Com_select"])
        status_info.insert_count = int(mysql_status_new["Com_insert"]) - int(mysql_status_old["Com_insert"])
        status_info.update_count = int(mysql_status_new["Com_update"]) - int(mysql_status_old["Com_update"])
        status_info.delete_count = int(mysql_status_new["Com_delete"]) - int(mysql_status_old["Com_delete"])
        status_info.commit = int(mysql_status_new["Com_commit"]) - int(mysql_status_old["Com_commit"])
        status_info.rollback = int(mysql_status_new["Com_rollback"]) - int(mysql_status_old["Com_rollback"])
        status_info.tps = status_info.insert_count + status_info.update_count + status_info.delete_count
        if(mysql_status_new.get("Innodb_max_trx_id") != None):
            #percona
            status_info.trx_count = int(mysql_status_new["Innodb_max_trx_id"]) - int(mysql_status_old["Innodb_max_trx_id"])
        else:
            #mysql show engine innodb status
            if(getattr(status_info, "trx_count") == None):
                status_info.trx_count = 0

        #thread and connection
        status_info.connections = int(mysql_status_new["Connections"])
        status_info.thread_created = int(mysql_status_new["Threads_created"])
        status_info.threads_count = int(mysql_status_new["Threads_connected"])
        status_info.threads_run_count = int(mysql_status_new["Threads_running"])
        status_info.thread_cache_hit = (1 - status_info.thread_created / status_info.connections) * 100
        status_info.connections_per = int(mysql_status_new["Connections"]) - int(mysql_status_old["Connections"])
        status_info.connections_usage_rate = status_info.threads_count * 100 / int(mysql_variables["max_connections"])

        #binlog cache
        status_info.binlog_cache_use = int(mysql_status_new["Binlog_cache_use"])
        status_info.binlog_cache_disk_use = int(mysql_status_new["Binlog_cache_disk_use"])
        if(status_info.binlog_cache_use > 0):
            #从库没有写binlog，所以这边要判断下
            status_info.binlog_cache_hit = (1 - status_info.binlog_cache_disk_use / status_info.binlog_cache_use) * 100
        else:
            status_info.binlog_cache_hit = 0

        #Handler_read
        status_info.handler_read_first = int(mysql_status_new["Handler_read_first"]) - int(mysql_status_old["Handler_read_first"])
        status_info.handler_read_key = int(mysql_status_new["Handler_read_key"]) - int(mysql_status_old["Handler_read_key"])
        status_info.handler_read_next = int(mysql_status_new["Handler_read_next"]) - int(mysql_status_old["Handler_read_next"])
        status_info.handler_read_last = int(mysql_status_new["Handler_read_last"]) - int(mysql_status_old["Handler_read_last"])
        status_info.handler_read_rnd = int(mysql_status_new["Handler_read_rnd"]) - int(mysql_status_old["Handler_read_rnd"])
        status_info.handler_read_rnd_next = int(mysql_status_new["Handler_read_rnd_next"]) - int(mysql_status_old["Handler_read_rnd_next"])

        #open table cache
        status_info.table_open_cache = int(mysql_variables["table_open_cache"])
        status_info.table_open_cache_instances = int(mysql_variables["table_open_cache_instances"])
        status_info.open_tables = int(mysql_status_new["Open_tables"])
        status_info.openend_tables = int(mysql_status_new["Opened_tables"]) - int(mysql_status_old["Opened_tables"])
        status_info.table_open_cache_hits = int(mysql_status_new["Table_open_cache_hits"]) - int(mysql_status_old["Table_open_cache_hits"])
        status_info.table_open_cache_misses = int(mysql_status_new["Table_open_cache_misses"]) - int(mysql_status_old["Table_open_cache_misses"])
        status_info.table_open_cache_overflows = int(mysql_status_new["Table_open_cache_overflows"]) - int(mysql_status_old["Table_open_cache_overflows"])

        #tmp table create
        status_info.create_tmp_files = int(mysql_status_new["Created_tmp_files"]) - int(mysql_status_old["Created_tmp_files"])
        status_info.create_tmp_table_count = int(mysql_status_new["Created_tmp_tables"]) - int(mysql_status_old["Created_tmp_tables"])
        status_info.create_tmp_disk_table_count = int(mysql_status_new["Created_tmp_disk_tables"]) - int(mysql_status_old["Created_tmp_disk_tables"])

        #table lock
        status_info.table_locks_immediate = int(mysql_status_new["Table_locks_immediate"]) - int(mysql_status_old["Table_locks_immediate"])
        status_info.table_locks_waited = int(mysql_status_new["Table_locks_waited"]) - int(mysql_status_old["Table_locks_waited"])

        #2.---------------------------------------------------------获取innodb的相关数据-------------------------------------------------------------------
        innodb_info = self.__cache.get_innodb_infos(host_info.key)
        innodb_info.trxs = 0
        innodb_info.current_row_locks = 0
        innodb_info.history_list_length = 0
        innodb_info.commit = status_info.commit
        innodb_info.rollback = status_info.rollback
        innodb_info.trx_count = status_info.trx_count

        '''
        if(mysql_status_new.get("Innodb_history_list_length") != None):
            #percona
            innodb_info.history_list_length = int(mysql_status_new["Innodb_history_list_length"])
        if(mysql_status_new.get("Innodb_current_row_locks") != None):
            #percona
            innodb_info.current_row_locks = mysql_status_new["Innodb_current_row_locks"]
        elif(mysql_status_new.get("Innodb_row_lock_current_waits") != None):
            #mysql
            innodb_info.current_row_locks = mysql_status_new["Innodb_row_lock_current_waits"]'''

        #innodb redo log info
        innodb_info.innodb_log_writes = int(mysql_status_new["Innodb_log_writes"]) - int(mysql_status_old["Innodb_log_writes"])
        innodb_info.innodb_os_log_pending_fsyncs = int(mysql_status_new["Innodb_os_log_pending_fsyncs"])
        innodb_info.innodb_os_log_pending_writes = int(mysql_status_new["Innodb_os_log_pending_writes"])
        innodb_info.innodb_os_log_written = int(mysql_status_new["Innodb_os_log_written"]) - int(mysql_status_old["Innodb_os_log_written"])

        #innodb log row page waits
        innodb_info.innodb_log_waits = int(mysql_status_new["Innodb_log_waits"])
        innodb_info.pool_wait_free = int(mysql_status_new["Innodb_buffer_pool_wait_free"])
        innodb_info.innodb_row_lock_waits = int(mysql_status_new["Innodb_row_lock_waits"]) - int(mysql_status_old["Innodb_row_lock_waits"])

        #buffer pool page
        innodb_info.page_dirty_count = int(mysql_status_new["Innodb_buffer_pool_pages_dirty"])
        innodb_info.page_free_count = int(mysql_status_new["Innodb_buffer_pool_pages_free"])
        innodb_info.page_total_count = int(mysql_status_new["Innodb_buffer_pool_pages_total"])
        innodb_info.page_dirty_pct = round(float(innodb_info.page_dirty_count) / float(innodb_info.page_total_count) * 100, 2)
        innodb_info.page_flush_persecond = int(mysql_status_new["Innodb_buffer_pool_pages_flushed"]) - int(mysql_status_old["Innodb_buffer_pool_pages_flushed"])

        #buffer pool update read insert delete
        innodb_info.buffer_pool_reads = int(mysql_status_new["Innodb_buffer_pool_reads"])
        innodb_info.buffer_pool_read_requests = int(mysql_status_new["Innodb_buffer_pool_read_requests"])
        innodb_info.buffer_pool_hit = (1 - innodb_info.buffer_pool_reads / innodb_info.buffer_pool_read_requests) * 100
        innodb_info.rows_read = int(mysql_status_new["Innodb_rows_read"]) - int(mysql_status_old["Innodb_rows_read"])
        innodb_info.rows_updated = int(mysql_status_new["Innodb_rows_updated"]) - int(mysql_status_old["Innodb_rows_updated"])
        innodb_info.rows_deleted = int(mysql_status_new["Innodb_rows_deleted"]) - int(mysql_status_old["Innodb_rows_deleted"])
        innodb_info.rows_inserted = int(mysql_status_new["Innodb_rows_inserted"]) - int(mysql_status_old["Innodb_rows_inserted"])

        #3.-----------------------------------------------------获取replcation status-------------------------------------------------------------------
        result = self.__db_util.fetchone(host_info, "show slave status;")
        if(result != None):
            repl_info = self.__cache.get_repl_info(host_info.key)
            repl_info.is_slave = 1
            repl_info.error_message = result["Last_Error"]
            repl_info.io_status = result["Slave_IO_Running"]
            repl_info.sql_status = result["Slave_SQL_Running"]
            repl_info.master_log_file = result["Master_Log_File"]
            repl_info.master_log_pos = int(result["Read_Master_Log_Pos"])
            repl_info.slave_log_file = result["Relay_Master_Log_File"]
            repl_info.slave_log_pos = int(result["Exec_Master_Log_Pos"])
            repl_info.slave_retrieved_gtid_set = result["Retrieved_Gtid_Set"]
            repl_info.slave_execute_gtid_set = result["Executed_Gtid_Set"]
            repl_info.seconds_Behind_Master = result["Seconds_Behind_Master"]
            repl_info.delay_pos_count = repl_info.master_log_pos - repl_info.slave_log_pos
            if(repl_info.seconds_Behind_Master is None):
                repl_info.seconds_Behind_Master = 0
            if(mysql_status_new["Slave_running"] == "OFF"):
                repl_info.is_slave = 0

        #self.insert_status_log(status_info)
        bb = time.time()
        if(host_info.id == 1):
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
        if(monitor_type == MonitorEnum.Host):
            return self.__cache.get_all_linux_infos()
        elif(monitor_type == MonitorEnum.Status):
            return self.__cache.get_all_status_infos()
        elif(monitor_type == MonitorEnum.Innodb):
            return self.__cache.get_all_innodb_infos()
        elif(monitor_type == MonitorEnum.Replication):
            return self.__cache.get_all_repl_infos()

    def insert_status_log(self, status_info):
        sql = "insert into mysql_web.mysql_status_log(host_id, qps, tps, commit, rollback, connections, " \
              "thread_count, thread_running_count, tmp_tables, tmp_disk_tables, send_bytes, receive_bytes) VALUES " \
              "({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, \'{10}\', \'{11}\')"\
              .format(status_info.host_info.id, status_info.qps, status_info.tps, status_info.commit, status_info.rollback, status_info.connections_per,
                      status_info.threads_count, status_info.threads_run_count, status_info.create_tmp_table_count, status_info.create_tmp_disk_table_count,
                      status_info.send_bytes, status_info.receive_bytes)
        self.__db_util.execute(settings.MySQL_Host, sql)

    def monitor_host_status(self, host_info):
        host_client = None
        linux_info = self.__cache.get_linux_info(host_info.key)
        try:
            host_client = paramiko.SSHClient()
            host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            host_client.connect(host_info.ip, port=22, username="root")

            #监测CPU负载
            self.monitor_host_for_cpu(host_client, linux_info)
            #监测网卡流量
            self.monitor_host_for_net(host_client, linux_info)
            #监测硬盘空间
            self.monitor_host_for_disk(host_client, linux_info)
            #监测linux内存使用情况
            self.monitor_host_for_memory(host_client, linux_info)
            #监控mysql的cpu和memory以及data大小
            self.monitor_host_for_mysql_cpu_and_memory(host_client, host_info, linux_info)
        finally:
            if (host_client != None):
                host_client.close()

    def monitor_host_for_cpu(self, host_client, linux_info):
        stdin, stdout, stderr = host_client.exec_command("cat /proc/loadavg")
        cpu_value = stdout.readlines()[0].split()
        linux_info.cpu_1 = cpu_value[0]
        linux_info.cpu_5 = cpu_value[1]
        linux_info.cpu_15 = cpu_value[2]

    def monitor_host_for_net(self, host_client, linux_info):
        net_send_byte, net_receive_byte = 0, 0
        stdin, stdout, stderr = host_client.exec_command("cat /proc/net/dev")
        for line in stdout.readlines():
            if(line.find("eth") >= 0):
                value_list = []
                for value in line.split(" "):
                    if(len(value) > 0):
                        value_list.append(value)
                net_send_byte = net_send_byte + long(value_list[9])
                net_receive_byte = net_receive_byte + long(value_list[1])

        linux_info.net_send_old = linux_info.net_send_new
        linux_info.net_receive_old = linux_info.net_receive_new
        linux_info.net_send_new = net_send_byte
        linux_info.net_receive_new = net_receive_byte
        linux_info.net_send_byte = linux_info.net_send_new - linux_info.net_send_old
        linux_info.net_receive_byte = linux_info.net_receive_new - linux_info.net_receive_old

    def monitor_host_for_disk(self, host_client, linux_info):
        id_tmp = 0
        max_disk_value = 0
        total_disk_value = 0
        stdin, stdout, stderr = host_client.exec_command("df")
        for line in stdout.readlines():
            id_tmp = id_tmp + 1
            if(id_tmp == 1):
                continue
            values = line.split()
            for value in values:
                if(value.find("%") >= 0):
                    disk_value_int = int(value.replace("%", ""))
                    if(max_disk_value == 0):
                        max_disk_value = disk_value_int
                    else:
                        if(disk_value_int > max_disk_value):
                            max_disk_value = disk_value_int

            list_len = len(values)
            if(list_len >= 3):
                if(list_len == 6):
                    total_disk_value = total_disk_value + int(values[1])
                elif(list_len == 5):
                    total_disk_value = total_disk_value + int(values[0])
        linux_info.disk_value = str(max_disk_value) + "%"
        linux_info.total_disk_value = str(total_disk_value / 1024 / 1024)

    def monitor_host_for_memory(self, host_client, linux_info):
        stdin, stdout, stderr = host_client.exec_command("cat /proc/meminfo")
        for line in stdout.readlines():
            values = line.split(":")
            if(len(values) >= 2):
                if(values[0].find("MemTotal") >= 0):
                    linux_info.memory_total = self.change_byte_to_g(values[1])
                elif(values[0].find("MemFree") >= 0):
                    linux_info.memory_free = self.change_byte_to_g(values[1])
                elif (values[0].strip().lstrip() == "Buffers"):
                    linux_info.memory_buffers = self.change_byte_to_g(values[1])
                elif (values[0].strip().lstrip() == "Cached"):
                    linux_info.memory_cache = self.change_byte_to_g(values[1])
                elif (values[0].find("SwapTotal") >= 0):
                    linux_info.swap_total = self.change_byte_to_g(values[1])
                elif (values[0].find("SwapFree") >= 0):
                    linux_info.swap_free = self.change_byte_to_g(values[1])
        linux_info.memory_free = linux_info.memory_free + linux_info.memory_buffers + linux_info.memory_cache

    def monitor_host_for_mysql_cpu_and_memory(self, host_client, host_info, linux_info):
        stdin, stdout, stderr = host_client.exec_command("cat %s" % host_info.mysql_pid_file)
        linux_info.mysql_pid = int(stdout.readlines()[0])

        stdin, stdout, stderr = host_client.exec_command("top -b -n1 | grep mysql")
        for line in stdout.readlines():
            values = line.split()
            if (int(values[0]) == linux_info.mysql_pid):
                if(float(values[8]) >= 1):
                    #防止获取的CPU为0的情况
                    linux_info.mysql_cpu = values[8]
                linux_info.mysql_memory = values[9]
                break

        #监测MySQL数据目录大小
        stdin, stdout, stderr = host_client.exec_command("du -h %s | tail -n1 | awk '{print $1'}" % host_info.mysql_data_dir)
        linux_info.mysql_data_size = stdout.readlines()[0].replace("\n", "").replace("G", "")

    def change_byte_to_g(self, value):
        return int(value.replace("kB", "")) / 1024 / 1024

    def read_innodb_status(self, host_info):
        innodb_status = self.get_innodb_status_infos(host_info)
        if(innodb_status.has_key("LOG") == True):
            self.get_lsn_info(host_info, innodb_status["LOG"])
        if(innodb_status.has_key("INDIVIDUAL BUFFER POOL INFO") == True):
            self.get_buffer_pool_infos(host_info, innodb_status["INDIVIDUAL BUFFER POOL INFO"])
        if(innodb_status.has_key("LATEST DETECTED DEADLOCK") == True):
            self.get_latest_deadlock(host_info, innodb_status["LATEST DETECTED DEADLOCK"])
        if(innodb_status.has_key("TRANSACTIONS") == True):
            self.get_transactions_info(host_info, innodb_status["TRANSACTIONS"])

    def get_lsn_info(self, host_info, values):
        info_tmp = self.__cache.get_engine_innodb_status_infos(host_info.key)
        num = 0
        for line in values:
            line_split = line.split(" ")
            split_value = line_split[len(line_split) - 1]
            if(num == 1):
                info_tmp.log_lsn = split_value
            elif(num == 2):
                info_tmp.log_flush_lsn = split_value
            elif(num == 3):
                info_tmp.page_flush_lsn = split_value
            elif(num == 4):
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
            if(len(str_value) > 0):
                if(str_value.find("---BUFFER POOL") >= 0):
                    buffer_pool_key = str_value
                    buffer_pool_infos[buffer_pool_key] = []
                else:
                    if(len(buffer_pool_key) > 0):
                        buffer_pool_infos[buffer_pool_key].append(str_value)

        for key, value_list in buffer_pool_infos.items():
            num = 0
            info_tmp = base_class.BaseClass(None)
            buffer_pool_name = key.replace("-", "")
            info_tmp.name = buffer_pool_name
            for line in value_list:
                line_split = line.split(" ")
                split_value = line_split[len(line_split) - 1].replace(",", "")
                if(line.find("unzip_LRU") >= 0):
                    info_tmp.unzip_lur = split_value
                elif(line.find("Free buffers") >= 0):
                    info_tmp.free_pages = split_value
                elif(line.find("Buffer pool size ") >= 0):
                    info_tmp.total_pages = split_value
                elif(line.find("Database pages") >= 0):
                    info_tmp.lru_pages = split_value
                elif(line.find("Old database pages") >= 0):
                    info_tmp.old_pages = split_value
                elif(line.find("Modified db pages") >= 0):
                    info_tmp.dirty_pages = split_value
                elif(line.find("Buffer pool hit rate") >= 0):
                    info_tmp.buffer_pool_hit = int(line_split[4].replace(",", "")) / int(line_split[6].replace(",", "")) * 100
                elif(line.find("reads") >= 0 and line.find("creates") >= 0 and line.find("writes") >= 0):
                    info_tmp.reads_per = line_split[0]
                    info_tmp.creates_per = line_split[2]
                    info_tmp.writes_per = line_split[4]
                elif(line.find("Pending reads") >= 0):
                    info_tmp.pending_reads = split_value
                num = num + 1
                cache.Cache().get_engine_innodb_status_infos(host_info.key).buffer_pool_infos[buffer_pool_name] = info_tmp

    def get_latest_deadlock(self, host_info, values):
        info_tmp = self.__cache.get_engine_innodb_status_infos(host_info.key)
        if(len(values) > 0):
            info_tmp.latest_deadlock = ""
        for line in values:
            info_tmp.latest_deadlock = info_tmp.latest_deadlock + line + "\n"

    def get_transactions_info(self, host_info, values):
        #status_info = self.__cache.get_status_infos(host_info.key)
        info_tmp = self.__cache.get_engine_innodb_status_infos(host_info.key)
        for line in values:
            line_split = line.split(" ")
            split_value = line_split[len(line_split) - 1].replace(",", "")
            if(line.find("History list length") >= 0):
                info_tmp.undo_history_list_len = split_value
            elif(line.find("Trx id counter") >= 0):
                pass
                #if(status_info)

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
            if(len(str_value) > 0):
                if(str_value in flag_list):
                    key_name = str_value
                    innodb_status_infos[key_name] = []
                else:
                    if(len(key_name) > 0):
                        innodb_status_infos[key_name].append(str_value)
        return innodb_status_infos
