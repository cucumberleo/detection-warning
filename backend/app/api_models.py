from typing import Literal

from pydantic import BaseModel, Field

from .models import AlertRuleUpdate, DetectionRequest, GasType


class LoginRequest(BaseModel):
    role: Literal["user", "admin"] = "user"


class PreferenceUpdate(BaseModel):
    gas_types: list[GasType] | None = None
    modules: list[Literal["monitor", "alerts", "analytics", "assistant"]] | None = None


class EventRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    page: str = Field(default="unknown", max_length=80)
    role: Literal["user", "admin"] = "user"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    role: Literal["user", "admin"] = "user"


AlertRulePayload = dict[GasType, AlertRuleUpdate]

__all__ = [
    "AlertRulePayload",
    "ChatRequest",
    "DetectionRequest",
    "EventRequest",
    "LoginRequest",
    "PreferenceUpdate",
]
