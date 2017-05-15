import time
from flask import render_template

import cache, settings, mail_util

def send_report_everyday():
    html_str = render_template("report.html", tablespace_infos=cache.Cache().get_all_tablespace_infos())
    subject = "MySQL Report - {0}".format(time.strftime("%Y-%m-%d", time.localtime(time.time())))
    mail_util.send_html(subject, settings.EMAIL_SEND_USERS, html_str)
    print("send report ok")