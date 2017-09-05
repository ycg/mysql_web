# -*- coding: utf-8 -*-

import argparse, sys, os, time, commands

# 参数详解
# --user：备份机器用户名，默认为root
# --host：备份机器host
# --log-file：备份日志文件路径，如果给host赋值了，那么就是远程备份日志路径
# --recovery-dir：备份恢复目录
# 注意：恢复好之后要记得改目录的权限，如果远程恢复，必须配置免密码ssh登录

# backup.log各个分割字段含义
# {0}:{1}:{2}:{3}:{4}:{5}:{6}:{7}:{8}:{9}
# 备份模式:备份路径:备份文件名:备份日志名:备份开始时间:备份结束时间:备份日期:备份是否正常:流式备份方式:压缩方式

# 远程恢复调用命令
# python bk_recovery_xtrabackup_remote.py --host=master --log-file=/opt/backup_compress/backup_log.txt --recovery-dir=/opt/recovery_dir

# 本地调用命令
# 不加--host参数就是从本地拷贝备份文件用于恢复
# python bk_recovery_xtrabackup_remote.py --log-file=/opt/backup_compress/backup_log.txt --recovery-dir=/opt/recovery_dir


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


# 获取命令参数
def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, dest="user", help="ssh login user, default value is root", default="root")
    parser.add_argument("--host", type=str, dest="host", help="if backup is remote, please input host value", default=None)
    parser.add_argument("--log-file", type=str, dest="log_file", help="backup log file path")
    parser.add_argument("--recovery-dir", type=str, dest="recovery_dir", help="backup recovery dir")
    parser.add_argument("--use-memory", type=int, dest="use_memory", help="recovery use memory the unit is G", default=2)
    args = parser.parse_args()

    if not args.log_file or not args.recovery_dir:
        print_log("[Error]:Please input log file path or recovery dir.")
        sys.exit(1)

    # 检查是否包含xtrabackup命令
    execute_shell_command("innobackupex --help")

    # 创建恢复目录
    if (os.path.exists(args.recovery_dir) == False):
        execute_shell_command("mkdir -p {0}".format(args.recovery_dir))

    if (args.host != None):
        # 检测ssh是否正常
        execute_shell_command("ssh {0}@{1} 'df -h'".format(args.user, args.host), error_log="[Error]:Please check ssh user or host is correct.")

        # 拷贝日志文件
        args.remote = True
        log_file_name = os.path.basename(args.log_file)
        execute_shell_command("scp {0}@{1}:{2} {3}".format(args.user, args.host, args.log_file, args.recovery_dir))
        args.log_file = os.path.join(args.recovery_dir, log_file_name)
    else:
        # 检测日志文件是否存在
        args.remote = False
        execute_shell_command("cat {0}".format(args.log_file), error_log="[Error]:The log file is not exists.")

    return args


# 恢复mysql备份文件
def recovery(args):
    print_log("[Info]:start recovery mysql.")
    backup_infos = get_latest_backup_infos(args)
    copy_backup_dir_to_recovery_dir(args, backup_infos)
    uncompress(args, backup_infos)
    recovery_backup(args, backup_infos)
    print_log("[Info]:recovery mysql ok.")


# 拷贝文件
def copy_backup_dir_to_recovery_dir(args, backup_infos):
    print_log("[Info]:start copy all backup files.")
    for log_info in backup_infos:
        if (args.remote):
            # 远程拷贝文件
            status, output = commands.getstatusoutput("scp -r {0}@{1}:{2} {3}".format(args.user, args.host, log_info.backup_file_path, args.recovery_dir))
            if (int(status) > 0):
                print_log("[Error]" + output)
            else:
                print_log("[Info]:copy remote[{0}] backup file {1} to {2} ok.".format(args.host, log_info.backup_file_path, args.recovery_dir))
        else:
            # 本地拷贝文件
            execute_shell_command("cp -r {0} {1}".format(log_info.backup_file_path, args.recovery_dir))
            print_log("[Info]:copy backup file {0} to {1} ok.".format(log_info.backup_file_path, args.recovery_dir))
    print_log("[Info]:copy all backup files ok.")


