# -*- coding: utf-8 -*-

import os, argparse, sys, time, datetime, subprocess

# python bk_xtrabackup.py --host=192.168.1.101 --user=yangcg --password=yangcaogui --mode=1 --backup-dir=/opt/my_backup
# 备份周期是按照一个星期来的，星期天全量备份，其余增量备份
# 参数详解：
# --host
# --user
# --password
# --port
# --backup-dir:备份目录，需要指定一个不存在的目录才行
# --mode：备份模式，1代表全量，2代表增量
# --backup-time：定时备份时间
# --expire-days：备份文件过期时间

FULL_BACKUP = 1
INCREMENT_BACKUP = 2
WRITE_FILE_COVER = "w"
WRITE_FILE_APPEND = "a"


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql host")
    parser.add_argument("--user", type=str, dest="user", help="mysql user")
    parser.add_argument("--password", type=str, dest="password", help="mysql password")
    parser.add_argument("--port", type=int, dest="port", help="mysql port", default=3306)
    parser.add_argument("--backup-dir", type=str, dest="backup_dir", help="backup dir")
    parser.add_argument("--mode", type=int, dest="mode", help="backup mode", default=INCREMENT_BACKUP)
    parser.add_argument("--backup-time", type=str, dest="backup_time", help="help time", default="03:30")
    parser.add_argument("--ssh-host", type=str, dest="ssh_host", help="backup scp remote ip")
    parser.add_argument("--expire-days", type=int, dest="expire_days", help="expire backup days", default=14)
    args = parser.parse_args()

    if not args.host or not args.user or not args.password or not args.port:
        print("[error]:Please input host or user or password or port.")
        sys.exit(1)

    '''if not args.backup_dir:
        print("[error]:Please input backup directory.")
        sys.exit(1)
    else:
        if (os.path.exists(args.backup_dir)):
            print("[error]:Backup directory exists.")
            sys.exit(1)
        else:
            os.mkdir(args.backup_dir)'''

    if not args.backup_dir:
        print("[error]:Please input backup directory.")
        sys.exit(1)

    if (os.path.exists(args.backup_dir) == False):
        os.mkdir(args.backup_dir)

    if (args.mode != FULL_BACKUP and args.mode != INCREMENT_BACKUP):
        print("[error]:Backup mode value is 1 or 2.")
        sys.exit(1)

    args.backup_log_file_path = os.path.join(args.backup_dir, "backup.log")
    return args


def backup(args):
    if (args.mode == FULL_BACKUP):
        full_backup(args)
    else:
        day_of_week = datetime.datetime.now().weekday()
        if (day_of_week == 6):
            full_backup(args)
        else:
            increment_backup(args)
    remove_expire_backup_directory(args)
    print("backup complete ok.")


def get_backup_date():
    return time.strftime('%Y-%m-%d', time.localtime(time.time()))


def get_current_time():
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))


def full_backup(args):
    start_backup_time = get_current_time()
    full_backup_dir = os.path.join(args.backup_dir, "full_{0}".format(start_backup_time))
    if (os.path.exists(full_backup_dir) == False):
        os.mkdir(full_backup_dir)
    full_backup_log_path = os.path.join(args.backup_dir, "full_{0}.log".format(start_backup_time))
    command = "innobackupex --host={0} --user={1} --password='{2}' --port={3} --no-timestamp {4} 2>> {5}".format(args.host, args.user, args.password, args.port, full_backup_dir, full_backup_log_path)
    result = subprocess.Popen(command, shell=True)
    result.wait()
    stop_backup_time = get_current_time()
    log_value = "{0}:{1}:{2}:{3}:{4}:{5}:{6}\n" \
                .format(FULL_BACKUP, full_backup_dir, full_backup_log_path, start_backup_time, stop_backup_time, get_backup_date, check_backup_is_correct(full_backup_log_path))
    write_log_file(args.backup_log_file_path, log_value, WRITE_FILE_APPEND)


def increment_backup(args):
    last_line = read_backup_log_last_line(args.backup_log_file_path)
    if (last_line == None):
        full_backup(args)

    last_line_values = last_line.split(":")
    if (len(last_line_values) > 0 and len(last_line_values) < 10):
        last_backup_dir = last_line_values[1]
        start_backup_time = get_current_time()
        increment_backup_dir = os.path.join(args.backup_dir, "increment_{0}".format(start_backup_time))
        if (os.path.exists(increment_backup_dir) == False):
            os.mkdir(increment_backup_dir)
        increment_backup_log_path = os.path.join(args.backup_dir, "increment_{0}.log".format(start_backup_time))
        command = "innobackupex --host={0} --user={1} --password='{2}' --port={3} --no-timestamp --incremental --incremental-basedir={4} {5} 2>> {6}" \
            .format(args.host, args.user, args.password, args.port, last_backup_dir, increment_backup_dir, increment_backup_log_path)
        result = subprocess.Popen(command, shell=True)
        result.wait()
        stop_backup_time = get_current_time()
        log_value = "{0}:{1}:{2}:{3}:{4}:{5}:{6}\n" \
                    .format(FULL_BACKUP, increment_backup_dir, increment_backup_log_path, start_backup_time, stop_backup_time, get_backup_date(), check_backup_is_correct(increment_backup_log_path))
        write_log_file(args.backup_log_file_path, log_value, WRITE_FILE_APPEND)
    else:
        full_backup(args)


def read_backup_log_last_line(file_path):
    file = None
    try:
        file = open(file_path, "r")
        log_lines = file.readlines()
        if (len(log_lines) > 0):
            return log_lines[-1]
        else:
            return None
    except:
        return None
    finally:
        if (file != None):
            file.close()


def remove_expire_backup_directory(args):
    current_time = datetime.datetime.now()
    for path in os.listdir(args.backup_dir):
        full_path = os.path.join(args.backup_dir, path)
        dir_or_file_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
        if ((current_time - dir_or_file_time).days > args.expire_days):
            if (os.path.isdir(full_path)):
                os.rmdir(full_path)
            elif (os.path.isfile(full_path)):
                os.remove(full_path)


def check_backup_is_correct(xtrabackup_log_path):
    file = None
    try:
        file = open(xtrabackup_log_path)
        log_values = file.readlines()
        last_line = log_values[-1]
        if (last_line.find("completed OK") > 0):
            return 1
        else:
            return 0
    except:
        return 0
    finally:
        if (file != None):
            file.close()


def write_log_file(file_path, log_value, write_type):
    file = None
    try:
        file = open(file_path, write_type)
        if (isinstance(log_value, list)):
            file.writelines(log_value)
        else:
            file.write(log_value)
    finally:
        if (file != None):
            file.close()


'''args = check_arguments()
while (True):
    current_time = time.strftime('%H:%M', time.localtime(time.time()))
    if (current_time == args.backup_time):
        backup(args)
    time.sleep(10)'''

backup(check_arguments())
# write_log_file("C:\\Users\\Administrator\\Desktop\\123.txt", "aaa\n", WRITE_FILE_APPEND)
# write_log_file("C:\\Users\\Administrator\\Desktop\\123.txt", "bbb\n", WRITE_FILE_APPEND)
