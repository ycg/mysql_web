# -*- coding: utf-8 -*-

import paramiko, subprocess, traceback, json, datetime, time
from entitys import BaseClass
import db_util


def convert_object_json(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, time.date):
        return obj.strftime('%Y-%m-%d')
    else:
        return obj.__dict__


# 把数据库返回数据转换为对象
def get_object(row):
    info = BaseClass(None)
    for key, value in row.items():
        if (value == "None"):
            value = None
        setattr(info, key.lower(), value)
    return info


# 把数据库返回数据转换为对象集合
def get_object_list(rows):
    info_list = []
    for row in rows:
        info = BaseClass(None)
        for key, value in row.items():
            if (value == "None"):
                value = None
            setattr(info, key.lower(), value)
        info_list.append(info)
    return info_list


# 转换对象为json数据
def convert_obj_to_json_str(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)
    #return json.dumps(obj, default=convert_obj_to_json_str(xxx))
    #return json.dumps(obj, default=lambda o: o.strftime("%Y-%m-%d %H:%M:%S") if (isinstance(o, datetime)) else o.__dict__)


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
        host_client.connect(host_info.host, port=host_info.ssh_port, username=host_info.ssh_user, password=host_info.ssh_password, timeout=1)
        stdin, stdout, stderr = host_client.exec_command(command)
        return stdin, stdout, stderr
    finally:
        if (host_client == None):
            host_client.close()


# 测试SSH连接是否OK
def test_ssh_connection_is_ok(obj):
    try:
        host_info = BaseClass(None)
        host_info.host = obj.host_ip
        host_info.ssh_port = obj.host_ssh_port
        host_info.ssh_user = obj.host_ssh_user
        host_info.ssh_password = obj.host_ssh_password if(len(obj.host_ssh_password) > 0) else None
        execute_remote_command(host_info, "df -h")
    except:
        traceback.print_exc()
        return False
    return True


# 测试MySQL连接是否OK
def test_mysql_connection_is_ok(obj):
    try:
        db_util.DBUtil().execute_sql(obj.host_ip, obj.host_port, obj.host_user, obj.host_password, "select 1;")
    except Exception:
        traceback.print_exc()
        return False
    return True


