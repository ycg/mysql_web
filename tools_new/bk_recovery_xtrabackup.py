# -*- coding: utf-8 -*-

import argparse, sys, os, traceback, subprocess

# xtrabackup备份恢复脚本
# 一个重要细节
# 是在原有上进行备份恢复，还是把数据拷贝到一个目录中去再进行恢复
# 可想而知还是不要在原有的基础上恢复，还是拷贝一下吧

# backup.log各个分割字段含义
# {0}:{1}:{2}:{3}:{4}:{5}:{6}:{7}
# 备份模式:备份路径:备份日志路径:备份开始时间:备份结束时间:备份日期:备份是否正常:备份目录名称

# 本地恢复调用：
# python bk_recovery_xtrabackup.py --log-file=/backup_test/bk_dir/backup.log --recovery-dir=/backup_test/recovery_dir/

# 远程恢复调用：
# python bk_recovery_xtrabackup.py --ssh-host=192.168.11.101 --log-file=/backup_test/bk_dir/backup.log --recovery-dir=/backup_test/recovery_dir/


BACKUP_OK = "1"
FULL_BACKUP = "1"
INCREMENT_BACKUP = "2"


class BackupInfo():
    def __init__(self):
        pass


# 获取调用脚本参数
def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssh-user", type=str, dest="ssh_user", help="ssh user", default="root")
    parser.add_argument("--ssh-host", type=str, dest="ssh_host", help="ssh host", default=None)
    parser.add_argument("--ssh-password", type=str, dest="ssh_password", help="ssh password", default=None)
    parser.add_argument("--log-file", type=str, dest="log_file", help="backup log file path")
    parser.add_argument("--recovery-dir", type=str, dest="recovery_dir", help="backup recovery dir")
    args = parser.parse_args()

    if not args.log_file or not args.recovery_dir:
        print("[error]:Please input log file path.")
        sys.exit(1)
    return args


# 备份恢复总目录
def backup_recover(args):
    log_lines = check_log_file_is_correct(args)
    backup_infos = get_backup_recover_dir_infos(args, log_lines)
    copy_backup_dir_to_recovery_dir(args, backup_infos)
    xtrbackup_recovery(backup_infos)


# 监测备份日志数据是否正常
def check_log_file_is_correct(args):
    if (args.ssh_host != None):
        log_file_save_path = "/tmp/"
        execute_linux_command("scp root@{0}:{1} {2}".format(args.ssh_host, args.log_file, log_file_save_path))
        args.log_file = log_file_save_path

    if (os.path.exists(args.log_file) == False):
        print("[error]:backup log file path is error.")
        sys.exit(1)

    log_lines = read_file_lines(args.log_file)
    if (log_lines == None or len(log_lines) <= 0):
        print("[error]:the file value is error.")
        sys.exit(1)

    for value in log_lines:
        tmp_list = value.split(":")
        if (len(tmp_list) != 8):
            # 检测backup log文件字段的个数是否一致
            print("[error]:the backup log file column is error.")
            sys.exit(1)

    return log_lines


# 根据备份日志获取备份目录地址
def get_backup_recover_dir_infos(args, log_lines):
    backup_infos = []
    length = len(log_lines)
    for index in range(length):
        values = log_lines[length - index - 1].replace("\n", "").split(":")
        # 检测备份是否正常
        if (values[6] == BACKUP_OK):
            info = BackupInfo()
            info.key = index
            info.mode = values[0]
            info.backup_dir = values[1]
            info.recovery_dir = os.path.join(args.recovery_dir, values[7])
            backup_infos.append(info)
        # 检测当前备份是否是全量备份
        if (values[0] == FULL_BACKUP):
            break
    return backup_infos


# 拷贝备份目录到指定的路径
def copy_backup_dir_to_recovery_dir(args, backup_infos):
    for info in backup_infos:
        if (args.ssh_host != None):
            # 将远程的备份文件拷贝到本地
            print("[info]:remote {0} copy {0} to {1} start.".format(args.ssh_host, info.backup_dir, args.recovery_dir))
            command = "scp -r root@{0}:{1} {2}".format(args.ssh_host, info.backup_dir, args.recovery_dir)
            result = subprocess.Popen(command, shell=True)
            result.wait()
            print("[info]:remote {0} copy {0} to {1} ok.".format(args.ssh_host, info.backup_dir, args.recovery_dir))
        else:
            # 本地拷贝文件
            print("[info]:copy {0} to {1} start.".format(info.backup_dir, args.recovery_dir))
            command = "cp -r {0} {1}".format(info.backup_dir, args.recovery_dir)
            result = subprocess.Popen(command, shell=True)
            result.wait()
            print("[info]:copy {0} to {1} ok.".format(info.backup_dir, args.recovery_dir))


# 使用xtrabackup进行恢复
def xtrbackup_recovery(backup_infos):
    if (len(backup_infos) > 0):
        if (len(backup_infos) == 1):
            # 只有一个备份而且是全量备份
            execute_linux_command("innobackupex --apply-log --redo-only {0}".format(backup_infos[0].recovery_dir))
        else:
            # backup_infos字段的key是从小到大排序的，也就是key最大值为全量备份，所以先倒序排列
            number = 1
            full_backup_dir = ""
            sort_list = sorted(backup_infos, cmp=lambda x, y: cmp(x.key, y.key), reverse=True)
            for info in sort_list:
                if (number == 1):
                    # 全量备份恢复
                    full_backup_dir = info.recovery_dir
                    execute_linux_command("innobackupex --apply-log --redo-only {0}".format(info.recovery_dir))
                    print("[info]:recovery full backup {0} ok.".format(info.recovery_dir))
                elif (number == len(sort_list)):
                    # 最后一个增量备份恢复
                    execute_linux_command("innobackupex --apply-log {0} --incremental-dir={1}".format(full_backup_dir, info.recovery_dir))
                    print("[info]:recovery latest increment backup {0} ok.".format(info.recovery_dir))
                else:
                    # 其余增量备份恢复
                    execute_linux_command("innobackupex --apply-log --redo-only {0} --incremental-dir={1}".format(full_backup_dir, info.recovery_dir))
                    print("[info]:recovery increment backup {0} ok.".format(info.recovery_dir))
                number += 1

        print("[info]:xtrabackup recovery ok.")
    else:
        print("[error]:backup log infos is empty.")


# 执行linux命令
def execute_linux_command(command):
    result = subprocess.Popen(command, shell=True)
    result.wait()
    return result


# 获取文件所有的行数据
def read_file_lines(file_path):
    file = None
    try:
        file = open(file_path, "r")
        return file.readlines()
    except:
        traceback.print_exc()
        return None
    finally:
        if (file != None):
            file.close()


if (__name__ == "__main__"):
    backup_recover(check_arguments())
