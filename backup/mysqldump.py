
import time, os
import traceback
from backup_base import BackupBase
from monitor import cache, common
import settings

class MySQLDump(BackupBase):
    def __init__(self, task_id):
        self.task_id = task_id

    def backup(self, backup_info):
        try:
            backup_info.start_datetime = self.get_current_time()
            backup_info.file_path = os.path.join(backup_info.backup_directory, "{0}_{1}.gz".format(backup_info.host, self.get_current_time()))
            command = self.backup_command.format(backup_info.host_info.host, backup_info.host_info.user,
                                                 backup_info.host_info.password, backup_info.host_info.port, backup_info.file_path)
            stdin, stdout, stderr = common.execute_remote_command(backup_info.backup_remote_host, command)
            backup_info.backup_status = settings.BACKUP_SUCCESS
            backup_info.backup_result = stdout.readline()
            backup_info.stop_datetime = self.get_current_time()
            self.insert_backup_log(backup_info)
        except:
            backup_info.stop_datetime = self.get_current_time()
            backup_info.backup_status = settings.BACKUP_ERROR
            self.insert_backup_log(backup_info)
            traceback.print_exc()

    def restore(self, restor_info):
        pass

    backup_command = "mysqldump -h{0} -u{1} -p{2} -P{3} " \
                     "--max-allowed-packet=1G --single-transaction --master-data=2 " \
                     "--default-character-set=utf8mb4 --triggers --routines --events -B --all-databases | gzip > {4}"

    restore_command = "mysql -h{0} -u{1} -p{2} -P{3} --default-character-set=utf8mb4 --max-allowed-packet=1G < {4}"




print(os.path.join("/opt/", "aaa.txt"))
