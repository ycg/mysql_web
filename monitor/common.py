# -*- coding: utf-8 -*-

import paramiko, subprocess


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


# 执行本地命令
def execute_localhost_command(command):
    result = subprocess.Popen(command, shell=True)
    result.wait()
    return result.stdin, result.stdout, result.stderr
