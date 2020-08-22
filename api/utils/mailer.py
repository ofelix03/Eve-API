import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from api.utils.load_env import load_env

load_env()

SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_SERVER = os.getenv('SMTP_SERVER')

EMAIL_FROM = os.getenv("EMAIL_FROM")


# def send_email(email_from=EMAIL_FROM, email_to=None, message=None):
#     print("email##", email_from)
#     with smtplib.SMTP_SSL(host=SMTP_SERVER, port=SMTP_PORT) as s:
#         s.login(SMTP_USER, SMTP_PASSWORD)
#         s.sendmail(email_from, email_to, message)


def send_email(email_from=EMAIL_FROM,  email_to=None,  subject=None, message=None):
    print("email##", email_from)

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to
    msg.attach(MIMEText(message, 'html'))

    with smtplib.SMTP_SSL(host=SMTP_SERVER, port=SMTP_PORT) as s:
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.sendmail(email_from, email_to, msg.as_string())




#
# def email_price_list(filtered_file_path):
#     msg = MIMEMultipart()
#     email_from = os.getenv("EMAIL_FROM")
#     email_to = os.getenv('EMAIL_TO')
#     msg['Subject'] = "".join(["Platt Prices - ", date_str1])
#     msg['From'] = email_from
#     msg['To'] = email_to
#     body = """
#                 <p>Hi, <p>
#                 <p>Kindly find attached the Platt Prices for {}</p>
#            """.format(date_str1)
#     msg.attach(MIMEText(body, 'html'))
#
#     attachment_bytes = filtered_file_path.read_bytes()
#     payload = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#     payload.set_payload(attachment_bytes)
#     encoders.encode_base64(payload)
#     filename = filtered_file_path.name.replace(' - ', ' ').replace(' ', '_')
#     payload.add_header('Content-Disposition', "attachment; filename= %s" % filename)
#     msg.attach(payload)
#
#     with smtplib.SMTP_SSL(host=os.getenv('SMTP_SERVER'), port=os.getenv('SMTP_PORT')) as s:
#         s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
#         s.sendmail(email_from, email_to, msg.as_string())