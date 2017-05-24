# -*- coding: utf-8 -*-

import pymysql, time, argparse, sys, random, string, commands, os


def check_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, dest="host", help="mysql slave host")
    parser.add_argument("--port", type=int, dest="port", help="mysql slave port", default=3306)
    parser.add_argument("--user", type=str, dest="user", help="mysql slave user")
    parser.add_argument("--password", type=str, dest="password", help="mysql slave password")
    parser.add_argument("--master-host", type=str, dest="master_host", help="mysql master host")
    parser.add_argument("--master-port", type=int, dest="master_port", help="mysql master port", default=3306)
    parser.add_argument("--master-user", type=str, dest="master_user", help="mysql master user")
    parser.add_argument("--master-password", type=str, dest="master_password", help="mysql master password")

    parser.add_argument("--base-dir", type=str, dest="base_dir", help="mysql base dir", default="/usr/local/mysql/")
    parser.add_argument("--charset", type=str, dest="charset", help="mysql charset", default="utf8")
    parser.add_argument("--mysqldump-path", type=str, dest="mysqldump_path", help="mysql dump path", default="/opt/master_data.sql")
    parser.add_argument("--repl-user", type=str, dest="repl_user", help="mysql replication user name", default="sys_repl_"+get_password(2))
    parser.add_argument("--repl-password", type=str, dest="repl_password", help="mysql replication user password", default=get_password(10))
    parser.add_argument("--repl-mode", type=int, dest="repl_mode", help="mysql replication mode [1-POS] or [2-GTID]", default=1)
    args = parser.parse_args()

    if not args.host or not args.port or not args.user or not args.password or \
       not args.master_host or not args.master_port or not args.master_user or not args.master_password:
        sys.exit(1)
    return args

def check_accout_is_ok(args):
    execute_sql_for_slave(args, "select 2;")
    execute_sql_for_master(args, "select 1;")

def create_slave_for_xtrabackup(args):
    #1.全量备份
    shell = "innobackupex --defaults-file={0} --no-timestamp " \
            "--host={1} --user={2} --password='{3}' --port={4} /slave_bak/" \
            .format("/etc/my.cnf", args.master_host, args.master_user, args.master_password, args.master_port)

    #2.scp数据拷贝到目标机器
    shell = "scp /slave_bak/ root@{0}:/slave_bak/".format(args.host)

    #3.在目标机器进行恢复操作
    shell = "innobackupex  --defaults-file=/etc/my.cnf  --apply-log --use-momery=2G /slave_bak/"

    #4.拷贝数据到目标目录，如果不想改，需要修改配置文件数据目录路径
    shell = "mv /slave_bak/ /mysql_data/"

    #5.启动数据库
    shell = "mysqld --defaults-file=/etc/my.cnf &"

    #6.change master操作，需要分为POS和GTID设置
    pass

def change_master(args):
    if(args.repl_mode == 1):
        #普通复制
        status, output = commands.getstatusoutput("head -n50 {0} | grep -i 'change master to'".format(args.mysqldump_path))
        sql = output[2:len(output)-1] + ","
    elif(args.repl_mode == 2):
        #gtid复制
        sql = "change master to master_auto_position=1,"
    sql = sql + " master_host='{0}', master_port={1}, master_user='{2}', master_password='{3}';"\
                .format(args.master_host, args.master_port, args.repl_user, args.repl_password)
    execute_sql_for_slave(args, sql)
    execute_sql_for_slave(args, "start slave;")

def check_slave_is_ok(args):
    number = 1
    while(number <= 5):
        result = execute_sql_for_slave(args, "show slave status;")
        if(result[0]["Slave_IO_Running"] != "Yes" or result[0]["Slave_SQL_Running"] != "Yes"):
            print(result["Last_Error"])
        else:
            print("IO Thread: Yes | SQL Thread: Yes")
        number = number + 1
        time.sleep(1)

def execute_sql_for_slave(args, sql):
    return execute_sql(args.host, args.port, args.user, args.password, args.charset, sql)

def execute_sql_for_master(args, sql):
    return execute_sql(args.master_host, args.master_port, args.master_user, args.master_password, args.charset, sql)

def execute_sql(host, port, user, password, charset, sql):
    cursor = None
    connection = None
    try:
        print(host, port, user, password, charset, sql)
        connection = pymysql.connect(host=host, port=port, user=user, password=password, charset=charset, cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        if(cursor != None):
            cursor.close()
        if(connection != None):
            connection.close()


