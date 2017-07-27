
import time

import settings
from monitor import db_util, common

class BackupBase():
    def __init__(self):
        pass

    def backup(self, backup_info):
        pass

    def restore(self, restor_info):
        pass

    def get_current_time(self):
        return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))

    def get_backup_info(self, backup_task_id):
        return common.get_object(db_util.DBUtil().fetchone(settings.MySQL_Host,
                                                           "select * from mysql_web.backup_task where id = {0} and is_deleted = 0;".format(backup_task_id)))

    def insert_backup_log(self, backup_info):
        sql = """insert into mysql_web.backup_log
                 (task_id, file, `size`, start_datetime, stop_datetime, status, result)
                 VALUES
                 ({0}, '{1}', {2}, '{3}', '{4}', {5}, '{6}')"""\
                 .format(backup_info.task_id, backup_info.file_name, backup_info.file_size,
                         backup_info.start_datetime, backup_info.stop_datetime, backup_info.status, backup_info.result)
        db_util.DBUtil().execute(settings.MySQL_Host, sql)

