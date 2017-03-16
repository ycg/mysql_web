import smtplib, settings
from email.mime.text import MIMEText

def send_text(subject, to_list, content):
    send_mail(subject, to_list, content, "plain")

def send_html( subject, to_list, content):
    send_mail(subject, to_list, content, "html")

def send_mail(subject, to_list, content, mail_type):
    list_t = []
    server = None
    if(isinstance(to_list, list) == False):
        list_t.append(to_list)
    try:
        message = MIMEText(content, _subtype=mail_type, _charset="utf8")
        message['Subject'] = subject
        message['To'] = ";".join(list_t)
        message['From'] = settings.EMAIL_HOST_USER

        server = smtplib.SMTP()
        server.connect(settings.EMAIL_HOST)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.EMAIL_HOST_USER, list_t, message.as_string())
    finally:
        if(server != None):
            server.close()