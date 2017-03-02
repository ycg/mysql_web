import threading

class ReportThread(threading.Thread):
    __instance = None

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def __new__(cls, *args, **kwargs):
        if(ReportThread.__instance is None):
            ReportThread.__instance == object.__new__(cls, *args, **kwargs)
        return ReportThread.__instance

    def run(self):
        while(True):
            pass
