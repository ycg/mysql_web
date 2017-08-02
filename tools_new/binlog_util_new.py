# -*- coding: utf-8 -*-

import commands, MySQLdb, time

# 直接解析binlog文件
# 不过需要指定有同样表结构的数据
# 在最下面的代码中进行数据库的指定，以及binlog文件路径的指定

class Data:
    def __init__(self):
        pass

def execute(sql):
    conn = None
    try:
        columns = []
        conn = MySQLdb.connect(host="192.168.1.208", port=3310, user="yangcg", passwd="yangcaogui", db="mysql")
        cursor = conn.cursor()
        result = cursor.execute(sql)
        for field in cursor.description:
            columns.append(field[0])

        data = []
        for row in cursor.fetchall():
            rowValues = []
            for index in range(len(columns)):
                rowValues.append(row[index])
            data.append(rowValues)
        return data
    finally:
        if(conn != None):
            conn.close()
    return None

class ColumnInfo:
    def __init__(self):
        pass

table_dic = {}

'''获取表的列信息并且返回表名'''
def get_table_columns(value, sql_flag):
    table_name = ""
    if(sql_flag == DELETE):
        table_name = value.split(" ")[3]
    elif(sql_flag == INSERT):
        table_name = value.split(" ")[3]
    elif(sql_flag == UPDATE):
        table_name = value.split(" ")[2]

    if(len(table_name) > 0):
        if (table_dic.has_key(table_name) == False):
            result = execute("DESC " + table_name)
            table_dic[table_name] = result
    return table_name

'''获取表列数量'''
def get_table_column_count(table_name):
    return len(table_dic[table_name])

'''根据下标获取表列名'''
def get_table_column_name(table_name, index):
    return "`" + table_dic[table_name][index][0] + "`"

'''获取列类型'''
def check_column_type(table_name, index, value):
    columnType = table_dic[table_name][index][1]

    if(columnType.find("timestamp") >= 0):
        return "FROM_UNIXTIME(" + value + ")"

    if (columnType.find("int") >= 0):
        if(columnType.find("unsigned") == -1):
            return value.split(' ')[0];

    return value

'''检查是否是主键'''
def check_is_primary_key(table_name, index):
    columnType = table_dic[table_name][index][3]
    return columnType.find("PRI")

'''获取标记位'''
def get_substring_start_index(line_flag):
    return len(FLAG) + 3 + len("@%d=" % ((line_flag - 2)))

'''生成delete的sql语句'''
def delete(log_value, line_flag, table_name, result_value):
    if(line_flag == 3):
        result_value += " WHERE "

    column_index = line_flag - 3
    column_name = get_table_column_name(table_name, column_index)
    value = log_value[get_substring_start_index(line_flag):].rstrip()

    if(UPDATE_OR_DELETE_FOR_PRIMARY_KEY == 1):
        if(check_is_primary_key(table_name, column_index)):
            result_value += "%s=%s;" % (column_name, check_column_type(table_name, column_index, value))
    else:
        result_value += "%s=%s" % (column_name, check_column_type(table_name, column_index, value))
        if(get_table_column_count(table_name) == (line_flag - 2)):
            result_value += ";"
        else:
            result_value += " AND "
    return result_value

'''生成insert的sql语句'''
def insert(log_value, line_flag, table_name, result_value):
    if(line_flag == 3):
        result_value += " VALUES("

    index = get_substring_start_index(line_flag)
    value = log_value[index:]
    result_value += check_column_type(table_name, line_flag - 3, value);
    if(get_table_column_count(table_name) == (line_flag - 2)):
        result_value += ");"
    else:
        result_value += ", "
    return result_value

'''生成update的sql语句'''
def update(log_value, line_flag, table_name, result_value):
    if(line_flag == 3):
        result_value += " WHERE "

    columnCount = get_table_column_count(table_name);
    setFlag = columnCount + 3;

    if(line_flag < setFlag):
        column_index = line_flag - 3
        column_name = get_table_column_name(table_name, column_index)
        value = log_value[get_substring_start_index(line_flag):].rstrip()

        if(UPDATE_OR_DELETE_FOR_PRIMARY_KEY == 1):
            if(check_is_primary_key(table_name, column_index) > 0):
                result_value += "%s=%s;" % (column_name, check_column_type(table_name, column_index, value))
        else:
            result_value +=  "%s=%s" % (column_name, check_column_type(table_name, column_index, value))
            if(line_flag == (columnCount + 2)):
                result_value += ";"
            else:
                result_value += " AND "
    return result_value

'''delete反转生成insert'''
def delete_for_reverse(log_value, line_flag, table_name, result_value):
    return insert(log_value, line_flag, table_name, result_value)

'''insert反转生成delete'''
def insert_for_reverse(log_value, line_flag, table_name, result_value):
    return delete(log_value, line_flag, table_name, result_value)

