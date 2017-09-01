# -*- coding: utf-8 -*-

import os, argparse, sys, time, datetime, subprocess, traceback

# xtrabackup远程流式备份脚本
# 两种流式备份方式：
# 1：xbstream + gzip
# 2：tar + pigz

# xbstream解压方式
# 解压：gunzip /tmp/backup.tar.gz
# 恢复到目录：xbstream -x < backup.tar -C /tmp/mysql

# tar+pigz解压方式
# 两种方式
# unpigz /tmp/backup.tar.gz
# pigz -k /tmp/backup.tar.gz

# 全量备份命令：
# 本地压缩
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | gzip > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"
# 压缩并复制到远程服务器
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | ssh root@master "gzip - > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=tar --slave-info --no-timestamp --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | ssh root@master "pigz - > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"

# 增量备份命令：
# 本地压缩
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --incremental --incremental-basedir=/data/operatingteam/ --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | gzip > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"
# 压缩并复制到远程服务器
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --incremental --incremental-basedir=/data/operatingteam/ --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | ssh root@master "gzip - > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"


# 本地压缩备份示例
# python bk_xtrabackup_remote.py --host=192.168.11.101 --user=yangcg --password='yangcaogui' --mode=1 --stream=1 --backup-dir=/opt/backup_compress

# 远程压缩备份示例
# python bk_xtrabackup_remote.py --host=192.168.11.101 --user=yangcg --password='yangcaogui' --mode=2 --stream=1 --ssh-host=master --remote-backup-dir=/opt/backup_compress

SUNDAY_INT = 6
FULL_BACKUP = 1
INCREMENT_BACKUP = 2
STREAM_TAR = 1
STREAM_XBSTREAM = 2
CHECKPOINTS_FILE_NAME = "xtrabackup_checkpoints"


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql host")
    parser.add_argument("--user", type=str, dest="user", help="mysql user")
    parser.add_argument("--password", type=str, dest="password", help="mysql password")
    parser.add_argument("--port", type=int, dest="port", help="mysql port", default=3306)
    parser.add_argument("--backup-dir", type=str, dest="backup_dir", help="backup dir", default="/opt/xtrabackup_local/")
    parser.add_argument("--mode", type=int, dest="mode", help="backup mode", default=INCREMENT_BACKUP)
    parser.add_argument("--backup-time", type=str, dest="backup_time", help="help time", default="03:30")
    parser.add_argument("--expire-days", type=int, dest="expire_days", help="expire backup days", default=14)

    parser.add_argument("--stream", type=int, dest="stream", help="--stream", default=STREAM_TAR)
    parser.add_argument("--ssh-user", type=str, dest="ssh_user", help="backup remote user", default="root")
    parser.add_argument("--ssh-host", type=str, dest="ssh_host", help="backup remote host")
    parser.add_argument("--remote-backup-dir", type=str, dest="remote_backup_dir", help="remote backup dir")

    args = parser.parse_args()
    if (not args.host or not args.user or not args.password or not args.port):
        print("[error]:Please input host or user or password or port")
        sys.exit(1)

    if (not args.ssh_host):
        # 本地压缩备份
        args.is_local_backup = True
    else:
        # 远程压缩备份
        args.is_local_backup = False

    # 检查本地和远程的备份目录是否创建
    if (args.is_local_backup):
        execute_shell_command("mkdir -p {0}".format(args.backup_dir))
    else:
        execute_shell_command("ssh {0}@{1} \"mkdir -p {2}\"".format(args.ssh_user, args.ssh_host, args.remote_backup_dir))

    if (args.stream == STREAM_TAR):
        args.stream_value = "tar"
        args.compress_value = "pigz"
    elif (args.stream == STREAM_XBSTREAM):
        args.stream_value = "xbstream"
        args.compress_value = "gzip"
    return args


# 备份
def backup(args):
    print("start backup.")
    if (args.mode == FULL_BACKUP):
        full_backup(args)
    else:
        day_of_week = datetime.datetime.now().weekday()
        if (day_of_week == SUNDAY_INT):
            full_backup(args)
        else:
            if (os.path.exists(os.path.join(args.backup_dir, CHECKPOINTS_FILE_NAME)) == False):
                full_backup(args)
            else:
                increment_backup(args)
    print("backup complete ok.")


# 全量备份
def full_backup(args):
    start_backup_time = get_current_time()
    log_name = "full_{0}.log".format(start_backup_time)
    file_name = "full_{0}.tar.gz".format(start_backup_time)
    if (args.is_local_backup):
        command = full_backup_to_local(args, file_name)
    else:
        command = full_backup_to_remote(args, file_name)
    execute_shell_command(command)
    stop_backup_time = get_current_time()


# 本地压缩备份
def full_backup_to_local(args, file_name):
    return "innobackupex --host={0} --user={1} --password='{2}' --port={3} --stream={4} --slave-info --no-timestamp --extra-lsndir={5} {5} | {6} > {7}" \
        .format(args.host,
                args.user,
                args.password,
                args.port,
                args.stream_value,
                args.backup_dir,
                args.compress_value,
                os.path.join(args.backup_dir, file_name))


# 远程流式备份
def full_backup_to_remote(args, file_name):
    return "innobackupex --host={0} --user={1} --password='{2}' --port={3} --stream={4} --slave-info --no-timestamp --extra-lsndir={5} {5} | ssh {6}@{7} \"{8} - > {9}\"" \
        .format(args.host,
                args.user,
                args.password,
                args.port,
                args.stream_value,
                args.backup_dir,
                args.ssh_user,
                args.ssh_host,
                args.compress_value,
                os.path.join(args.remote_backup_dir, file_name))


# 增量备份
def increment_backup(args):
    # 增量备份只支持xbstream的备份方式
    start_backup_time = get_current_time()
    log_name = "increment_{0}.log".format(start_backup_time)
    file_name = "increment_{0}.tar.gz".format(start_backup_time)
    if (args.is_local_backup):
        command = increment_backup_to_local(args, file_name)
    else:
        command = increment_backup_to_remote(args, file_name)
    execute_shell_command(command)
    stop_backup_time = get_current_time()


# 本地增量备份
def increment_backup_to_local(args, file_name):
    return "innobackupex --host={0} --user={1} --password='{2}' --port={3} --stream=xbstream --slave-info --no-timestamp --incremental --incremental-basedir={4} --extra-lsndir={4} {4} | gzip > {5}" \
        .format(args.host,
                args.user,
                args.password,
                args.port,
                args.backup_dir,
                os.path.join(args.backup_dir, file_name))


# 远程增量备份
def increment_backup_to_remote(args, file_name):
    return "innobackupex --host={0} --user={1} --password='{2}' --port={3} --stream=xbstream --slave-info --no-timestamp --incremental --incremental-basedir={4} --extra-lsndir={4} {4} | ssh {5}@{6} \"gzip - > {7}\"" \
        .format(args.host,
                args.user,
                args.password,
                args.port,
                args.backup_dir,
                args.ssh_user,
                args.ssh_host,
                os.path.join(args.remote_backup_dir, file_name))


def get_current_time():
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))


def execute_shell_command(command):
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.wait()
    print("--------------------------")
    if (result.stdout != None):
        print(result.stdout.readlines())
    if (result.stderr != None):
        print(result.stderr.readlines())


backup(check_arguments())
