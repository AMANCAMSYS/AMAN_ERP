"""Notifications module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional


class NotificationSettingsUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_tls: Optional[bool] = None
    sms_api_url: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_sender_name: Optional[str] = None
    notification_email_enabled: Optional[bool] = None
    notification_sms_enabled: Optional[bool] = None
