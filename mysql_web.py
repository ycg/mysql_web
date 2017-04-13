# -*- coding: utf-8 -*-

#yum install openssl-devel  python-devel libffi-devel -y
#pip install flask threadpool pymysql DBUtils paramiko

import enum, settings
from flask import Flask, render_template, request, app, redirect
from monitor import cache, server, slow_log, mysql_status, alarm_thread, tablespace, general_log, execute_sql

app = Flask(__name__)

mysql_cache = cache.Cache()
mysql_cache.load_all_host_infos()
monitor_server = server.MonitorServer()
monitor_server.load()
monitor_server.start()
alarm_thread.AlarmLog().start()

@app.route("/mysql")
def get_mysql_data():
    return render_template("mysqls.html", mysql_infos=mysql_cache.get_all_host_infos())

@app.route("/mysql/<int:id>")
def get_mysql_data_by_id(id):
    return get_monitor_data(data_host=convert_object_to_list(mysql_cache.get_linux_info(id)),
                            data_status=convert_object_to_list(mysql_cache.get_status_infos(id)),
                            data_repl=convert_object_to_list(mysql_cache.get_repl_info(id)),
                            data_innodb=convert_object_to_list(mysql_cache.get_innodb_infos(id)),
                            data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(id))

@app.route("/status")
def get_status_data():
    return get_monitor_data(data_status=mysql_cache.get_all_status_infos())

@app.route("/status/<int:id>")
def get_status_data_by_id(id):
    return get_monitor_data(data_status=convert_object_to_list(mysql_cache.get_status_infos(id)))

@app.route("/innodb")
def get_innodb_data():
    return get_monitor_data(data_innodb=mysql_cache.get_all_innodb_infos())

@app.route("/innodb/<int:id>")
def get_innodb_data_by_id(id):
    return get_monitor_data(data_innodb=convert_object_to_list(mysql_cache.get_innodb_infos(id)), data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(id))

@app.route("/replication")
def get_replication_data():
    return get_monitor_data(data_repl=mysql_cache.get_all_repl_infos())

@app.route("/replication/<int:id>")
def get_replication_data_by_id(id):
    return get_monitor_data(slave_status=mysql_status.get_show_slave_status(id))

@app.route("/tablespace")
def get_tablespace():
    return get_monitor_data(tablespace_status=mysql_cache.get_all_tablespace_infos())

@app.route("/tablespace/<int:id>")
def get_tablespace_by_id(id):
    return render_template("tablespace.html", table_status=mysql_cache.get_tablespace_info(id).detail[0:50], host_info=mysql_cache.get_host_info(id))

@app.route("/general/<int:page_number>")
def get_general_log_by_page_number(page_number):
    if(page_number <= 5):
        page_list = range(1, 10)
    else:
        page_list = range(page_number-5, page_number + 6)
    return render_template("general_log.html", general_logs=general_log.get_general_logs_by_page_index(page_number), page_number=page_number, page_list=page_list)

@app.route("/general/<int:page_number>/detail/<checksum>")
def get_general_log_detail(page_number, checksum):
    return render_template("general_log_detail.html", page_number=page_number, general_log_detail=general_log.get_general_log_detail(checksum))

def convert_object_to_list(obj):
    list_tmp = None
    if(obj != None):
        list_tmp = []
        list_tmp.append(obj)
    return list_tmp

def get_monitor_data(data_status=None, data_innodb=None, data_repl=None, data_engine_innodb=None, data_host=None, slave_status=None, tablespace_status=None):
    return render_template("monitor.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host, slave_status=slave_status, tablespace_status=tablespace_status)

@app.route("/slowlog")
def get_slow_logs():
    return render_template("slow_log.html", slow_list = slow_log.get_slow_log_top_20(), slow_low_info=None)

@app.route("/slowlog/<checksum>")
def get_slow_log_detail(checksum):
    return render_template("slow_log.html", slow_list = None, slow_low_info=slow_log.get_slow_log_detail(checksum))

@app.route("/os")
def get_os_infos():
    return get_monitor_data(data_host=mysql_cache.get_all_linux_infos())

@app.route("/sql")
def execute_sql_home():
    return render_template("execute_sql.html", host_infos=mysql_cache.get_all_host_infos())

@app.route("/autoreview", methods=['GET', 'POST'])
def execute_sql_for_commit():
    print(request.form)
    return execute_sql.execute_sql_test(request.form["cluster_name"], request.form["sql_content"], request.form["workflow_name"])

@app.route("/testsql", methods=['GET', 'POST'])
def test_sql():
    return "execute sql ok."

@app.route("/home")
def home():
    return render_template("home.html", interval=settings.UPDATE_INTERVAL * 1000)

@app.route("/mytest")
def test_tablespace():
    monitor_server.test_get_tablespace_infos()
    return "aaaaaaaaa"

@app.route("/home/chart")
def chart():
    data="[1996-01-02, 22], [1997-02-08, 36], [1996-01-02, 37], [1996-01-02, 45], [1996-01-02, 50], [1996-01-02, 30], [1996-01-02, 61], [1996-01-02, 61], [1996-01-02, 62], [1996-01-02, 66], [1996-01-02, 73]"
    data="[aaa, 22], [bbb, 36], [1996-01-02, 37], [1996-01-02, 45], [1996-01-02, 50], [1996-01-02, 30], [1996-01-02, 61], [1996-01-02, 61], [1996-01-02, 62], [1996-01-02, 66], [1996-01-02, 73]"
    #return render_template("chart.html", p_data=data)
    return render_template("test.html")

@app.route("/home/binlog")
def get_test():
    return render_template("binlog.html")

if __name__ == '__main__':
    #app.run(threaded=True)
    app.run(debug=True, host="0.0.0.0", port=int("5000"))
