"""Financial notes module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional


class NoteCollectParams(BaseModel):
    collection_date: Optional[str] = None
    treasury_account_id: Optional[int] = None


class NoteProtestParams(BaseModel):
    protest_date: Optional[str] = None
    reason: Optional[str] = None


class NotePayParams(BaseModel):
    payment_date: Optional[str] = None
    treasury_account_id: Optional[int] = None
