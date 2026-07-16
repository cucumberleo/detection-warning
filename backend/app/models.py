from typing import Literal

from pydantic import BaseModel, Field


GasType = Literal["NH3", "Toluene", "HCHO", "TEA"]


class DetectionRequest(BaseModel):
    device_id: str = "dev-01"
    gas_type: GasType = "NH3"
    scenario: Literal["safe", "warning"] = "warning"


class AlertRuleUpdate(BaseModel):
    threshold: float = Field(gt=0, le=1000)
    severity: Literal["low", "medium", "high"]
