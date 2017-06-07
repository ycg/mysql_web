# -*- coding: utf-8 -*-

import os, paramiko, argparse, sys, time

#首先安装依赖包 - pip install paramiko

#1.生成配置文件
    #获取buffer pool的大小
    #创建各种目录 - mkdir
#2.从服务器获取安装包
    #scp /opt/mysql.5.6.tar.gz root@192.168.11.129:/opt/
    #mkdir /usr/local/mysql
    #tar -zxvf /opt/mysql.5.6.tar.gz --strip-components=1 -C /usr/local/mysql
#3.创建用户
    #groupadd mysql
    #useradd mysql -g mysql
    #chmod -R mysql:mysql /mysql_data/
    #chmod -R mysql:mysql /mysql_binlog/
#3.自动初始化数据
    #5.6和5.7的方式不一样
    #5.6
        #yum install -y perl-Module-Install.noarch
        #/usr/local/mysql/script/mysql_install_db --defaults-file=/etc/my.cnf > /tmp/mysql_install.log
    #5.7
        #/usr/local/mysql/bin/mysqld --defaults-file=/etc/my.cnf --initialize-insecure > /tmp/mysql_install.log
#4.自动启动
    #/usr/local/mysql/bin/mysqld --defaults-file=/etc/my.cnf &

#5.脚本示例
#python mysql_auto_install.py --host=192.168.11.129 --version=5.6 --package=/opt/mysql-5.6.tar.gz
#--host：需要安装的主机ip
#--port：指定mysql端口，多实例安装需要用到
#--version：安装包的版本
#--package：安装包路径
#--data-dir：指定数据存储目录
#--binlog-dir：指定binlog存储目录
#--gtid：是否使用gtid模式
#--semi-sync：是否使用半同步模式来保证数据的一致性

error = "error"
output = "output"
mysql_5_6 = "5.6"
mysql_5_7 = "5.7"
data_dir = "/mysql/data"
binlog_dir = "/mysql/binlog"
base_dir = "/usr/local/mysql"

def check_arguments():
    global data_dir, base_dir, binlog_dir
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql host")
    parser.add_argument("--port", type=str, dest="port", help="mysql port", default="3306")
    parser.add_argument("--version", type=str, dest="version", help="mysql version", default=mysql_5_6)
    parser.add_argument("--data-dir", type=str, dest="data_dir", help="mysql data dir", default=data_dir)
    parser.add_argument("--base-dir", type=str, dest="base_dir", help="mysql base dir", default=base_dir)
    parser.add_argument("--binlog-dir", type=str, dest="binlog_dir", help="mysql bin log dir", default=binlog_dir)
    parser.add_argument("--package", type=str, dest="package", help="mysql install package path")
    parser.add_argument("--gtid", type=int, dest="gtid", help="binlog use gtid mode", default=0)
    parser.add_argument("--semi-sync", type=int, dest="semi_sync", help="repl semi sync mode", default=0)
    args = parser.parse_args()

    if not args.host or not args.version:
        print("[error]:Please input remote host ip or hostname.")
        sys.exit(1)
    if(args.version != "5.6" and args.version != "5.7"):
        print("[error]:Please input mysql package version number [--version=5.6 | --version=5.7].")
        sys.exit(1)
    if not args.package:
        args.package = "/opt/mysql.tar.gz"
    data_dir = args.data_dir
    base_dir = args.base_dir
    binlog_dir = args.binlog_dir
    args.package_name = os.path.basename(args.package)
    return args

