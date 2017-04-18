import enum, db_util, cache, base_class, json

class PrivEnum(enum.Enum):
    SELECT = 1
    INSERT = 2
    UPDATE = 3
    DELETE = 4

class MySQLUser():
    __host_info = None

    def __init__(self, host_id):
        self.__host_info = cache.Cache().get_host_info(host_id)

    def query_user(self, name, ip):
        if(self.__host_info == None):
            return []
        sql = "select host, user, Select_priv, Insert_priv, Update_priv, Delete_priv from mysql.user where 1 = 1 "
        if(len(name) > 0):
            sql += "and user like '%{0}%'".format(name)
        if(len(ip) > 0):
            sql += "and host like '%{0}%'".format(ip)
        print(sql)
        return self.get_user_infos(db_util.DBUtil().fetchall(self.__host_info, sql))

    def get_all_users(self):
        sql = "select host, user, Select_priv, Insert_priv, Update_priv, Delete_priv from mysql.user"
        return self.get_user_infos(db_util.DBUtil().fetchall(self.__host_info, sql))

    def get_user_by_ip(self, ip):
        sql = "select host, user, Select_priv, Insert_priv, Update_priv, Delete_priv from mysql.user where host='{0}'".format(ip)
        return self.get_user_infos(db_util.DBUtil().fetchall(self.__host_info, sql))

    def get_user_by_name(self, name):
        sql = "select host, user, Select_priv, Insert_priv, Update_priv, Delete_priv from mysql.user where user='{0}'".format(name)
        return self.get_user_infos(db_util.DBUtil().fetchall(self.__host_info, sql))

    def get_user_infos(self, rows):
        result = []
        for row in rows:
            user_info = base_class.BaseClass(None)
            user_info.host = row["host"]
            user_info.user = row["user"]
            user_info.select = row["Select_priv"]
            user_info.insert = row["Insert_priv"]
            user_info.update = row["Update_priv"]
            user_info.delete = row["Delete_priv"]
            result.append(user_info)
        return result

    def get_privs_by_user(self, name, ip):
        result = []
        sql = "show grants for '{0}'@'{1}'".format(name, ip)
        for row in db_util.DBUtil().fetchall(self.__host_info, sql):
            result.append(row.values()[0])
        return "</br>".join(result)
        #return json.dumps(result, default=lambda o: o.__dict__)

    def add_user(self, user_info):
        sql = "create user '{0}'@'{1}' identified by '{2}';\n".format(user_info.name, user_info.ip, user_info.password)
        for db_name in user_info.db_list:
            sql += "grant select, update, insert on {0}.* to '{1}'@'{2}';\n".format(db_name, user_info.name, user_info.ip)
        sql += "flush privileges;"
        print(sql)

    def drop_user(self, name, ip):
        db_util.DBUtil().execute(self.__host_info, "drop user '{0}'@'{1}';".format(name, ip))

    def exists_user(self, name, ip):
        sql = "select host, user, Select_priv, Insert_priv, Update_priv, Delete_priv from mysql.user where user='{0}' and host='{1}'".format(name, ip)
        result = self.get_user_infos(db_util.DBUtil().fetchall(self.__host_info, sql))
        if(len(result) > 0):
            return True
        return False

    def drop_user(self, ip, name):
        db_util.DBUtil().execute(self.__host_info, "drop user '{0}'@'{1}';".format(name, ip))

    def get_all_database_name(self):
        result = []
        for row in db_util.DBUtil().fetchall(self.__host_info, "show databases;"):
            info = base_class.BaseClass(None)
            info.text = row.values()[0]
            result.append(info)
        return json.dumps(result, default=lambda o: o.__dict__)

