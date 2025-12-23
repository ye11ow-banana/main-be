from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AppDTO(BaseModel):
    id: UUID
    name: str
    image: str | None = None
    description: str
    is_active: bool = True
    created_at: datetime
