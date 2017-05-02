import hashlib
from flask_login import UserMixin

import cache

class User(UserMixin):
    def __init__(self, username):
        self.username = username
        self.id = self.get_id()
        self.password = self.get_password()

    def verify_password(self, password, result):
        if self.id is None or self.password is None:
            result.error = "user name incorrect"
            return False
        if(self.password == self.get_value_for_md5(password)):
            result.success = "ok"
            return True
        result.error = "password incorrect"
        return False

    def get_password(self):
        return self.get_user_info_by_user_name(self.username, "user_password")

    def get_id(self):
        return self.get_user_info_by_user_name(self.username, "user_id")

    def get_user_info_by_user_name(self, user_name, attr_name):
        list_tmp = cache.Cache().get_mysql_web_user_infos()
        for info in list_tmp:
            if(info.user_name == user_name):
                value = getattr(info, attr_name)
                return value
        return None

    @staticmethod
    def get(user_id):
        if not user_id:
            return None
        user_info = cache.Cache().get_mysql_web_user_infos(user_id)
        if(user_info != None):
            return User(user_info.user_name)
        return None

    def get_value_for_md5(self, password):
        obj = hashlib.md5()
        obj.update(password)
        return obj.hexdigest()