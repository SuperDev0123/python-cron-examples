import copy
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import COMMASPACE, formatdate

from _env import (
    EMAIL_USE_TLS,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_HOST_USER,
    EMAIL_HOST_PASSWORD,
)


def send_email(
    send_to,
    send_cc,
    send_bcc,
    subject,
    text,
    files=None,
    mime_type="plain",
    server="localhost",
    use_tls=True,
):
    assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = COMMASPACE.join(send_to)
    msg["Cc"] = COMMASPACE.join(send_cc)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject
    msg.attach(MIMEText(text, mime_type))

    smtp = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)

    if use_tls:
        smtp.starttls()

    smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    smtp.sendmail(EMAIL_HOST_USER, send_to + send_cc + send_bcc, msg.as_string())
    smtp.close()
