# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, current_app, app, redirect
from monitor import cache, server

app = Flask(__name__)


monitor_server = server.MonitorServer()
monitor_server.start()

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/yang", methods=['POST'])
def my_hello_wordaaa():
    return '''yang cao gui ''' + request.form['username']

@app.route("/<type>")
def monitor(type):
    if(type == server.MonitorEnum.Status.name):
        return render_template("monitor.html", data_status=monitor_server.get_cache_by_type(server.MonitorEnum.Status), data_innodb=None, data_repl=None)
    elif(type == server.MonitorEnum.Innodb.name):
        return render_template("monitor.html", data_status=None, data_innodb=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb), data_repl=None)
    elif(type == server.MonitorEnum.Replication.name):
        return render_template("monitor.html", data_status=None, data_innodb=None, data_repl=monitor_server.get_cache_by_type(server.MonitorEnum.Replication))
    return render_template("monitor.html", data_status=monitor_server.get_cache_by_type(server.MonitorEnum.Status),
                                           data_innodb=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb),
                                           data_repl=monitor_server.get_cache_by_type(server.MonitorEnum.Replication))


'''
@app.route("/status")
def status():
    return render_template("status.html", data=monitor_server.get_cache_by_type(server.MonitorEnum.Status), monitorname=server.MonitorEnum.Status.name)

@app.route("/innodb")
def innodb():
    return render_template("innodb.html", data=monitor_server.get_cache_by_type(server.MonitorEnum.Innodb), monitorname=server.MonitorEnum.Innodb.name)

@app.route("/replication")
def replication():
    return render_template("replication.html", data=monitor_server.get_cache_by_type(server.MonitorEnum.Replication), monitorname=server.MonitorEnum.Replication.name)
'''


if __name__ == '__main__':
    app.run(debug=True)
