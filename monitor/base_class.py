class BaseClass(object):
    trx_count = 0
    old_trx_count = 0
    new_trx_count = 0
    history_list_length = 0
    net_send_new = 0
    net_receive_new = 0

    def __init__(self, host_info):
        self.host_info = host_info
