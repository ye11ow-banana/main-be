from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TeamStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TeamResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    addressee_id: UUID
    status: str
    created_at: datetime


class TeamRequestDTO(BaseModel):
    user_id: UUID


class TeamActionDTO(BaseModel):
    team_id: UUID
