# -*- coding: utf-8 -*-

#pip install flask threadpool pymysql DBUtils

from flask import Flask, render_template, request, current_app, app, redirect
from monitor import cache, server, alarm_thread, report_server

app = Flask(__name__)

mysql_cache = cache.Cache()
mysql_cache.load_all_host_infos()
monitor_server = server.MonitorServer()
monitor_server.load()
monitor_server.start()
#alarm_thread.AlarmThread().start()
report_server.Report().report_tablespace()

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/yang", methods=['POST'])
def my_hello_wordaaa():
    return '''yang cao gui ''' + request.form['username']

@app.route("/<type>")
def monitor(type):
    if(type.upper() == server.MonitorEnum.Host.name.upper()):
        return get_monitor_data(data_host=monitor_server.get_mysql_status(server.MonitorEnum.Status))
    elif(type.upper() == server.MonitorEnum.Status.name.upper()):
        return get_monitor_data(data_status=monitor_server.get_cache_by_type(server.MonitorEnum.Status))
    elif(type.upper() == server.MonitorEnum.Innodb.name.upper()):
        return get_monitor_data(data_innodb=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb))
    elif(type.upper() == server.MonitorEnum.Replication.name.upper()):
        return get_monitor_data(data_repl=monitor_server.get_cache_by_type(server.MonitorEnum.Replication))
    elif(type.upper() == "ALL"):
        return get_monitor_data(data_status=monitor_server.get_cache_by_type(server.MonitorEnum.Status),
                                data_innodb=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb),
                                data_repl=monitor_server.get_cache_by_type(server.MonitorEnum.Replication))
    else:
        return "No data."

@app.route("/innodb/<hostid>")
def get_innodb_buffer_poo_infos(hostid):
    return get_monitor_data(data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(int(hostid)))

def get_monitor_data(data_status=None, data_innodb=None, data_repl=None, data_engine_innodb=None, data_host=None):
    return render_template("monitor.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host)

@app.route("/load")
def load_host_info():
    return cache.Cache().load_all_host_infos()

@app.route("/test")
def test_chart():
    return render_template("chart.html")

@app.route("/home")
def home():
    return render_template("home.html")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int("5000"))
