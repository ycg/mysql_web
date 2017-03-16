class HoseInfo():
    def __init__(self, host="", port=3306, user="", password="", remark=""):
        self.host = host
        self.port = port
        self.user = user
        self.remark = remark
        self.password = password
        self.key = host + ":" + str(port)