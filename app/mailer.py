import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_babel import gettext as _


def get_mail_config():
    return {
        "to": os.environ.get("MAIL_TO", ""),
        "host": os.environ.get("SMTP_HOST", "localhost"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "tls": os.environ.get("SMTP_TLS", "true").lower() == "true",
        "ssl": os.environ.get("SMTP_SSL", "false").lower() == "true",
    }


def send_email(subject, html_body, text_body=None, to=None):
    cfg = get_mail_config()
    recipient = to or cfg["to"]
    if not recipient:
        return False, _("No destination email configured. Set MAIL_TO in .env.")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["user"] or "bipagen@localhost"
    msg["To"] = recipient
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        if cfg["ssl"]:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=30)
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=30)
            if cfg["tls"]:
                server.starttls()
        if cfg["user"] and cfg["password"]:
            server.login(cfg["user"], cfg["password"])
        server.sendmail(msg["From"], [recipient], msg.as_string())
        server.quit()
        return True, _("Service request sent by email.")
    except Exception as e:
        return False, _("Failed to send the email: %(message)s") % {"message": e}
