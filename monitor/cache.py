# -*- coding: utf-8 -*-

import os, threadpool
import base_class, host_info, collections, db_util, settings, mysql_branch, tablespace

class Cache(object):
    __number = False
    __instance = None
    __thread_pool = None
    __user_infos = collections.OrderedDict()
    __tablespace = collections.OrderedDict()
    __host_infos = collections.OrderedDict()
    __repl_infos = collections.OrderedDict()
    __linux_infos = collections.OrderedDict()
    __status_infos = collections.OrderedDict()
    __innodb_infos = collections.OrderedDict()
    __analyze_infos = collections.OrderedDict()
    __innodb_status_infos = collections.OrderedDict()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if (Cache.__instance is None):
            Cache.__instance = object.__new__(cls, *args, **kwargs)
        return Cache.__instance

    def load_all_host_infos(self):
        if (self.__thread_pool == None):
            self.__thread_pool = threadpool.ThreadPool(settings.THREAD_POOL_SIZE)
        sql = "select host_id, host, port, user, password, remark, is_master, is_slave, master_id, is_deleted, ssh_port from mysql_web.host_infos;"
        for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
            host_id = row["host_id"]
            if (self.__host_infos.has_key(host_id) == True):
                host_info_temp = self.__host_infos[host_id]
            else:
                host_info_temp = host_info.HoseInfo()
                host_info_temp.host_id = host_id
                self.__host_infos[host_info_temp.host_id] = host_info_temp
            host_info_temp.host = row["host"]
            host_info_temp.port = row["port"]
            host_info_temp.user = row["user"]
            host_info_temp.password = row["password"]
            host_info_temp.remark = row["remark"]
            host_info_temp.master_host_id = 0
            host_info_temp.is_master = bool(row["is_master"])
            host_info_temp.is_slave = bool(row["is_slave"])
            host_info_temp.master_id = row["master_id"]
            host_info_temp.ssh_port = row["ssh_port"]
            host_info_temp.key = host_info_temp.host_id
            if (row["is_deleted"] == 1):
                self.remove_key(self.__tablespace, host_id)
                self.remove_key(self.__host_infos, host_id)
                self.remove_key(self.__repl_infos, host_id)
                self.remove_key(self.__status_infos, host_id)
                self.remove_key(self.__host_infos, host_id)
                self.remove_key(self.__innodb_infos, host_id)
                self.remove_key(self.__linux_infos, host_id)
                self.remove_key(self.__innodb_status_infos, host_id)
                self.remove_key(self.__analyze_infos, host_id)
            else:
                if (self.__tablespace.has_key(host_id) == False):
                    self.__tablespace[host_id] = base_class.BaseClass(host_info_temp)
                if (self.__repl_infos.has_key(host_id) == False):
                    self.__repl_infos[host_id] = base_class.BaseClass(host_info_temp)
                if (self.__linux_infos.has_key(host_id) == False):
                    self.__linux_infos[host_id] = base_class.BaseClass(host_info_temp)
                if (self.__status_infos.has_key(host_id) == False):
                    self.__status_infos[host_id] = base_class.BaseClass(host_info_temp)
                if (self.__innodb_infos.has_key(host_id) == False):
                    self.__innodb_infos[host_id] = self.init_innodb_info(base_class.BaseClass(host_info_temp))
                if (self.__analyze_infos.has_key(host_id) == False):
                    self.__analyze_infos[host_id] = self.init_analyze_info(base_class.BaseClass(None))
                if (self.__innodb_status_infos.has_key(host_id) == False):
                    self.__innodb_status_infos[host_id] = base_class.BaseClass(host_info_temp)
                    self.__innodb_status_infos[host_id].buffer_pool_infos = collections.OrderedDict()

        self.load_mysql_web_user_infos()
        self.check_mysql_server_version_and_branch()
        self.check_master_and_slave_relation()
        result = "load all host infos ok."
        print(result)
        return result

    def add_user_info(self, info):
        if (info.is_deleted == 1):
            if (self.__user_infos.has_key(info.user_id) == True):
                self.__user_infos.pop(info.user_id)
        else:
            self.__user_infos[info.user_id] = info

    def load_mysql_web_user_infos(self):
        sql = "select id, user_name, user_password, is_deleted from mysql_web.mysql_web_user_info;"
        for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
            user_info = base_class.BaseClass(None)
            user_info.user_id = row["id"]
            user_info.user_name = row["user_name"]
            user_info.user_password = row["user_password"]
            user_info.is_deleted = row["is_deleted"]
            self.add_user_info(user_info)

    def init_analyze_info(self, analyze_info):
        for key in Analyze_OS_Key:
            setattr(analyze_info, key + Value_Min, 0)
            setattr(analyze_info, key + Value_Max, 0)
            setattr(analyze_info, key + Value_Avg, 0)
            setattr(analyze_info, key + Value_Sum, 0)
            setattr(analyze_info, key + Value_Count, 0)

        for key in Analyze_MySQL_Key:
            setattr(analyze_info, key + Value_Min, 0)
            setattr(analyze_info, key + Value_Max, 0)
            setattr(analyze_info, key + Value_Avg, 0)
            setattr(analyze_info, key + Value_Sum, 0)
            setattr(analyze_info, key + Value_Count, 0)

        return analyze_info

    def init_innodb_info(self, innodb_info):
        innodb_info.innodb_ibuf_size = 0
        innodb_info.innodb_ibuf_merges = 0
        innodb_info.innodb_ibuf_free_list = 0
        innodb_info.innodb_ibuf_merged_inserts = 0
        innodb_info.innodb_ibuf_merged_deletes = 0
        innodb_info.innodb_ibuf_merged_delete_marks = 0
        innodb_info.innodb_ibuf_merges_old = 0
        innodb_info.innodb_ibuf_merges_new = 0
        innodb_info.innodb_ibuf_merged_inserts_old = 0
        innodb_info.innodb_ibuf_merged_deletes_old = 0
        innodb_info.innodb_ibuf_merged_delete_marks_old = 0
        innodb_info.innodb_ibuf_merged_inserts_new = 0
        innodb_info.innodb_ibuf_merged_deletes_new = 0
        innodb_info.innodb_ibuf_merged_delete_marks_new = 0
        innodb_info.innodb_mutex_os_waits = 0
        innodb_info.innodb_mutex_os_waits_old = 0
        innodb_info.innodb_mutex_os_waits_new = 0
        innodb_info.innodb_mutex_spin_rounds = 0
        innodb_info.innodb_mutex_spin_rounds_old = 0
        innodb_info.innodb_mutex_spin_rounds_new = 0
        innodb_info.innodb_mutex_spin_waits = 0
        innodb_info.innodb_mutex_spin_waits_old = 0
        innodb_info.innodb_mutex_spin_waits_new = 0
        innodb_info.innodb_s_lock_os_waits = 0
        innodb_info.innodb_s_lock_os_waits_old = 0
        innodb_info.innodb_s_lock_os_waits_new = 0
        innodb_info.innodb_s_lock_spin_rounds = 0
        innodb_info.innodb_s_lock_spin_rounds_old = 0
        innodb_info.innodb_s_lock_spin_rounds_new = 0
        innodb_info.innodb_s_lock_spin_waits = 0
        innodb_info.innodb_s_lock_spin_waits_old = 0
        innodb_info.innodb_s_lock_spin_waits_new = 0
        innodb_info.innodb_x_lock_os_waits = 0
        innodb_info.innodb_x_lock_os_waits_old = 0
        innodb_info.innodb_x_lock_os_waits_new = 0
        innodb_info.innodb_x_lock_spin_rounds = 0
        innodb_info.innodb_x_lock_spin_rounds_old = 0
        innodb_info.innodb_x_lock_spin_rounds_new = 0
        innodb_info.innodb_x_lock_spin_waits = 0
        innodb_info.innodb_x_lock_spin_waits_old = 0
        innodb_info.innodb_x_lock_spin_waits_new = 0
        innodb_info.innodb_mutex_ratio = 0
        innodb_info.innodb_s_ratio = 0
        innodb_info.innodb_x_ratio = 0
        return innodb_info

    def join_thread_pool(self, method_name):
        requests = threadpool.makeRequests(method_name, list(self.get_all_host_infos()), None)
        for request in requests:
            self.__thread_pool.putRequest(request)
        self.__thread_pool.poll()

    def remove_key(self, dic, key):
        if (dic.has_key(key) == True):
            dic.pop(key)

    def get_all_host_infos(self, keys=[]):
        # return self.__host_infos.values()
        return self.get_values_by_keys(self.__host_infos, keys)

    def get_all_repl_infos(self, keys=[]):
        # return self.__repl_infos.values()
        # keys = list(keys)
        return self.get_values_by_keys(self.__repl_infos, keys)

    def get_all_status_infos(self, keys=[]):
        # return self.__status_infos.values()
        return self.get_values_by_keys(self.__status_infos, keys)

    def get_all_innodb_infos(self, keys=[]):
        # return self.__innodb_infos.values()
        return self.get_values_by_keys(self.__innodb_infos, keys)

    def get_all_linux_infos(self, keys=[]):
        # return self.__linux_infos.values()
        return self.get_values_by_keys(self.__linux_infos, keys)

    def get_mysql_web_user_infos(self, key=None):
        if (key == None):
            return self.__user_infos.values()
        return self.get_value_for_key(self.__user_infos, key)

    def get_all_tablespace_infos(self):
        return self.__tablespace.values()

    def get_mysql_web_host_info(self):
        return self.__mysql_web_host_info

    def get_host_info(self, key):
        return self.get_value_for_key(self.__host_infos, key)

    def get_repl_info(self, key):
        return self.get_value_for_key(self.__repl_infos, key)

    def get_linux_info(self, key):
        return self.get_value_for_key(self.__linux_infos, key)

    def get_status_info(self, key):
        return self.get_value_for_key(self.__status_infos, key)

    def get_innodb_info(self, key):
        return self.get_value_for_key(self.__innodb_infos, key)

    def get_analyze_info(self, key):
        return self.get_value_for_key(self.__analyze_infos, key)

    def get_tablespace_info(self, key):
        return self.get_value_for_key(self.__tablespace, key)

    def get_engine_innodb_status_infos(self, key):
        return self.get_value_for_key(self.__innodb_status_infos, key)

    def get_value_for_key(self, dir, key):
        if (dir.has_key(key)):
            return dir[key]
        return None

    def get_values_by_keys(self, dir, keys):
        if (len(keys) <= 0):
            return dir.values()
        result = []
        for id in keys:
            info = self.get_value_for_key(dir, int(id))
            if (info != None):
                result.append(info)
        return result

    def check_master_and_slave_relation(self):
        """for key, value in self.__repl_infos.items():
            result = db_util.DBUtil().fetchone(self.__host_infos[key], "show slave status;")
            if (result != None and int(result["Read_Master_Log_Pos"]) > 0):
                value.is_slave = 1
                value.master_host_id = 0
                value.host_info.role = "S"
                value.host_info.is_slave = True
                master_ip = result["Master_Host"]
                master_port = result["Master_Port"]
                for host_info in self.__host_infos.values():
                    if (host_info.host == master_ip and host_info.port == master_port):
                        value.master_host_id = host_info.host_id
                        break
            else:
                value.host_info.role = "M"
                value.host_info.is_master = True"""

        #有的mysql既是主库也是从库，这个要理清逻辑
        uuid_key = "Slave_UUID"
        for key, value in self.__repl_infos.items():
            result = db_util.DBUtil().fetchall(value.host_info, "show slave hosts;")
            if (len(result) <= 0):
                #解决集群中只有一个mysql的情况
                slave_status = db_util.DBUtil().fetchone(value.host_info, "show slave status;")
                if(slave_status != None):
                    value.host_info.is_slave = True
                else:
                    value.host_info.is_master = True
                continue

            number = 0
            value.master_name = ""
            for row in result:
                if(uuid_key not in row.keys()):
                    continue
                number += 1
                for host_info in self.__host_infos.values():
                    if (host_info.server_uuid == row[uuid_key]):
                        host_info.is_slave = True
                        repl_info = self.__repl_infos[host_info.host_id]
                        host_info.master_name = value.host_info.remark
                        repl_info.master_host_id = value.host_info.host_id
                        host_info.master_host_id = value.host_info.host_id
            #解决"show slave status"有数据但UUID为空的情况
            if(number >= 1 and len(result) > 0):
                value.host_info.is_master = True
            else:
                value.host_info.is_slave = True

    def check_mysql_server_version_and_branch(self):
        for host_info in self.__host_infos.values():
            result = db_util.DBUtil().fetchall(host_info, "show global variables where variable_name in ('version', 'version_comment', 'datadir', 'pid_file', 'innodb_buffer_pool_size', 'server_uuid');")
            data = {}
            for row in result:
                data[row.get("Variable_name")] = row.get("Value")
            host_info.version = data["version"]
            str_branch = data["version_comment"]
            host_info.mysql_data_dir = data["datadir"]
            host_info.server_uuid = data["server_uuid"]
            host_info.innodb_buffer_pool_size = tablespace.get_data_length(long(data["innodb_buffer_pool_size"]))
            if (str_branch.find(mysql_branch.MySQLBranch.Percona.name) >= 0):
                host_info.branch = mysql_branch.MySQLBranch.Percona
            elif (str_branch.find(mysql_branch.MySQLBranch.Mariadb.name) >= 0):
                host_info.branch = mysql_branch.MySQLBranch.Mariadb
            else:
                host_info.branch = mysql_branch.MySQLBranch.MySQL
            host_info.mysql_pid_file = data["pid_file"]
            if (os.path.exists(host_info.mysql_pid_file) == False):
                host_info.mysql_pid_file = os.path.join(host_info.mysql_data_dir, host_info.mysql_pid_file)

Value_Min = "_min"
Value_Max = "_max"
Value_Avg = "_avg"
Value_Sum = "_sum"
Value_Count = "_count"

Analyze_OS_Key = [
]

Analyze_MySQL_Key = [
    "qps",
    "tps",
    "threads_count",
    "create_tmp_table_count",
    "create_tmp_disk_table_count",
]