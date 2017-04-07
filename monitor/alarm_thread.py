# -*- coding: utf-8 -*-

#实现邮件告警，以及数据库健康检查状态的report发送
#告警，包括CPU，内存，线程数，qps和tps等等

import threading, time, cache, mail_util, enum, db_util, settings, mysql_status, base_class

class AlarmEnum(enum.Enum):
    ReplStatus = 0
    ReplDelay = 1
    CPU = 2
    Memory = 3
    Disk = 4

class AlarmThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while(True):
            time.sleep(settings.ALARM_INTERVAL)
            self.alarm_for_replication()

    def alarm_for_replication(self):
        for repl_info in cache.Cache().get_all_repl_infos():
            if(hasattr(repl_info, "io_status") == True):
                error_flag = False
                subject = "MySQL-" + repl_info.host_info.remark
                if(repl_info.io_status == "No" or repl_info.sql_status == "No"):
                    error_flag = True
                    subject = subject + "复制异常"
                elif(repl_info.delay_pos_count > 20000):
                    error_flag = True
                    subject = subject + "复制延迟"
                if(error_flag == True):
                    mail_util.send_text(subject, "yangcaogui.sh@superjia.com", self.get_alarm_for_repl_status_format(repl_info))

    def alarm_for_mysql_status(self):
        pass

    def get_alarm_for_repl_status_format(self, repl_info):
        return "IO Status: {0}\nYes Status: {1}\nDelay Pos: {2}\nError Msg: {3}"\
               .format(repl_info.io_status, repl_info.sql_status, repl_info.delay_pos_count, repl_info.error_message)

    def collect_mysql_status(self):
        #当程序出现告警的时候，手机mysql系统信息
        #1.show full processlist
        #2.show engine innodb status
        #3.show slave status
        #4.获取error的数据信息

        for host_info in cache.Cache.get_all_host_infos():
            sql = "SELECT concat(ID, '\t', user, '\t', host, '\t', db, '\t', time, '\t', state, '\t', info, '\n') as process_data " \
                  "FROM information_schema.processlist where length(info) > 0"
            db_util.DBUtil.fetchall(sql)

@enum.unique
class ExceptionType(enum.Enum):
    Repl_Delay = 1
    Repl_Fail = 2

@enum.unique
class ExceptionLevel(enum.Enum):
    Prompt = 1
    General = 2
    Serious = 3
    Fatal = 4

class AlarmLog(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        while(True):
            time.sleep(settings.UPDATE_INTERVAL)
            cache.Cache().join_thread_pool(self.check_status)

    def check_status(self, host_info):
        self.check_os_status(cache.Cache().get_linux_info(host_info.key))
        self.check_mysql_status(cache.Cache().get_status_infos(host_info.key))
        self.check_innodb_status(cache.Cache().get_innodb_infos(host_info.key))
        self.check_replication_status(cache.Cache().get_repl_info(host_info.key))

    def check_os_status(self, os_info):
        pass

    def check_mysql_status(self, status_info):
        pass

    def check_innodb_status(self, innodb_info):
        pass

    def check_replication_status(self, repl_info):
        pass
        '''if(repl_info.io_status != "Yes" or repl_info.sql_status != "Yes"):
            log_text = ""
            result = mysql_status.get_show_slave_status(repl_info.host_info.key)
            for key, value in result.items():
                log_text = key + ":" + value + "\n"
            self.insert_alarm_log(repl_info.host_info.key, ExceptionType.Repl_Fail.value, ExceptionLevel.Serious.value, log_text)'''

    def insert_alarm_log(self, host_id, type, level, log_text):
        conn, cur = db_util.DBUtil().get_conn_and_cur(settings.MySQL_Host)
        cur.execute("insert into mysql_web.mysql_exception(host_id, exception_type, level) VALUES ({0}, {1}, {2});".format(host_id, type, level))
        cur.execute("insert into mysql_web.mysql_exception_log(id, log_text) VALUES ({0}, '{1}');".format(cur.lastrowid, log_text))
        db_util.DBUtil().close(conn, cur)