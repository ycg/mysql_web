# -*- coding: utf-8 -*-

import pymysql, time, argparse, sys, random, string, commands

'''
#自动创建从库
#一丶mysqldump创建
    1.首先从主库进行备份，备份在本地
    2.然后导入到从库

#二丶xtrabackup备份
    1.首先检测有没有安装
    2.slave机器进行备份
    3.把安装包同步到本地机器
    4.数据库恢复
    5.启动

可能有的问题：
1.xtrabackup --远程备份问题
2.大数据库备份问题
3.是否是gtid操作

python mysql_auto_create_slave.py --host=192.168.11.130 --user=yangcg --password=yangcaogui \
--master-host=192.168.11.129 --master-user=yangcg --master-password=yangcaogui \
--base-dir=/usr/local/mysql --charset=utf8 --repl-user=sys_repl --repl-password=yangcaogui
'''

import os

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

def create_slave_for_mysqldump(args):
    check_accout_is_ok(args)
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

    #3.创建用户，如果没有指定用户，则自动创建用户-先要监测用户时候存在，如果存在则不创建
    print("\n-------------------------------3.create replication user-----------------------------------")
    create_replication_user(args)

    #4.进行change master操作
    print("\n-------------------------------4.change master operation-----------------------------------")
    change_master(args)

    #5.监测从库状态是否正确，如果没有异常，则创建从库成功
    print("\n-------------------------------5.check slave status is ok----------------------------------")
    check_slave_is_ok(args)

    print("\n-------------------------------6.create slave is ok----------------------------------------")

def create_slave_for_xtrabackup(args):
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

def create_replication_user(args):
    execute_sql_for_master(args, "grant replication slave, replication client on *.* to {0}@'%' identified by '{1}';".format(args.repl_user, args.repl_password))
    execute_sql_for_master(args, "flush privileges;")

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

def get_password(length):
    #随机出数字的个数
    numOfNum = random.randint(1,length-1)
    numOfLetter = length - numOfNum
    #选中numOfNum个数字
    slcNum = [random.choice(string.digits) for i in range(numOfNum)]
    #选中numOfLetter个字母
    slcLetter = [random.choice(string.ascii_letters) for i in range(numOfLetter)]
    #打乱这个组合
    slcChar = slcNum + slcLetter
    random.shuffle(slcChar)
    #生成密码
    password = ''.join([i for i in slcChar])
    return password

create_slave_for_mysqldump(check_arguments())