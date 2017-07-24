# -*- coding: utf-8 -*-

import monitor.cache, monitor.mail_util, settings
import enum, threading, time, traceback

#通过配置属性名称来获取数据
#通过配置阀值来判断
#有三种情况
#1.等于多少
#2.大于多少
#3.小于多少

class Operation(enum.Enum):
    #等于
    EQ = 0
    #大于等于
    GE = 1
    #大于
    GT = 2
    #小于等于
    LE = 3
    #小于
    LT = 4
    #不等于
    NE = 5

class AlarmEntity():
    def __init__(self, name, attribute_name, value, operation, title):
        self.name = name
        self.title = title
        self.value = value
        self.alarm_count = 0
        self.operation = operation
        self.last_send_alarm_time = ""
        self.attribute_name = attribute_name

Alarm_Info = {}

Replication_Alarm_Setting_List = [
    AlarmEntity("slave io thread", "io_status", "No", Operation.EQ, "{0} Slave IO Thread Error"),
    AlarmEntity("slave sql thread", "sql_status", "No", Operation.EQ, "{0} Slave SQL Thread Error"),
]

class AlarmServer(threading.Thread):
    __times = 0

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while(True):
            try:
                if(self.__times % 5 == 0):
                    for repl_info in monitor.cache.Cache().get_all_repl_infos():
                        if(repl_info.host_info.is_slave):
                            self.check_alarm_setting(repl_info, Replication_Alarm_Setting_List)
            except Exception:
                traceback.print_exc()
            time.sleep(1)
            self.__times += 1

    def get_value(self, obj, attribute_name):
        return getattr(obj, attribute_name)

    def check_alarm_setting(self, monitor_info, alarm_setting_list):
        for info in alarm_setting_list:
            value = self.get_value(monitor_info, info.attribute_name)
            if(info.operation == Operation.EQ):
                if(value == info.value):
                    #发送邮件，并检查告警次数
                    print("1--------------------000000000000-----------------", monitor_info.host_info.remark, info.name, info)
                    self.check_alarm_count_and_send_mail(monitor_info, info)
                else:
                    #告警次数重置0
                    print("2--------------------000000000000-----------------", monitor_info.host_info.remark, info.name, info)
                    info.alarm_count = 0

    def check_alarm_count_and_send_mail(self, obj, alarm_setting_info):
        '''
            告警次数
            每五秒告警一次 执行12次 总共一分钟
            没十秒告警一次 执行12次 总共两分钟
            每三十秒告警一次 执行十次 总共五分钟
            每一分钟告警一次 执行无数次 直到问题被修复
        '''

        is_send_mail = False

        if(alarm_setting_info.alarm_count <= 12):
            if(self.check_time(5)):
                is_send_mail = True
        elif(alarm_setting_info.alarm_count > 12 and alarm_setting_info.alarm_count <= 24):
            if(self.check_time(10)):
                is_send_mail = True
        elif(alarm_setting_info.alarm_count > 24 and alarm_setting_info.alarm_count <= 34):
            if(self.check_time(30)):
                is_send_mail = True
        else:
            if(self.check_time(60)):
                is_send_mail = True
        if(is_send_mail):
            print(alarm_setting_info.alarm_count)
            alarm_setting_info.alarm_count = alarm_setting_info.alarm_count + 1
            self.send_mail(obj, alarm_setting_info)
            alarm_setting_info.last_send_alarm_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    def check_time(self, interval_time):
        return self.__times % interval_time == 0

    def send_mail(self, obj, alarm_setting_info):
        title = alarm_setting_info.title.format(obj.host_info.remark)
        #print(title, alarm_setting_info.alarm_count, alarm_setting_info.last_send_alarm_time, alarm_setting_info)
        #mail_util.send_text(title, settings.EMAIL_SEND_USERS, "")