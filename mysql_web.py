# -*- coding: utf-8 -*-

#yum install openssl-devel python-devel libffi-devel -y
#pip install flask flask-login threadpool pymysql DBUtils paramiko

import json, os, gzip, StringIO, base64
import settings
from flask import Flask, render_template, request, app, redirect, make_response, helpers
from monitor import cache, server, slow_log, mysql_status, alarm_thread, tablespace, general_log, execute_sql, user, thread, chart
from monitor import user_login, base_class, alarm, new_slow_log
from flask_login import login_user, login_required
from flask_login import LoginManager, current_user

#region load data on run

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login_home"
login_manager.init_app(app=app)

mysql_cache = cache.Cache()
mysql_cache.load_all_host_infos()
monitor_server = server.MonitorServer()
monitor_server.load()
monitor_server.start()
#alarm.AlarmServer().start()
slow_log.load_slow_log_table_config()

#endregion

#region mysql api

@app.route("/mysql", methods=['GET', 'POST'])
@login_required
def get_mysql_data():
    return gzip_compress(render_template("mysqls.html", mysql_infos=mysql_cache.get_all_host_infos(keys=json.loads(request.values["keys"]))))

@app.route("/mysql/<int:id>")
@login_required
def get_mysql_data_by_id(id):
    return get_monitor_data(data_host=convert_object_to_list(mysql_cache.get_linux_info(id)),
                            data_status=convert_object_to_list(mysql_cache.get_status_infos(id)),
                            data_repl=convert_object_to_list(mysql_cache.get_repl_info(id)),
                            data_innodb=convert_object_to_list(mysql_cache.get_innodb_infos(id)),
                            data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(id))

#endregion

#region mysql status api

@app.route("/status", methods=['GET', 'POST'])
@login_required
def get_status_data():
    return gzip_compress(get_monitor_data(data_status=mysql_cache.get_all_status_infos(keys=json.loads(request.values["keys"]))))

@app.route("/status/<int:id>")
@login_required
def get_status_data_by_id(id):
    return get_monitor_data(data_status=convert_object_to_list(mysql_cache.get_status_infos(id)))

#endregion

#region innodb api

@app.route("/innodb", methods=['GET', 'POST'])
@login_required
def get_innodb_data():
    return gzip_compress(get_monitor_data(data_innodb=mysql_cache.get_all_innodb_infos(keys=json.loads(request.values["keys"]))))

@app.route("/innodb/<int:id>")
@login_required
def get_innodb_data_by_id(id):
    return get_monitor_data(data_innodb=convert_object_to_list(mysql_cache.get_innodb_infos(id)), data_engine_innodb=mysql_cache.get_engine_innodb_status_infos(id))

#endregion

#region replication api

@app.route("/replication", methods=['GET', 'POST'])
@login_required
def get_replication_data():
    return gzip_compress(get_monitor_data(data_repl=mysql_cache.get_all_repl_infos(keys=json.loads(request.values["keys"]))))

@app.route("/replication/<int:id>")
@login_required
def get_replication_data_by_id(id):
    return get_monitor_data(slave_status=mysql_status.get_show_slave_status(id))

#endregion

#region tablespace api

@app.route("/tablespace")
@login_required
def get_tablespace():
    return render_template("tablespace.html", host_infos=mysql_cache.get_all_host_infos())

@app.route("/tablespace/check/invoke")
def execute_check_tablespace():
    monitor_server.invoke_check_tablespace_method()
    return "invoke ok, please wait."

@app.route("/tablespace/sort/<int:host_id>/<int:sort_type>")
@login_required
def sort_tablespace(host_id, sort_type):
    if(host_id <= 0):
        return render_template("tablespace_dispaly.html", host_tablespace_infos=tablespace.sort_tablespace(sort_type), tablespace_status=None)
    else:
        table_list = tablespace.sort_tablespace_by_host_id(host_id, sort_type)
        if(len(table_list) > 50):
            table_list = table_list[0:50]
        return render_template("tablespace_dispaly.html", host_tablespace_infos=None, tablespace_status=table_list)

#endregion

#region general log api

@app.route("/general/<int:page_number>")
@login_required
def get_general_log_by_page_number(page_number):
    if(page_number <= 5):
        page_list = range(1, 10)
    else:
        page_list = range(page_number-5, page_number + 6)
    return render_template("general_log.html", general_logs=general_log.get_general_logs_by_page_index(page_number), page_number=page_number, page_list=page_list)

@app.route("/general/<int:page_number>/detail/<checksum>")
@login_required
def get_general_log_detail(page_number, checksum):
    return render_template("general_log_detail.html", page_number=page_number, general_log_detail=general_log.get_general_log_detail(checksum))

@app.route("/general/review/<int:checksum>")
@login_required
def set_general_log_is_review(checksum):
    return general_log.set_general_log_is_review(checksum)

@app.route("/general/review/<int:host_id>/<int:checksum>")
@login_required
def set_general_log_is_review_by_host_id(host_id, checksum):
    return general_log.set_general_log_is_review_by_host_id(host_id, checksum)

#endregion

#region common methon

def gzip_compress(content):
    zbuf = StringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=9, fileobj=zbuf)
    zfile.write(content)
    zfile.close()
    return base64.b64encode(zbuf.getvalue())

def gzip_decompress(content):
    compresseddata = base64.b64decode(content)
    compressedstream = StringIO.StringIO(compresseddata)
    gzipper = gzip.GzipFile(fileobj=compressedstream)
    data = gzipper.read()
    return data

def convert_object_to_list(obj):
    list_tmp = None
    if(obj != None):
        list_tmp = []
        list_tmp.append(obj)
    return list_tmp

