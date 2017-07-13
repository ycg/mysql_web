# -*- coding: utf-8 -*-

import cache, base_class, mail_util, tablespace
from flask import render_template, app

class Report():
    #REPORT_DATA = 24 * 60 * 60
    #1发送数据增长报告
    #REPORT_TABLESPACE = 7 * 24 * 60 * 60
    #2发送表空间检测报告
    #REPORT_DISK = 24 * 60 * 60
    #3发送磁盘空间报告
    #REPORT_INDEX = 30 * 24 * 60 * 60
    #4.发送冗余索引报告

    def report_data(self):
        pass

    def report_disk(self):
        pass

    def report_index(self):
        pass

    def report_tablespace(self):
        db_tablespace = {}
        for host_info in cache.Cache().get_all_host_infos():
            key = host_info.host + ":" + str(host_info.port)
            if(db_tablespace.has_key(key) == False):
                tmp_info = base_class.BaseClass(None)
                tmp_info.name = host_info.remark
                tablespace_list = tablespace.check_table_space(host_info)
                tmp_info.data = tablespace_list
                db_tablespace[key] = tmp_info
        str_html = render_template("report.html", tablespace_data=db_tablespace, report_name="Tablespace Report")
        mail_util.send_html("Database Tablespace Report", "yangcaogui.sh@superjia.com", str_html)

