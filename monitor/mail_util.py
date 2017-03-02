# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText

class MailUtil(object):
    __instance = None
    __mail_host="smtp.exmail.qq.com"
    __mail_user="sendmail@superjia.com"
    __mail_password="Iw2015Many"

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if(MailUtil.__instance is None):
            MailUtil.__instance = object.__new__(cls, *args, **kwargs)
        return MailUtil.__instance

    def send_text(self, subject, to_list, content):
        self.send_mail(subject, to_list, content, "plain")

    def send_html(self, subject, to_list, content):
        self.send_mail(subject, to_list, content, "html")

    def send_mail(self, subject, to_list, content, mail_type):
        list_t = []
        server = None
        if(isinstance(to_list, list) == False):
            list_t.append(to_list)
        try:
            message = MIMEText(content, _subtype=mail_type, _charset="utf8")
            message['Subject'] = subject
            message['From'] = self.__mail_user
            message['To'] = ";".join(list_t)

            server = smtplib.SMTP()
            server.connect(self.__mail_host)
            server.login(self.__mail_user, self.__mail_password)
            server.sendmail(self.__mail_user, list_t, message.as_string())
        finally:
            if(server != None):
                server.close()

#aa = MailUtil()
#aa.send_html("测试的邮件", "yangcaogui.sh@superjia.com", "<h1>aaaaa</h1>")
#http://www.cnblogs.com/xiaowuyi/archive/2012/03/17/2404015.html