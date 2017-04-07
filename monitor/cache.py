import base_class, host_info, collections, db_util, settings, mysql_branch, threadpool

class Cache(object):
    __number = False
    __instance = None
    __thread_pool = None
    __tablespace = collections.OrderedDict()
    __host_infos = collections.OrderedDict()
    __repl_infos = collections.OrderedDict()
    __linux_infos = collections.OrderedDict()
    __status_infos = collections.OrderedDict()
    __innodb_infos = collections.OrderedDict()
    __innodb_status_infos = collections.OrderedDict()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if(Cache.__instance is None):
            Cache.__instance = object.__new__(cls, *args, **kwargs)
        return Cache.__instance

    def load_all_host_infos(self):
        if(self.__thread_pool == None):
            self.__thread_pool = threadpool.ThreadPool(settings.THREAD_POOL_SIZE)
        sql = "select host_id, host, port, user, password, remark, is_master, is_slave, master_id, is_deleted from mysql_web.host_infos;"
        for row in db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
            host_id = row["host_id"]
            if(self.__host_infos.has_key(host_id) == True):
                host_info_temp = self.__host_infos[host_id]
            else:
                host_info_temp = host_info.HoseInfo()
                host_info_temp.id = host_id
                self.__host_infos[host_info_temp.id] = host_info_temp
            host_info_temp.host = row["host"]
            host_info_temp.port = row["port"]
            host_info_temp.user = row["user"]
            host_info_temp.password = row["password"]
            host_info_temp.remark = row["remark"]
            host_info_temp.is_master = row["is_master"]
            host_info_temp.is_slave = row["is_slave"]
            host_info_temp.master_id = row["master_id"]
            host_info_temp.key = host_info_temp.id
            if(row["is_deleted"] == 1):
                self.remove_key(self.__tablespace, host_id)
                self.remove_key(self.__host_infos, host_id)
                self.remove_key(self.__repl_infos, host_id)
                self.remove_key(self.__status_infos, host_id)
                self.remove_key(self.__host_infos, host_id)
                self.remove_key(self.__innodb_infos, host_id)
                self.remove_key(self.__linux_infos, host_id)
                self.remove_key(self.__innodb_status_infos, host_id)
            else:
                if(self.__repl_infos.has_key(host_id) == False):
                    self.__tablespace[host_id] = {}
                if(self.__repl_infos.has_key(host_id) == False):
                    self.__repl_infos[host_id] = base_class.BaseClass(host_info_temp)
                if(self.__linux_infos.has_key(host_id) == False):
                    self.__linux_infos[host_id] = base_class.BaseClass(host_info_temp)
                if(self.__status_infos.has_key(host_id) == False):
                    self.__status_infos[host_id] = base_class.BaseClass(host_info_temp)
                if(self.__innodb_infos.has_key(host_id) == False):
                    self.__innodb_infos[host_id] = base_class.BaseClass(host_info_temp)
                if(self.__innodb_status_infos.has_key(host_id) == False):
                    self.__innodb_status_infos[host_id] = base_class.BaseClass(host_info_temp)
                    self.__innodb_status_infos[host_id].buffer_pool_infos = collections.OrderedDict()

        self.check_mysql_server_version_and_branch()
        result = "load all host infos ok."
        print(result)
        return result

    def join_thread_pool(self, method_name):
        requests = threadpool.makeRequests(method_name, list(self.get_all_host_infos()), None)
        for request in requests:
            self.__thread_pool.putRequest(request)
        self.__thread_pool.poll()

    def remove_key(self, dic, key):
        if(dic.has_key(key) == True):
            dic.pop(key)

    def get_all_host_infos(self):
        return self.__host_infos.values()

    def get_all_repl_infos(self):
        return self.__repl_infos.values()

    def get_all_status_infos(self):
        return self.__status_infos.values()

    def get_all_innodb_infos(self):
        return self.__innodb_infos.values()

    def get_all_linux_infos(self):
        return self.__linux_infos.values()

    def get_mysql_web_host_info(self):
        return self.__mysql_web_host_info

    def get_host_info(self, key):
        return self.get_value_for_key(self.__host_infos, key)

    def get_repl_info(self, key):
        return self.get_value_for_key(self.__repl_infos, key)

    def get_linux_info(self, key):
        return self.get_value_for_key(self.__linux_infos, key)

    def get_status_infos(self, key):
        return self.get_value_for_key(self.__status_infos, key)

    def get_innodb_infos(self, key):
        return self.get_value_for_key(self.__innodb_infos, key)

    def get_engine_innodb_status_infos(self, key):
        return self.get_value_for_key(self.__innodb_status_infos, key)

    def get_value_for_key(self, dir, key):
        if(dir.has_key(key)):
            return dir[key]
        return None

    def check_mysql_server_version_and_branch(self):
        for host_info in self.__host_infos.values():
            result = db_util.DBUtil().fetchall(host_info, "show global variables where variable_name in ('version', 'version_comment');")
            host_info.version = result[0]["Value"]
            str_branch = result[1]["Value"]
            if(str_branch.find(mysql_branch.MySQLBranch.Percona.name) >= 0):
                host_info.branch = mysql_branch.MySQLBranch.Percona
            elif(str_branch.find(mysql_branch.MySQLBranch.Mariadb.name) >= 0):
                host_info.branch = mysql_branch.MySQLBranch.Mariadb
            else:
                host_info.branch = mysql_branch.MySQLBranch.MySQL
