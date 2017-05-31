
import time, os
import backup_base, backup_util
from monitor import cache

class MySQLDump(backup_base.BackupBase):
    def backup(self):
        start_time = self.get_current_time()
        self.execute_mysqldump_backup()
        end_time = self.get_current_time()
        print(start_time, end_time)

    def execute_mysqldump_backup(self):
        host_info = cache.Cache().get_host_info(self.backup_info.backup_host_id)
        file_name = "{0}_{1}.gzip".format(host_info.remark, self.get_current_time())
        file_path = os.path.join(self.backup_info.backup_directory, file_name)
        command = "mysqldump -h{0} -u{1} -p{2} -P{3} " \
                  "--max-allowed-packet=1G --single-transaction --master-data=2 " \
                  "--default-character-set=utf8mb4 --triggers --routines --events -B --all-databases | gzip > {4}"\
                  .format(host_info.host, host_info.user, host_info.port, host_info.password, file_path)

        stdin, stdout, stderr = backup_util.local_execute_command(command)
        print(stdin, stdout, stderr)




