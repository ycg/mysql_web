
import threading, time

class BackupServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while(True):
            time.sleep(1)