'''update生成更新前的update操作'''
def update_for_reverse(log_value, line_flag, table_name, result_value):
    if(line_flag == 3):
        result_value += " SET "
    column_count = get_table_column_count(table_name)
    set_flag = column_count + 3

    if(line_flag < set_flag):
        column_name = get_table_column_name(table_name, line_flag - 3)
        value = log_value[get_substring_start_index(line_flag):].rstrip()
        result_value += ("%s=%s") % (column_name, check_column_type(table_name, line_flag - 3, value))
        if(line_flag == (column_count + 2)):
            pass
        else:
            result_value += ", "
    elif(line_flag == set_flag):
        result_value += " WHERE "
    elif(line_flag > set_flag):
        column_index = line_flag - set_flag - 1
        column_name = get_table_column_name(table_name, column_index)
        value = log_value[get_substring_start_index(line_flag - column_count - 1):].rstrip()

        if(UPDATE_OR_DELETE_FOR_PRIMARY_KEY == 1):
            if(check_is_primary_key(table_name, column_index) >= 0):
                result_value += ("%s=%s;") % (column_name, check_column_type(table_name, column_index, value))
        else:
            result_value += ("%s=%s") % (column_name, check_column_type(table_name, column_index, value))
            if(line_flag == (column_count + set_flag)):
                result_value += ";"
            else:
                result_value += " AND "

    return result_value

'''入口方法，循环binlog所有的行'''
def general_sql(binlog_values, sql_type):
        lineFlag = 0
        sql_list = []

        sqlFlag = ""
        tableName = ""
        resultSQLValue = ""

        for logValue in binlog_values:
            if (len(logValue) < 3):
                continue;

            if (substring(logValue, 0, 3) == FLAG):
                sqlFlagTmp = ""
                if (len(logValue) >= 10):
                    sqlFlagTmp = substring(logValue, 4, 6)

                #判断的操作类型
                if ((sqlFlagTmp == DELETE) | (sqlFlagTmp == INSERT) | (sqlFlagTmp == UPDATE)):
                    lineFlag = 1
                    sqlFlag = sqlFlagTmp

                    if(len(resultSQLValue.strip().lstrip()) > 0):
                        sql_list.append(resultSQLValue + "\n")

                    resultSQLValue = substring(logValue, 3, (len(logValue) - len(FLAG))).replace("\r", "").strip().lstrip()

                    #反转sql的时候判断
                    if(sql_type == SQL_REVERSE):
                        if(sqlFlagTmp == DELETE):
                            resultSQLValue = "%s INTO %s" % (INSERT, resultSQLValue.split(' ')[2])
                        elif(sqlFlagTmp == INSERT):
                            resultSQLValue = "%s FROM %s" % (DELETE, resultSQLValue.split(' ')[2])

                    tableName = get_table_columns(logValue, sqlFlag)
                else:
                    lineFlag = lineFlag + 1

                #根据标记和sql类型生成delete update insert语句
                if(lineFlag > 2):
                    if(sqlFlag == DELETE):
                        if(sql_type == SQL_REVERSE):
                            resultSQLValue = delete_for_reverse(logValue, lineFlag, tableName, resultSQLValue)
                        else:
                            resultSQLValue = delete(logValue, lineFlag, tableName, resultSQLValue)
                    elif(sqlFlag == INSERT):
                        if(sql_type == SQL_REVERSE):
                            resultSQLValue = insert_for_reverse(logValue, lineFlag, tableName, resultSQLValue)
                        else:
                            resultSQLValue = insert(logValue, lineFlag, tableName, resultSQLValue)
                    elif(sqlFlag == UPDATE):
                        if(sql_type == SQL_REVERSE):
                            resultSQLValue = update_for_reverse(logValue, lineFlag, tableName, resultSQLValue)
                        else:
                            resultSQLValue = update(logValue, lineFlag, tableName, resultSQLValue)


        sql_list.append(resultSQLValue)

        file = None
        file_name = "binlog.sql"
        try:
            file = open(file_name, "w")
            file.truncate()
            file.writelines(sql_list)
        finally:
            if(file != None):
                file.close()

def substring(str, index, length):
    endIndex = index + length
    return str[index : endIndex]

'''根据参数获取mysqlbinlog的脚本完整命令'''
def get_mysql_binlog_shell():
    shell_value = "mysqlbinlog -v --base64-output=decode-rows "

    if(START_POSITION > 0 & STOP_POSITION > 0):
        shell_value += ("--start-position=%d --stop-position=%d ") % (START_POSITION, STOP_POSITION)

    if(len(START_DATETIME) > 0 & len(STOP_DATETIME) > 0):
        shell_value += ("--start-datetime=%s --stop-datetime=%s ") % (START_DATETIME, STOP_DATETIME)

    if(len(BINLOG_PATH) > 0):
        shell_value += BINLOG_PATH

    return shell_value

#根据binlog生成原生SQL
SQL = 1
#根据binlog生成反正
SQL_REVERSE = 2
#binlog文件每一行的开头标记
FLAG = "###"
#delete语句关键字
DELETE = "DELETE"
#insert语句关键字
INSERT = "INSERT"
#update语句关键字
UPDATE = "UPDATE"
#update和delete的时候只根据主键查询
UPDATE_OR_DELETE_FOR_PRIMARY_KEY = 0

#host="192.168.1.208", port=3310, user="yangcg", passwd="yangcaogui", db="mysql"
HOST = "192.168.1.208"
PORT = 3310
USER = "yangcg"
PASSWORD = "yangcaogui"
START_POSITION = 0
STOP_POSITION = 0
START_DATETIME = ""
STOP_DATETIME = ""
BINLOG_PATH = ""

print("start read bin log. %d" % (time.time()))
(status, output) = commands.getstatusoutput('mysqlbinlog -v --base64-output=decode-rows /data/mysql3310/mysql_bin.000005')
print("read bin log ok and analysis. %d" % (time.time()))
general_sql(output.split("\n"), SQL_REVERSE)
print("Complete OK. %d" % (time.time()))
