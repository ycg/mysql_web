# -*- coding: utf-8 -*-

import paramiko, subprocess
from entitys import BaseClass


# 把数据库返回数据转换为对象
def get_object(row):
    info = BaseClass(None)
    for key, value in row.items():
        if (value == "None"):
            value = None
        setattr(info, key, value)
    return info


# 执行本地命令
def execute_localhost_command(command):
    result = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    result.wait()
    return result.stdin, result.stdout, result.stderr


# ssh执行远程命令
def execute_remote_command(host_info, command):
    host_client = None
    try:
        host_client = paramiko.SSHClient()
        host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        host_client.connect(host_info.host, port=host_info.ssh_port, username="root")
        stdin, stdout, stderr = host_client.exec_command(command)
        return stdin, stdout, stderr
    finally:
        if (host_client == None):
            host_client.close()

