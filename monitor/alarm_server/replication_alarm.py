
import base_alarm
from monitor import cache

class ReplicationAlarm(base_alarm.BaseAlarm):
    def __init__(self):
        pass

    def alarm_check(self, host_id):
        repl_info = cache.Cache().get_repl_info(host_id)
