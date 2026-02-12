from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class IncidentCreate(BaseModel):
    station_code: str = "LDS"  # Default to Leeds if not sent
    train_id: Optional[str] = None
    type: str
    severity: int
    description: Optional[str] = None

class IncidentUpdate(BaseModel):
    type: Optional[str] = None
    severity: Optional[int] = None
    description: Optional[str] = None

class IncidentResponse(IncidentCreate):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TrainResponse(BaseModel):
    from_code: str
    from_name: str
    origin_city: str
    scheduled: Optional[str] = None
    estimated: Optional[str] = None
    status: str
    delay_weight: int
    platform: Optional[str] = None
    delay_reason: Optional[str] = None
    operator: Optional[str] = None
    length: int = 0
    refund_eligible: bool = False
    train_id: Optional[str] = None