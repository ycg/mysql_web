import threading, time, traceback

import monitor.base_class, monitor.cache, monitor.mail_util

class AlarmType():
    def __init__(self):
        pass

    Slave_Delay_Time = 5
    Slave_Thread_Exception = 1

    MySQL_QPS = 9
    MySQL_TPS = 10
    MySQL_Crash = 3
    MySQL_Thread_Too_Much = 4
    MySQL_Thread_Execute_Long_Time = 5

    IO = 8
    CPU_Sys = 6
    CPU_User = 7

    Mail_To = 11

class AlarmFrequency():
    def __init__(self):
        pass

    total_count = 0
    latest_time = 0
    current_alarm_count = 0

class AlarmServer(threading.Thread):
    __times = 0
    __alarm_details = {}
    __alarm_content = {}
    __cache = monitor.cache.Cache()
    __host_alarm_parameter = {}
    __global_alarm_parameter = {}

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.init_global_alarm_parameter()

    def run(self):
        while(True):
            try:
                self.slave_for_alarm()
                self.mysql_status_for_alarm()
            except Exception, e:
                traceback.print_exc()
            time.sleep(1)
            self.__times += 1

    def init_global_alarm_parameter(self):
        self.__global_alarm_parameter[AlarmType.Slave_Delay_Time] = 5
        self.__global_alarm_parameter[AlarmType.MySQL_Thread_Execute_Long_Time] = 5
        self.__global_alarm_parameter[AlarmType.Mail_To] = "yangcaogui.sh@superjia.com"

        for host_info in monitor.cache.Cache().get_all_host_infos():
            self.__alarm_details[host_info.host_id] = {}

    def update_host_alarm_parameter(self, host_id, values):
        if(self.__host_alarm_parameter.has_key(host_id) == False):
            self.__host_alarm_parameter[host_id] = values

    def os_for_alarm(self):
        pass

    def slave_for_alarm(self):
        for info in monitor.cache.Cache().get_all_repl_infos():
            if(info.is_slave == 1):
                alarm_parameter = self.get_host_alarm_parameter(info.host_info.host_id)

                if(info.io_status == "No" or info.sql_status == "No"):
                    self.alarm_for_error(info.host_info, AlarmType.Slave_Thread_Exception)
                else:
                    self.alarm_for_success(info.host_info, AlarmType.Slave_Thread_Exception)

                if(info.seconds_Behind_Master >= alarm_parameter[AlarmType.Slave_Delay_Time]):
                    self.alarm_for_error(info.host_info, AlarmType.Slave_Delay_Time)
                else:
                    self.alarm_for_success(info.host_info, AlarmType.Slave_Delay_Time)

    def mysql_status_for_alarm(self):
        for info in self.__cache.get_all_status_infos():
            if(info.threads_count > 2):
                self.alarm_for_error(info.host_info, AlarmType.MySQL_Thread_Too_Much)

    def alarm_for_error(self, host_info, alarm_type):
        alarm_ok = 0
        detail = self.get_alarm_type_detail_by_host_id(host_info.host_id, alarm_type)

        if(self.__times % 2 == 0):
            if(detail.current_alarm_count >= 0 and detail.current_alarm_count <= 20):
                alarm_ok = 1
        if(self.__times % 60 == 0):
            if(detail.current_alarm_count > 20 and detail.current_alarm_count <= 40):
                alarm_ok = 1
        if(self.__times % 600 == 0):
            if(detail.current_alarm_count > 40):
                alarm_ok = 1

        if(alarm_ok == 1):
            self.send_alarm_mail(host_info, alarm_type)
            detail.total_count = detail.total_count + 1
            detail.current_alarm_count = detail.current_alarm_count + 1
            detail.latest_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def alarm_for_success(self, host_info, alarm_type):
        detail = self.get_alarm_type_detail_by_host_id(host_info.host_id, alarm_type)
        detail.current_alarm_count = 0

    def get_alarm_type_detail_by_host_id(self, host_id, alarm_type):
        if(self.__alarm_details[host_id].has_key(alarm_type) == False):
            self.__alarm_details[host_id][alarm_type] = AlarmFrequency()
        return self.__alarm_details[host_id][alarm_type]

    #region send alarm mail

    def send_replication_alarm_mail(self):
        pass

    def send_alarm_mail(self, host_info, alarm_type):
        print("send ok")
        monitor.mail_util.send_text("thread count is too much", self.__global_alarm_parameter[AlarmType.Mail_To], "test")

    #endregion

    def get_host_alarm_parameter(self, host_id):
        if(self.__host_alarm_parameter.has_key(host_id)):
            return self.__host_alarm_parameter[host_id]
        return self.__global_alarm_parameter