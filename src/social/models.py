from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FriendResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    addressee_id: UUID
    status: str
    created_at: datetime


class FriendRequestDTO(BaseModel):
    user_id: UUID


class FriendshipActionDTO(BaseModel):
    friendship_id: UUID