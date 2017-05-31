
import threading, time

class BackupBase(threading.Thread):
    def __init__(self, backup_info, ):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.backup_info = backup_info

    def run(self):
        self.backup()

    def backup(self):
        pass

    def get_current_time(self):
        return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))