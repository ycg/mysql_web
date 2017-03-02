import base_class, host_info, collections, db_util

class Cache(object):
    __instance = None
    __host_infos = collections.OrderedDict()
    __repl_infos = collections.OrderedDict()
    __status_infos = collections.OrderedDict()
    __innodb_infos = collections.OrderedDict()

    def __init__(self):
        self.load_all_host_infos()
        for value in self.__host_infos.values():
            self.__repl_infos[value.id] = base_class.BaseClass(value)
            self.__status_infos[value.id] = base_class.BaseClass(value)
            self.__innodb_infos[value.id] = base_class.BaseClass(value)

    def __new__(cls, *args, **kwargs):
        if(Cache.__instance is None):
            Cache.__instance = object.__new__(cls, *args, **kwargs)
        return Cache.__instance

    def load_all_host_infos(self):
        '''
        host_info1 = host_info.HoseInfo("192.168.11.129", 3306, "yangcg", "yangcaogui", "Master")
        host_info2 = host_info.HoseInfo("192.168.11.130", 3306, "yangcg", "yangcaogui", "Slave")
        self.__host_infos[host_info1.key] = host_info1
        self.__host_infos[host_info2.key] = host_info2'''

        monitor_host_info = host_info.HoseInfo(host="192.168.11.128", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")
        sql = "select host_id, host, port, user, password, remark, is_master, is_slave, master_id " \
              "from mysql_web.host_infos where is_deleted = 0;"
        for row in db_util.DBUtil().fetchall(monitor_host_info, sql):
            host_info_temp = host_info.HoseInfo()
            host_info_temp.id = row["host_id"]
            host_info_temp.host = row["host"]
            host_info_temp.port = row["port"]
            host_info_temp.user = row["user"]
            host_info_temp.password = row["password"]
            host_info_temp.remark = row["remark"]
            host_info_temp.is_master = row["is_master"]
            host_info_temp.is_slave = row["is_slave"]
            host_info_temp.master_id = row["master_id"]
            host_info_temp.key = host_info_temp.id
            self.__host_infos[host_info_temp.id] = host_info_temp

    def get_all_host_infos(self):
        return self.__host_infos.values()

    def get_all_repl_infos(self):
        return self.__repl_infos.values()

    def get_all_status_infos(self):
        return self.__status_infos.values()

    def get_all_innodb_infos(self):
        return self.__innodb_infos.values()

    def get_repl_info(self, key):
        return self.__repl_infos[key]

    def get_status_infos(self, key):
        return self.__status_infos[key]

    def get_innodb_infos(self, key):
        return self.__innodb_infos[key]