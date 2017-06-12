# -*- coding: utf-8 -*-

import argparse, paramiko, os

#自动安装mha前提是上传mha安装包

error = "error"
output = "output"
dowload_path = "/tmp/"

def check_arguments():
    global dowload_path
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="linux host")
    parser.add_argument("--package", type=str, dest="package", help="mha package path")
    args = parser.parse_args()
    return args

def install_mha_package(args):
    yum_command = "yum localinstall -y {0}mha4mysql-*.rpm".format(dowload_path)
    rpm_command = "rpm -ivh {0}epel-release-latest-7.noarch.rpm".format(dowload_path)
    wget_command = "wget http://mirrors.aliyun.com/epel/epel-release-latest-7.noarch.rpm -P /tmp/"

    if(not args.host):
        os.system("cp {0} {1}".format(args.package, dowload_path))
        os.system(wget_command)
        os.system(rpm_command)
        os.system(yum_command)
    else:
        os.system("scp {0} {1}:/tmp/".format(args.package, args.host))

        host_client = paramiko.SSHClient()
        host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        host_client.connect(args.host, port=22, username="root")

        execute_remote_shell(host_client, wget_command)
        execute_remote_shell(host_client, rpm_command)
        execute_remote_shell(host_client, yum_command)
        host_client.close()

def execute_remote_shell(host_client, shell):
    result = {}
    try:
        stdin, stdout, stderr = host_client.exec_command(shell)
        result[error] = stderr.readlines()
        result[output] = stdout.readlines()
        if(len(result[error]) > 0):
            print(result[error][0].replace("\n", ""))
        else:
            print(result[output][0].replace("\n", ""))
    except:
        host_client.close()
    return result

if(__name__ == "__main__"):
    args = check_arguments()
    install_mha_package(args)
    print("install {0} ok.".format(args.package))

