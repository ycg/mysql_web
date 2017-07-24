# -*- coding: utf-8 -*-

#实现邮件告警，以及数据库健康检查状态的report发送
#告警，包括CPU，内存，线程数，qps和tps等等

import pymysql, threading, time
import monitor.cache, monitor.mail_util, enum, monitor.db_util, settings, monitor.mysql_status, monitor.base_class

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
        for repl_info in monitor.cache.Cache().get_all_repl_infos():
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
                    monitor.mail_util.send_text(subject, "yangcaogui.sh@superjia.com", self.get_alarm_for_repl_status_format(repl_info))

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

        for host_info in monitor.cache.Cache.get_all_host_infos():
            sql = "SELECT concat(ID, '\t', user, '\t', host, '\t', db, '\t', time, '\t', state, '\t', info, '\n') as process_data " \
                  "FROM information_schema.processlist where length(info) > 0"
            monitor.db_util.DBUtil.fetchall(sql)

@enum.unique
class LogType(enum.Enum):
    Processlist = 1
    Innodb_Status = 2
    Slave_Status = 3
    Lock_Status = 4

@enum.unique
class ExceptionType(enum.Enum):
    Repl_Delay = 1
    Repl_Fail = 2
    CPU_High = 3
    Thread = 4

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
            time.sleep(settings.LINUX_UPDATE_INTERVAL)
            monitor.cache.Cache().join_thread_pool(self.check_status)

    def check_status(self, host_info):
        self.check_os_status(host_info)
        self.check_mysql_status(host_info)
        self.check_innodb_status(host_info)
        self.check_replication_status(host_info)

    def check_os_status(self, host_info):
        os_info = monitor.cache.Cache().get_linux_info(host_info.key)
        if(os_info.cpu_system > 20 or os_info.cpu_user > 80 or os_info.cpu_idle < 50):
            self.insert_alarm_log(host_info.key, ExceptionType.CPU_High, ExceptionLevel.Serious, LogType.Processlist)
            self.insert_alarm_log(host_info.key, ExceptionType.CPU_High, ExceptionLevel.Serious, LogType.Lock_Status)
            self.insert_alarm_log(host_info.key, ExceptionType.CPU_High, ExceptionLevel.Serious, LogType.Innodb_Status)

    def check_mysql_status(self, host_info):
        mysql_status = monitor.cache.Cache().get_status_infos(host_info.key)
        if(monitor.mysql_status.threads_run_count > 10):
            self.insert_alarm_log(host_info.key, ExceptionType.Thread, ExceptionLevel.Serious, LogType.Processlist)
            self.insert_alarm_log(host_info.key, ExceptionType.Thread, ExceptionLevel.Serious, LogType.Lock_Status)

    def check_innodb_status(self, host_info):
        innodb_info = monitor.cache.Cache().get_innodb_infos(host_info.key)

    def check_replication_status(self, host_info):
        repl_info = monitor.cache.Cache().get_repl_info(host_info.key)
        if(host_info.is_master):
            return
        if(hasattr(repl_info, "master_log_pos") == False):
            return
        if(repl_info.io_status != "Yes" or repl_info.sql_status != "Yes"):
            self.insert_alarm_log(host_info.key, ExceptionType.Repl_Fail, ExceptionLevel.Serious, LogType.Slave_Status)
        if(repl_info.seconds_Behind_Master > 5):
            self.insert_alarm_log(host_info.key, ExceptionType.Repl_Delay, ExceptionLevel.Serious, LogType.Processlist)

    def insert_alarm_log(self, host_id, type, level, log_type):
        log_text = ""
        if(log_type == LogType.Lock_Status):
            log_text = monitor.mysql_status.get_log_text(monitor.mysql_status.get_innodb_lock_status(host_id))
        elif(log_type == LogType.Processlist):
            log_text = monitor.mysql_status.get_log_text(monitor.mysql_status.get_show_processlist(host_id))
        elif(log_type == LogType.Slave_Status):
            log_text = monitor.mysql_status.get_log_text(monitor.mysql_status.get_show_slave_status(host_id))
        elif(log_type == LogType.Innodb_Status):
            log_text = monitor.mysql_status.get_log_text(monitor.mysql_status.get_show_engine_innodb_status(host_id))
        if(len(log_text) <= 0):
            return
        conn, cur = monitor.db_util.DBUtil().get_conn_and_cur(settings.MySQL_Host)
        cur.execute("insert into mysql_web.mysql_exception(host_id, exception_type, level, log_type) VALUES ({0}, {1}, {2}, {3});".format(host_id, type.value, level.value, log_type.value))
        cur.execute("insert into mysql_web.mysql_exception_log(id, log_text) VALUES ({0}, '{1}');".format(cur.lastrowid, pymysql.escape_string(log_text)))
        monitor.db_util.DBUtil().close(conn, cur)

def get_execption_logs(query_parameters):
    sql = """select t1.id, t1.host_id, t3.remark, exception_type, log_type, level, t1.created_time
             from mysql_web.mysql_exception t1
             left join mysql_web.mysql_exception_log t2 on t1.id = t2.id
             left join mysql_web.host_infos t3 on t1.host_id = t3.host_id
             order by t1.id desc limit 20;"""

    result_list = []
    for row in monitor.db_util.DBUtil().fetchall(settings.MySQL_Host, sql):
        info = monitor.base_class.BaseClass(None)
        info.id = row["id"]
        info.host_id = row["host_id"]
        info.remark = row["remark"]
        info.exception_type = ((ExceptionType)(row["exception_type"])).name
        info.log_type = ((LogType)(row["log_type"])).name
        info.level = ((ExceptionLevel)(row["level"])).name
        info.created_time = row["created_time"]
        result_list.append(info)
    return result_list

def get_exception_log_text(log_id):
    sql = "select * from mysql_web.mysql_exception_log where id = {0};".format(log_id)

class AlarmParameter():
    #status

    #innodb

    #replication
    Delay_Time = 10

    #os
    MySQL_CPU = 500
    CPU_SYS = 100
    CPU_USER = 100

    pass
