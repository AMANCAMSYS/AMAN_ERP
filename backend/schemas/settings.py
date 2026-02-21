"""Settings module Pydantic schemas."""
from pydantic import BaseModel
from typing import Dict, Any


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]
