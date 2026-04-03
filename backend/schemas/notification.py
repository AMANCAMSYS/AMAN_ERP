"""Pydantic schemas for the unified notification service (Phase 2)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    recipient_id: int
    channel: str  # "email" | "in_app" | "push"
    event_type: str
    title: str
    body: str
    feature_source: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    link: Optional[str] = None


class NotificationRead(BaseModel):
    id: int
    user_id: Optional[int]
    title: str
    message: Optional[str]
    body: Optional[str]
    link: Optional[str]
    is_read: bool
    type: Optional[str]
    channel: Optional[str]
    event_type: Optional[str]
    feature_source: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[int]
    status: Optional[str]
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationRead]
    total: int
    page: int
    page_size: int


class NotificationPreferenceRead(BaseModel):
    id: int
    user_id: int
    event_type: str
    email_enabled: bool
    in_app_enabled: bool
    push_enabled: bool

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    event_type: str
    email_enabled: bool = True
    in_app_enabled: bool = True
    push_enabled: bool = True


class UnreadCountResponse(BaseModel):
    unread_count: int
