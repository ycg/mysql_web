import base_class, host_info, collections, db_util, settings

class Cache(object):
    __number = False
    __instance = None
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
                self.__host_infos.pop(host_id)
                self.__repl_infos.pop(host_id)
                self.__status_infos.pop(host_id)
                self.__innodb_infos.pop(host_id)
                self.__linux_infos.pop(host_id)
            else:
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
        return "load all host infos ok."

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

    def get_repl_info(self, key):
        return self.__repl_infos[key]

    def get_linux_info(self, key):
        return self.__linux_infos[key]

    def get_status_infos(self, key):
        return self.__status_infos[key]

    def get_innodb_infos(self, key):
        return self.__innodb_infos[key]

    def get_mysql_web_host_info(self):
        return self.__mysql_web_host_info

    def get_engine_innodb_status_infos(self, key):
        return self.__innodb_status_infos[key]
