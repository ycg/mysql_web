
class InnodbStatus():
    def __init__(self):
        self.log_lsn = 0
        self.log_flush_lsn = 0
        self.page_flush_lsn = 0
        self.checkpoint_lsn = 0
