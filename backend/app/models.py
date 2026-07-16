from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["user", "admin"]
GasType = Literal["NH3", "Toluene", "HCHO", "TEA"]


@dataclass(frozen=True)
class SessionPrincipal:
    user_id: str
    role: Role
    device_ids: tuple[str, ...]


class DetectionRequest(BaseModel):
    device_id: str = "dev-01"
    gas_type: GasType = "NH3"
    scenario: Literal["safe", "warning"] = "warning"


class AlertRuleUpdate(BaseModel):
    threshold: float = Field(gt=0, le=1000)
    severity: Literal["low", "medium", "high"]
