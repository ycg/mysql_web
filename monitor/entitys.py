class BaseClass(object):
    trx_count = 0
    old_trx_count = 0
    new_trx_count = 0
    history_list_length = 0
    net_send_new = 0
    net_receive_new = 0
    thread_waits_count = 0

    def __init__(self, host_info):
        self.host_info = host_info

class HoseInfo():
    def __init__(self, host="", port=3306, user="", password="", remark=""):
        self.host = host
        self.port = port
        self.user = user
        self.remark = remark
        self.password = password
        self.key = host + ":" + str(port)


class Entity():
    def __init__(self):
        pass


