# -*- coding: utf-8 -*-

import argparse, sys, os, traceback, subprocess, time, commands

# backup.log各个分割字段含义
# {0}:{1}:{2}:{3}:{4}:{5}:{6}:{7}:{8}:{9}
# 备份模式:备份路径:备份文件名:备份日志名:备份开始时间:备份结束时间:备份日期:备份是否正常:流式备份方式:压缩方式

FULL_BACKUP = 1
INCREMENT_BACKUP = 2

NONE_COMPRESS = 0
GZIP_COMPRESS = 1
PIGZ_COMPRESS = 2

NONE_STREAM = 0
TAR_STREAM = 1
XBSTREAM_STREAM = 2


class BackupInfo():
    def __init__(self):
        pass


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, dest="user", help="user", default="root")
    parser.add_argument("--host", type=str, dest="host", help="host", default=None)
    parser.add_argument("--password", type=str, dest="password", help="password", default=None)

    parser.add_argument("--remote", type=bool, dest="remote", help="host is remote", default=False)
    parser.add_argument("--log-file", type=str, dest="log_file", help="backup log file path")
    parser.add_argument("--recovery-dir", type=str, dest="recovery_dir", help="backup recovery dir")
    args = parser.parse_args()

    if not args.log_file or not args.recovery_dir:
        print("[error]:Please input log file path.")
        sys.exit(1)
    return args


def recovery(args):
    backup_infos = get_latest_backup_infos(args)
    copy_backup_dir_to_recovery_dir(args, backup_infos)
    uncompress(args, backup_infos)
    recovery_backup(args, backup_infos)


# 拷贝文件
def copy_backup_dir_to_recovery_dir(args, backup_infos):
    for log_info in backup_infos:
        if (args.remote):
            # 远程拷贝文件
            execute_shell_command("scp -r {0} {1}@{2}:{3}".format(log_info.backup_file_path, args.user, args.host, args.recovery_dir))
            print_log("[Info]:copy remote[{0}] backup file {1} to {2} ok.".format(args.host, log_info.backup_file_path, args.recovery_dir))
        else:
            # 本地拷贝文件
            execute_shell_command("cp -r {0} {1}".format(log_info.backup_file_path, args.recovery_dir))
            print_log("[Info]:copy backup file {0} to {1} ok.".format(log_info.backup_file_path, args.recovery_dir))
    print_log("[Info]:copy all backup files ok.")


# 解压缩文件
def uncompress(args, backup_infos):
    for log_info in backup_infos:
        dir_name = log_info.backup_file_name.split(".")[0]
        umcompress_dir = os.path.join(args.recovery_dir, dir_name)
        execute_shell_command("mkdir -p {0}".format(umcompress_dir))
        log_info.umcompress_dir = umcompress_dir

        if (log_info.stream == TAR_STREAM):
            if (log_info.compress == GZIP_COMPRESS):
                execute_shell_command("tar -zxvf {0} -C {1}".format(log_info.backup_file_path, umcompress_dir))
            elif (log_info.compress == PIGZ_COMPRESS):
                execute_shell_command("unpigz {0}".format(log_info.backup_file_path))
                execute_shell_command("tar -xvf {0} -C {1}".format(log_info.backup_file_path, umcompress_dir))

        elif (log_info.stream == XBSTREAM_STREAM):
            if (log_info.compress == GZIP_COMPRESS):
                execute_shell_command("gunzip {0}".format(log_info.backup_file_path))
            elif (log_info.compress == PIGZ_COMPRESS):
                execute_shell_command("unpigz {0}".format(log_info.backup_file_path))
            execute_shell_command("xbstream -x < {0} -C {1}".format(os.path.join(args.recovery_dir, dir_name + ".tar"), umcompress_dir))

        elif (log_info.stream == NONE_STREAM and log_info.compress == NONE_COMPRESS):
            pass

        print_log("[Info]:uncompress {0} ok, dir is {1}".format(log_info.backup_file_path, umcompress_dir))


# 恢复备份文件
def recovery_backup(args, backup_infos):
    number = 1
    full_backup_dir = ""
    list_count = len(backup_infos)
    for info in backup_infos:
        recovery_log_file = os.path.join(args.recovery_dir, info.backup_file_name.split(".")[0] + ".log")
        if (info.mode == INCREMENT_BACKUP):
            full_backup_dir = info.umcompress_dir
            execute_xtrabackup_shell_command("innobackupex --apply-log --redo-only {0}".format(info.umcompress_dir), recovery_log_file)
        else:
            if (number == list_count):
                # 最后一个增量备份恢复
                execute_xtrabackup_shell_command("innobackupex --apply-log {0} --incremental-dir={1}".format(full_backup_dir, info.umcompress_dir), recovery_log_file)
            else:
                # 其余增量备份恢复
                execute_xtrabackup_shell_command("innobackupex --apply-log --redo-only {0} --incremental-dir={1}".format(full_backup_dir, info.umcompress_dir), recovery_log_file)
        number += 1


# 获取备份日志最后一个全量+增量日志
def get_latest_backup_infos(args):
    file = None
    backup_log_infos = []
    try:
        file = open(args.log_file, "r")
        backup_log_infos = file.readlines()
    except:
        traceback.print_exc()
    finally:
        if (file != None):
            file.close()

    if (len(backup_log_infos) <= 0):
        print_log("[Error]:the backup log file is empty.")
        sys.exit()

    # backup.log各个分割字段含义
    # {0}:{1}:{2}:{3}:{4}:{5}:{6}:{7}:{8}:{9}
    # 备份模式:备份路径:备份文件名:备份日志名:备份开始时间:备份结束时间:备份日期:备份是否正常:流式备份方式:压缩方式
    recovery_log_infos = []
    line_count = len(backup_log_infos)
    for i in range(line_count - 1, 0, -1):
        log_info = BackupInfo()
        values = backup_log_infos[i].split(":")
        log_info.index = i
        log_info.mode = int(values[0])
        log_info.backup_dir = values[1]
        log_info.backup_file_name = values[2]
        log_info.backup_log_name = values[3]
        log_info.backup_file_path = os.path.join(log_info.backup_dir, values[2])
        log_info.backup_log_path = os.path.join(log_info.backup_dir, values[3])
        log_info.start_time = values[4]
        log_info.stop_time = values[5]
        log_info.backup_date = values[6]
        log_info.backup_is_ok = bool(values[7])
        log_info.stream = int(values[8])
        log_info.compress = int(values[9])
        recovery_log_infos.append(log_info)
        if (log_info.mode == FULL_BACKUP):
            break
    if (len(recovery_log_infos) > 0):
        # 按index属性升序排列，把全量备份的放在第一位
        return sorted(recovery_log_infos, cmp=lambda x, y: cmp(x.index, y.index), reverse=False)
    return recovery_log_infos


# 打印日志
def print_log(log_value):
    print("{0} {1}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), log_value))


# 执行linux命令
def execute_shell_command(command):
    result = subprocess.Popen(command, shell=True)
    result.wait()


# 执行xtrabackup的命令
def execute_xtrabackup_shell_command(command, log_file_path):
    status, output = commands.getstatusoutput(command)
    file = None
    try:
        file = open(log_file_path, "w+")
        file.write(output)
    finally:
        if (file != None):
            file.close()

    status, output = commands.getstatusoutput("tail -n 1 {0} | grep 'completed OK'".format(log_file_path))
    if (int(status) >= 0):
        print_log("[Info]:recovery ok-√, log file path {0}".format(log_file_path))
    else:
        print_log("[Error]:recovery fail-X, log file path {0}".format(log_file_path))
        sys.exit()


recovery(check_arguments())