def mysql_install(args):
    #创建ssh对象
    host_client = paramiko.SSHClient()
    host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host_client.connect(args.host, port=22, username="root")

    #创建目录
    print("\n--------------------------1.rm dir and create mysql data dir-------------------")
    kill_mysql_process(host_client)
    execute_remote_shell(host_client, "rm -rf {0}".format(base_dir))
    execute_remote_shell(host_client, "rm -rf {0}".format(data_dir))
    execute_remote_shell(host_client, "rm -rf {0}".format(binlog_dir))
    execute_remote_shell(host_client, "mkdir -p {0}".format(base_dir))
    execute_remote_shell(host_client, "mkdir -p {0}".format(data_dir))
    execute_remote_shell(host_client, "mkdir -p {0}".format(binlog_dir))

    #生成配置文件并同步到远程机器
    print("\n--------------------------2.geneate mysql config-------------------------------")
    server_id = get_server_id(host_client, args)
    buffer_pool_size, buffer_pool_instance = get_mysql_buffer_pool_size(host_client)
    config_value = mysql_config.format(server_id, args.port, base_dir, data_dir, buffer_pool_size, buffer_pool_instance, binlog_dir)
    config_value = check_use_gtid_mode(args, config_value)
    config_value = check_use_repl_semi_sync(args, config_value)
    write_mysql_conf_to_file(args, config_value)

    #拷贝二进制包和解压
    print("\n--------------------------3.copy mysql install package and unzip---------------")
    os.system("scp {0} root@{1}:/opt/".format(args.package, args.host))
    execute_remote_shell(host_client, "tar -zxvf /opt/{0} --strip-components=1 -C {1}".format(args.package_name, base_dir))

    #创建用户和赋值权限
    execute_remote_shell(host_client, "groupadd mysql")
    execute_remote_shell(host_client, "useradd mysql -g mysql")
    execute_remote_shell(host_client, "chown -R mysql:mysql {0}".format(data_dir))
    execute_remote_shell(host_client, "chown -R mysql:mysql {0}".format(binlog_dir))

    #初始化数据和启动mysql
    print("\n--------------------------4.init mysql data------------------------------------")
    if(args.version == mysql_5_6):
        execute_remote_shell(host_client, "yum install -y perl-Module-Install.noarch")
        execute_remote_shell(host_client, "{0}/scripts/mysql_install_db --defaults-file=/etc/my.cnf --basedir={1}".format(base_dir, base_dir))
    else:
        execute_remote_shell(host_client, "{0}/bin/mysqld --defaults-file=/etc/my.cnf --initialize-insecure".format(base_dir))

    #要暂停一会，因为前面mysql初始化的时候进程还没有释放，就立刻启动会出现错误
    if(check_mysqld_pid_is_exists(host_client)):
        execute_remote_shell(host_client, "{0}/bin/mysqld --defaults-file=/etc/my.cnf".format(base_dir))
    #通过mysqld_safe进行启动，不建议这样的方式
    #execute_remote_shell(host_client, "cp {0}/support-files/mysql.server /etc/rc.d/init.d/mysqld".format(base_dir))
    #execute_remote_shell(host_client, "service mysqld start")

    host_client.close()
    print("\n--------------------------5.mysql install complete ok.-------------------------")

def kill_mysql_process(host_client):
    #改进kill掉mysql的逻辑
    result = execute_remote_shell(host_client, "cat {0}/mysql.pid".format(data_dir))
    if(len(result[error]) <= 0):
        mysql_pid = result[output][0].replace("\n", "")
        execute_remote_shell(host_client, "kill -6 " + mysql_pid)
    '''
    result = execute_remote_shell(host_client, "ps -ef | grep mysql | awk \'{print $2}\'")
    for pid in result[output]:
        execute_remote_shell(host_client, "kill -6 {0}".format(pid.replace("\n", "")))'''

def get_server_id(host_client, args):
    result = execute_remote_shell(host_client, "ip addr | grep inet | grep -v 127.0.0.1 | grep -v inet6 "
                                               "| awk \'{ print $2}\' | awk -F \"/\" \'{print $1}\' | awk -F \".\" \'{print $4}\'")
    return args.port + result[output][0].replace("\n", "")

def check_use_gtid_mode(args, config_value):
    if(args.gtid == 1):
        config_value = config_value + "\n" + gtid_config
    return config_value

def check_use_repl_semi_sync(args, config_value):
    if(args.semi_sync == 1):
        config_value = config_value + "\n" + rpl_semi_sync_config
        if(args.version == mysql_5_7):
            config_value += "rpl_semi_sync_master_wait_point=AFTER_SYNC"
    return config_value

def check_mysqld_pid_is_exists(host_client):
    number = 1
    while(number <= 10):
        result = execute_remote_shell(host_client, "ps -ef | grep mysqld")
        if(len(result[output]) <= 0):
            return True
        else:
            if(result[output][0].find("defaults-file") < 0):
                return True
            else:
                print("mysqld init pid is exists.")
        time.sleep(1)
        number += 1
    return True

def get_mysql_buffer_pool_size(host_client):
    buffer_pool_instance = 0
    result = execute_remote_shell(host_client, "free -g | head -n2 | tail -n1 | awk \'{print $2}\'")
    total_memory = int(result[output][0].replace("\n", ""))
    buffer_pool_size = str(int(round(total_memory * 0.75))) + "G"
    if(total_memory == 0):
        buffer_pool_size = "500M"
        buffer_pool_instance = 1
    elif(total_memory > 0 and total_memory <= 2):
        buffer_pool_instance = 2
    elif(total_memory > 2 and total_memory <= 8):
        buffer_pool_instance = 3
    elif(total_memory > 8 and total_memory <= 16):
        buffer_pool_instance = 4
    elif(total_memory > 16):
        buffer_pool_instance = 8
    return (buffer_pool_size, buffer_pool_instance)

def write_mysql_conf_to_file(args, config_value):
    file_path = "/tmp/my.cnf"
    file = open(file_path, "w")
    file.write(config_value)
    file.close()
    os.system("scp {0} root@{1}:/etc/".format(file_path, args.host))