def get_monitor_data(data_status=None, data_innodb=None, data_repl=None, data_engine_innodb=None, data_host=None, slave_status=None, tablespace_status=None):
    return render_template("monitor.html", data_engine_innodb=data_engine_innodb, data_status=data_status, data_innodb=data_innodb, data_repl=data_repl, data_host=data_host, slave_status=slave_status, tablespace_status=tablespace_status)

#endregion

#region slow log api

@app.route("/slowlog")
@login_required
def slow_log_home():
    return render_template("new_slow_log_home.html", host_infos=mysql_cache.get_all_host_infos())

@app.route("/slowlog/<int:query_type_id>")
@login_required
def get_slow_logs(query_type_id):
    return render_template("slow_log_display.html", slow_log_infos=slow_log.get_all_slow_infos(0, query_type_id))

@app.route("/slowlog/config/load/")
@login_required
def load_log_table_config():
    slow_log.load_slow_log_table_config()

@app.route("/slowlog/detail/<int:host_id>/<int:checksum>")
@login_required
def get_detail(host_id, checksum):
    return slow_log.get_slow_log_detail_by_host_id(host_id, checksum)

@app.route("/slowlog/detail/new/<int:checksum>")
@login_required
def get_slow_log_detail(checksum):
    return render_template("slow_log_detail.html", slow_low_info=slow_log.get_slow_log_detail(checksum))

@app.route("/newslowlog/", methods=['POST'])
@login_required
def new_get_slow_logs():
    print(request.form)
    return render_template("slow_log_display.html", slow_logs=new_slow_log.get_slow_logs(2016), slow_log_infos=None)

@app.route("/newslowlog/detail/<int:checksum>/<int:host_id>")
@login_required
def new_get_slow_log_detail(checksum, host_id):
    return render_template("slow_log_detail.html", slow_low_info=new_slow_log.get_slow_log_detail(checksum, 2016))

@app.route("/newslowlog/explain/<int:checksum>/<int:host_id>")
def get_explain_infos(server_id, checksum, ):
    return render_template("slow_log_detail.html", slow_low_info=new_slow_log.get_slow_log_detail(checksum, 2016))

#endregion

#region execute sql api

@app.route("/sql")
@login_required
def execute_sql_home():
    return render_template("execute_sql.html", host_infos=mysql_cache.get_all_host_infos())

@app.route("/autoreview", methods=['GET', 'POST'])
@login_required
def execute_sql_for_commit():
    return execute_sql.execute_sql_test(request.form["cluster_name"], request.form["sql_content"], request.form["workflow_name"], request.form["is_backup"])

#endregion

#region other api

@app.route("/os", methods=['GET', 'POST'])
@login_required
def get_os_infos():
    return gzip_compress(get_monitor_data(data_host=mysql_cache.get_all_linux_infos(keys=json.loads(request.values["keys"]))))

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", host_infos=mysql_cache.get_all_host_infos(), username=current_user.username, interval=settings.UPDATE_INTERVAL * 1000)

@app.route("/home/binlog")
@login_required
def get_test():
    return render_template("binlog.html")

@app.route("/home/load")
def load_all_host_infos():
    mysql_cache.load_all_host_infos()
    return "load ok"

#endregion

#region user web api

@app.route("/user")
@login_required
def user_home():
    return render_template("user.html", host_infos=mysql_cache.get_all_host_infos())

@app.route("/user/query", methods=['GET', 'POST'])
@login_required
def select_user():
    print(request.form)
    host_id = int(request.form["server_id"])
    return render_template("user_display.html", host_id=host_id, user_infos=user.MySQLUser(host_id).query_user(request.form["user_name"], request.form["ip"]))

@app.route("/user/db")
@login_required
def get_all_database_name():
    return user.MySQLUser(1).get_all_database_name()

@app.route("/user/<name>/<ip>")
@login_required
def get_detail_priv_by_user(name, ip):
    return user.MySQLUser(1).get_privs_by_user(name, ip)

@app.route("/user/detail/<int:host_id>/<name>/<ip>")
@login_required
def get_user_detail(host_id, name, ip):
    return user.MySQLUser(host_id).get_privs_by_user(name, ip)

@app.route("/user/add")
def add_user():
    pass

@app.route("/user/drop/<int:host_id>/<name>/<ip>")
@login_required
def drop_user(host_id, name, ip):
    return user.MySQLUser(host_id).drop_user(name, ip)

#endregion

#region thread api

@app.route("/thread")
@login_required
def thread_home():
    return render_template("thread.html", host_infos=mysql_cache.get_all_host_infos())

@app.route("/thread/<int:host_id>/<int:query_type>")
@login_required
def get_thread_infos(host_id, query_type):
    return render_template("thread_display.html", thread_infos=thread.get_all_thread(host_id, query_type))

#endregion

#region login api

@app.route("/login/verfiy", methods=['GET', 'POST'])
def login_verfiy():
    result = base_class.BaseClass(None)
    result.error = ""
    result.success = ""
    user_tmp = user_login.User(request.form["userName"])
    if(user_tmp.verify_password(request.form["passWord"], result) == True):
        login_user(user_tmp)
    return json.dumps(result, default=lambda o: o.__dict__)

@login_manager.user_loader
def load_user(user_id):
    return user_login.User(None).get(user_id)

@app.route("/login")
def login_home():
    return render_template("login.html")

#endregion

#region chart api

@app.route("/chart")
@login_required
def chart_home():
    return render_template("chart.html", host_infos=mysql_cache.get_all_host_infos(), interval=settings.UPDATE_INTERVAL * 1000)

@app.route("/chart/<int:host_id>")
@login_required
def get_chart_data_by_host_id(host_id):
    return chart.get_chart_data_by_host_id(host_id)

#endregion

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int("5000"), use_reloader=False)
