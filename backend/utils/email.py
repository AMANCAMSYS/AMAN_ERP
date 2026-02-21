import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(to_emails: list, subject: str, body: str, attachments: list = None):
    """
    Send an email with optional attachments.
    
    :param to_emails: List of recipient email addresses
    :param subject: Email subject
    :param body: Email body (HTML or Plain Text)
    :param attachments: List of dicts -> [{"filename": "report.pdf", "data": bytes, "content_type": "application/pdf"}]
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("⚠️ SMTP settings not configured. Email not sent.")
        return False

    msg = MIMEMultipart()
    msg['From'] = settings.SYSTEM_EMAIL
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    if attachments:
        for attachment in attachments:
            part = MIMEApplication(attachment["data"], Name=attachment["filename"])
            part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
            msg.attach(part)

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SYSTEM_EMAIL, to_emails, msg.as_string())
        server.quit()
        logger.info(f"✅ Email sent to {to_emails}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False