def execute_remote_shell(host_client, shell):
    result = {}
    try:
        print(shell)
        stdin, stdout, stderr = host_client.exec_command(shell)
        result[error] = stderr.readlines()
        result[output] = stdout.readlines()
        if(len(result[error]) > 0):
            print(result[error][0].replace("\n", ""))
    except:
        host_client.close()
    return result

#region mysql config

mysql_config = ("""
#[client]
#default_character_set = utf8mb4

[mysql]
prompt = "\\u@\\h(\\d) \\\\r:\\\\m:\\\\s>"
default_character_set = utf8mb4

[mysqld]
server_id = {0}
user = mysql
port = {1}
character_set_server = utf8mb4
basedir = {2}
datadir = {3}
socket = mysql.sock
pid_file= mysql.pid
log_error = mysql.err

#innodb
innodb_buffer_pool_size = {4}
innodb_flush_log_at_trx_commit = 2
innodb_flush_log_at_timeout = 1
innodb_flush_method = O_DIRECT
innodb_support_xa = 1
innodb_lock_wait_timeout = 3
innodb_rollback_on_timeout = 1
innodb_file_per_table = 1
transaction_isolation = REPEATABLE-READ
innodb_log_buffer_size = 16M
innodb_log_file_size = 256M
innodb_additional_mem_pool_size = 16M
innodb_data_file_path = ibdata1:1G:autoextend
#innodb_log_group_home_dir = ./
#innodb_log_files_in_group = 2
#innodb_force_recovery = 1
#read_only = 1
innodb_sort_buffer_size=2M
innodb_online_alter_log_max_size=1G
innodb_buffer_pool_instances = {5}
innodb_buffer_pool_load_at_startup = 1
innodb_buffer_pool_dump_at_shutdown = 1
innodb_lru_scan_depth = 2000
innodb_file_format = Barracuda
innodb_file_format_max = Barracuda
innodb_purge_threads = 8
innodb_large_prefix = 1
innodb_thread_concurrency = 0
innodb_io_capacity = 300
innodb_print_all_deadlocks = 1
#innodb_locks_unsafe_for_binlog = 1
#innodb_autoinc_lock_mode = 2
innodb_open_files = 6000

#replication
log_bin = {6}/bin_log
log_bin_index = {6}/bin_log_index
binlog_format = ROW
binlog_cache_size = 2M
max_binlog_cache_size = 50M
max_binlog_size = 1G
expire_logs_days = 7
sync_binlog = 0
skip_slave_start = 1
binlog_rows_query_log_events = 1
relay_log = {6}/relay_log
relay_log_index = {6}/relay_log_index
max_relay_log_size = 1G
#relay_log_purge = 0
master_info_repository = TABLE
relay_log_info_repository = TABLE
relay_log_recovery = ON
log_slave_updates = 1
slave_max_allowed_packet = 1G
plugin_load = "rpl_semi_sync_master=semisync_master.so;rpl_semi_sync_slave=semisync_slave.so"

#slow_log
slow_query_log = 1
long_query_time = 2
log_output = FILE
slow_query_log_file = slow.log
log_queries_not_using_indexes = 1
log_throttle_queries_not_using_indexes = 30
log_slow_admin_statements = 1
log_slow_slave_statements = 1

#thread buffer size
tmp_table_size = 256M
max_heap_table_size = 256M
sort_buffer_size = 128K
join_buffer_size = 128K
read_buffer_size = 512K
read_rnd_buffer_size = 512K
key_buffer_size = 10M

#other
#sql_safe_updates = 1
skip_name_resolve = 1
open_files_limit = 65535
max_connections = 3000
max_connect_errors = 100000
#max_user_connections = 150
thread_cache_size = 64
lower_case_table_names = 0
query_cache_size = 0
query_cache_type = 0
max_allowed_packet = 1G
#time_zone = SYSTEM
lock_wait_timeout = 30
performance_schema = OFF
table_open_cache_instances = 2
metadata_locks_hash_instances = 8
table_open_cache = 4000
table_definition_cache = 2048

#timeout
wait_timeout = 300
interactive_timeout = 300
connect_timeout = 20
""")

gtid_config = """
gtid_mode = ON
enforce_gtid_consistency = ON"""

rpl_semi_sync_config = """
#rpl semi sync
rpl_semi_sync_master_enabled = 0
rpl_semi_sync_master_timeout = 999999999
rpl_semi_sync_master_trace_level = 32
rpl_semi_sync_master_wait_no_slave = ON
rpl_semi_sync_master_wait_for_slave_count = 1
rpl_semi_sync_slave_enabled = 0
rpl_semi_sync_slave_trace_level = 32
slave_parallel_workers = 8
slave_parallel_type = LOGICAL_CLOCK
"""

#endregion

if(__name__ == "__main__"):
    mysql_install(check_arguments())