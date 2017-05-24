# -*- coding: utf-8 -*-

import pymysql, time, argparse, sys, commands, os

'''
grant replication slave on *.* to 'sys_repl'@'%' identified by 'yangcaogui';

python mysql_create_slave_for_mysqldump.py
--host=192.168.11.130 --user=yangcg --password=yangcaogui --port=3306 \
--master-host=192.168.11.129 --master-user=yangcg --master-password=yangcaogui --prot=3306
--repl-user=sys_repl --repl-password=yangcaogui
'''

#参数详解
#--host：从库地址
#--port：从库端口
#--user：从库用于执行sql的用户
#--password：从库用户密码

#--master-host
#--master-port
#--master-user
#--master-password

#--base-dir：mysql命令路径
#--charset：设置字符集
#--repl-mode：binlog模式[1-POS] or [2-GTID]

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

    parser.add_argument("--base-dir", type=str, dest="base_dir", help="mysql base dir", default="/usr/local/mysql/bin")
    parser.add_argument("--charset", type=str, dest="charset", help="mysql charset", default="utf8mb4")
    parser.add_argument("--mysqldump-path", type=str, dest="mysqldump_path", help="mysql dump path", default="/opt/master_data.sql")
    parser.add_argument("--repl-user", type=str, dest="repl_user", help="mysql replication user name")
    parser.add_argument("--repl-password", type=str, dest="repl_password", help="mysql replication user password")
    parser.add_argument("--repl-mode", type=int, dest="repl_mode", help="mysql replication mode [1-POS] or [2-GTID]", default=1)
    args = parser.parse_args()

    if not args.host or not args.port or not args.user or not args.password or \
       not args.master_host or not args.master_port or not args.master_user or not args.master_password or \
       not args.repl_user or not args.repl_password:
        sys.exit(1)
    return args

def check_accout_is_ok(args):
    execute_sql_for_slave(args, "select 2;")
    execute_sql_for_master(args, "select 1;")

def create_slave(args):
    check_accout_is_ok(args)
    os.system("PATH=$PATH:{0}".format(args.base_dir))

    #1.创建备份
    print("\n-------------------------------1.create mysqldump data-------------------------------------")
    execute_sql_for_slave(args, "stop slave;")
    shell = "mysqldump -h{0} -u{1} -p{2} -P{3} " \
            "--max-allowed-packet=1G --single-transaction --master-data=2 " \
            "--default-character-set={4} --triggers --routines --events -B --all-databases > {5}"\
            .format(args.master_host, args.master_user, args.master_password, args.master_port, args.charset, args.mysqldump_path)
    os.system(shell)

    #2.导入数据-对导入速度进行优化，不要设置双1，而且设置不写binlog
    print("\n-------------------------------2.import mysqldump data-------------------------------------")
    os.system("mysql -h{0} -u{1} -p{2} -P{3} --max-allowed-packet=1G --default-character-set={4} < {5}"
              .format(args.host, args.user, args.password, args.port, args.charset, args.mysqldump_path))

    #4.进行change master操作
    print("\n-------------------------------3.change master operation-----------------------------------")
    change_master(args)

    #5.监测从库状态是否正确，如果没有异常，则创建从库成功
    print("\n-------------------------------4.check slave status is ok----------------------------------")
    check_slave_is_ok(args)

    print("\n-------------------------------5.create slave is ok----------------------------------------")

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
        if(len(result) > 0):
            result = result[0]
        if(result["Slave_IO_Running"] != "Yes" or result["Slave_SQL_Running"] != "Yes"):
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
        connection = pymysql.connect(host=host, port=port, user=user, password=password, charset=charset, cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        if(cursor != None):
            cursor.close()
        if(connection != None):
            connection.close()

if(__name__ == "__main__"):
    create_slave(check_arguments())