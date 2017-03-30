# -*- coding: utf-8 -*-

#yum install openssl-devel  python-devel libffi-devel -y
#pip install flask threadpool pymysql DBUtils paramiko

import enum, settings
from flask import Flask, render_template, request, app, redirect
from monitor import cache, server, slow_log

app = Flask(__name__)

mysql_cache = cache.Cache()
mysql_cache.load_all_host_infos()
monitor_server = server.MonitorServer()
monitor_server.load()
monitor_server.start()
#alarm_thread.AlarmThread().start()

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
    return get_monitor_data(data_repl=convert_object_to_list(mysql_cache.get_repl_info(id)))

def convert_object_to_list(obj):
    list_tmp = None
    if(obj != None):
        list_tmp = []
        list_tmp.append(obj)
    return list_tmp

def get_monitor_data(data_status=None, data_innodb=None, data_repl=None, data_engine_innodb=None, data_host=None):
    return render_template("monitor.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host)

@app.route("/slowlog")
def get_slow_logs():
    return render_template("slow_log.html", slow_list = slow_log.get_slow_log_top_20(), slow_low_info=None)

@app.route("/slowlog/<checksum>")
def get_slow_log_detail(checksum):
    return render_template("slow_log.html", slow_list = None, slow_low_info=slow_log.get_slow_log_detail(checksum))

@app.route("/os")
def get_os_infos():
    return get_monitor_data(data_host=mysql_cache.get_all_linux_infos())

@app.route("/home")
def home():
    return render_template("home.html", interval=settings.UPDATE_INTERVAL * 1000)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int("5000"))
