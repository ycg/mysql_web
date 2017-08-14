# -*- coding: utf-8 -*-

import argparse, sys, os, traceback


# xtrabackup备份恢复脚本
# 一个重要细节
# 是在原有上进行备份恢复，还是把数据拷贝到一个目录中去再进行恢复
# 可想而知还是不要在原有的基础上恢复，还是拷贝一下吧

def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssh-host", type=str, dest="ssh_host", help="ssh host")
    parser.add_argument("--ssh-password", type=str, dest="ssh_password", help="ssh password")
    parser.add_argument("--log-file", type=str, dest="log_file", help="backup log file path")
    args = parser.parse_args()

    if not args.log_file:
        print("[error]:Please input host or user or password or port.")
        sys.exit(1)
    return args


def backup_recover(args):
    log_lines = check_log_file_is_correct(args)


def check_log_file_is_correct(args):
    if (os.path.exists(args.log_file) == False):
        print("[error]:backup log file path is error.")
        sys.exit(1)

    log_lines = read_file_lines(args.log_file)
    if (log_lines == None or len(log_lines) <= 0):
        print("[error]:the file value is error.")
        sys.exit(1)

    for value in log_lines:
        tmp_list = value.split(":")
        if (len(tmp_list) != 7):
            print("[error]:the file column is error.")
            sys.exit(1)

    return log_lines


def get_backup_recover_dir_infos(log_lines):
    pass

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