# 解压缩文件
def uncompress(args, backup_infos):
    print_log("[Info]:start uncompress all backup files.")
    for log_info in backup_infos:
        dir_name = log_info.backup_file_name.split(".")[0]
        recovery_dir = os.path.join(args.recovery_dir, dir_name)
        execute_shell_command("mkdir -p {0}".format(recovery_dir))
        log_info.recovery_dir = recovery_dir
        log_info.compress_file_path = os.path.join(args.recovery_dir, log_info.backup_file_name)

        if (log_info.stream == TAR_STREAM):
            if (log_info.compress == GZIP_COMPRESS):
                execute_shell_command("tar -zxvf {0} -C {1}".format(log_info.compress_file_path, log_info.recovery_dir))
            elif (log_info.compress == PIGZ_COMPRESS):
                execute_shell_command("unpigz {0}".format(log_info.compress_file_path))
                execute_shell_command("tar -xvf {0} -C {1}".format(log_info.compress_file_path, log_info.recovery_dir))

        elif (log_info.stream == XBSTREAM_STREAM):
            if (log_info.compress == GZIP_COMPRESS):
                execute_shell_command("gunzip {0}".format(log_info.compress_file_path))
            elif (log_info.compress == PIGZ_COMPRESS):
                execute_shell_command("unpigz {0}".format(log_info.compress_file_path))
            execute_shell_command("xbstream -x < {0} -C {1}".format(os.path.join(args.recovery_dir, dir_name + ".tar"), log_info.recovery_dir))

        elif (log_info.stream == NONE_STREAM and log_info.compress == NONE_COMPRESS):
            pass

        print_log("[Info]:uncompress {0} ok, dir is {1}".format(log_info.compress_file_path, log_info.recovery_dir))

        # 删除tar包文件，释放磁盘空间
        tar_file_path = os.path.join(args.recovery_dir, dir_name + ".tar")
        if (os.path.exists(tar_file_path)):
            os.remove(tar_file_path)
            print_log("[Info]:remove {0} tar file ok.".format(tar_file_path))

    print_log("[Info]:uncompress all backup files ok.")


# 恢复备份文件
def recovery_backup(args, backup_infos):
    number = 1
    full_backup_dir = ""
    list_count = len(backup_infos)
    for info in backup_infos:
        recovery_log_file = os.path.join(args.recovery_dir, info.backup_file_name.split(".")[0] + ".log")
        if (info.mode == FULL_BACKUP):
            full_backup_dir = info.recovery_dir
            execute_xtrabackup_shell_command("innobackupex --apply-log --use-memory={0}G --redo-only {1}".format(args.use_memory, info.recovery_dir), recovery_log_file)
        else:
            if (number == list_count):
                # 最后一个增量备份恢复
                execute_xtrabackup_shell_command("innobackupex --apply-log --use-memory={0}G {1} --incremental-dir={2}".format(args.use_memory, full_backup_dir, info.recovery_dir), recovery_log_file)
            else:
                # 其余增量备份恢复
                execute_xtrabackup_shell_command("innobackupex --apply-log --redo-only --use-memory={0}G {1} --incremental-dir={2}".format(args.use_memory, full_backup_dir, info.recovery_dir), recovery_log_file)
        number += 1

        # 每次恢复都检查日志最后是否有[completed OK]标记
        return_code, output = commands.getstatusoutput("tail -n 1 {0} | grep 'completed OK'".format(recovery_log_file))
        if (int(return_code) == 0):
            print_log("[Info]:recovery [{0}] ok-√, log file path {1}".format(info.recovery_dir, recovery_log_file))
        else:
            print_log("[Error]:recovery [{0}] fail-X, log file path {1}".format(info.recovery_dir, recovery_log_file))
            sys.exit()

    # 最后要修改全量备份目录的权限
    execute_shell_command("chown -R mysql:mysql {0}".format(full_backup_dir))
    print_log("[Info]:change {0} own to mysql ok.".format(full_backup_dir))


# 获取备份日志最后一个全量+增量日志
def get_latest_backup_infos(args):
    with open(args.log_file, "r") as file:
        backup_log_infos = file.readlines()

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
def execute_shell_command(command, error_log=None):
    status, output = commands.getstatusoutput(command)
    if (int(status) > 0):
        print_log("[Error]:" + output)
        if (error_log != None):
            print_log(error_log)
        sys.exit(1)


# 执行xtrabackup的命令
def execute_xtrabackup_shell_command(command, log_file_path):
    return_code, output = commands.getstatusoutput(command)
    with open(log_file_path, "w+") as file:
        file.write(output)

    if (int(return_code) > 0):
        print_log("[Error]:recovery error" + output)
        sys.exit(1)


recovery(check_arguments())

