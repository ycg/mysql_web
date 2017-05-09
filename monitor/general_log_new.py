import pymysql, traceback, time, commands, sys
reload(sys)
sys.setdefaultencoding('utf-8')


interval_rows = 1000

class Entity():
    pass

def get_general_log():
    connection, cursor = None, None
    try:
        connection = pymysql.connect(host="10.171.251.52", port=3309, user="yangcg", passwd="yangcaogui123!.+", db="mysql", charset="utf8")
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("select count(1) as rows from mysql.general_log;")
        rows_count = cursor.fetchone()["rows"]

        number = rows_count / interval_rows + 1
        sql = "select event_time, user_host, argument from mysql.general_log limit {0}, {1}"
        for page in range(0, number):
            print(page)
            cursor.execute(sql.format(page * interval_rows, interval_rows))
            fetch_all(cursor.fetchall())
    except:
        traceback.print_exc()
    finally:
        if (cursor != None):
            cursor.close()
        if (connection != None):
            connection.close()

def fetch_all(data):
    for row in data:
        command = "pt-fingerprint --query=\"{0}\"".format(row["argument"])
        print(command)
        (status, output) = commands.getstatusoutput(command)
        #print(status, output)

aa = time.time()
get_general_log()
bb = time.time()
print(bb - aa)