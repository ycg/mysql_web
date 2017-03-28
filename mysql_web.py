# -*- coding: utf-8 -*-

#yum install openssl-devel  python-devel libffi-devel -y
#pip install flask threadpool pymysql DBUtils paramiko

import enum
from flask import Flask, render_template, request, app
from monitor import cache, server, slow_log

app = Flask(__name__)

mysql_cache = cache.Cache()
mysql_cache.load_all_host_infos()
monitor_server = server.MonitorServer()
monitor_server.load()
monitor_server.start()
#alarm_thread.AlarmThread().start()

'''
@app.route('/')
def hello_world():
    return 'Hello World!'

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

@app.route("/innodb/<int:hostid>")
def get_innodb_buffer_poo_infos(hostid):
    return get_monitor_data(data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(hostid))

def get_monitor_data(data_status=None, data_innodb=None, data_repl=None, data_engine_innodb=None, data_host=None):
    #return render_template("monitor.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host)
    return render_template("monitor_new.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host)


@app.route("/mysqls/<int:hostid>")
def get_host_monitor_status(hostid):
    return get_monitor_data(data_host=convert_object_to_list(mysql_cache.get_linux_info(hostid)),
                            data_status=convert_object_to_list(mysql_cache.get_status_infos(hostid)),
                            data_repl=convert_object_to_list(mysql_cache.get_repl_info(hostid)),
                            data_innodb=convert_object_to_list(mysql_cache.get_innodb_infos(hostid)),
                            data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(hostid))

def convert_object_to_list(obj):
    list_tmp = None
    if(obj != None):
        list_tmp = []
        list_tmp.append(obj)
    return list_tmp

@app.route("/load")
def load_host_info():
    return cache.Cache().load_all_host_infos()

@app.route("/test")
def test_chart():
    return get_monitor_data(data_status=monitor_server.get_cache_by_type(server.MonitorEnum.Status),
                            data_innodb=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb),
                            data_repl=monitor_server.get_cache_by_type(server.MonitorEnum.Replication))
'''
'''
@app.route("/ajax")
def test_ajax():
    return render_template("monitor_new1.html", data_status=monitor_server.get_cache_by_type(server.MonitorEnum.Status),
                                                data_innodb=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb),
                                                data_repl=monitor_server.get_cache_by_type(server.MonitorEnum.Replication),
                                                data_host=None, data_engine_innodb=None)
'''


'''
@app.route("/")
def home():
    return render_template("home.html", request_url="/mysqls")

@app.route("/mysqls")
def get_mysqls():
    return render_template("mysqls1.html", mysql_infos=mysql_cache.get_all_host_infos())

@app.route("/<type>")
def monitor_data(type):
    return render_template("home.html", request_url="/" + type)'''

@app.route("/mysql")
def get_mysql_data():
    return render_template("mysqls1.html", mysql_infos=mysql_cache.get_all_host_infos())

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
    return render_template("monitor_new1.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host)

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
    return render_template("home.html")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int("5000"))
