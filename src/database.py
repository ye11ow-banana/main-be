import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import UUID, MetaData, text
from sqlalchemy.orm import DeclarativeBase, mapped_column

uuidpk = Annotated[
    uuid.UUID, mapped_column(primary_key=True, default=uuid.uuid4, index=True)
]
created_at = Annotated[
    datetime,
    mapped_column(server_default=text("TIMEZONE('utc', now())"), nullable=False),
]
updated_at = Annotated[
    datetime,
    mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        nullable=False,
        onupdate=datetime.utcnow,
    ),
]  # todo: find a trigger to update this field


class Base(DeclarativeBase):
    type_annotation_map = {uuidpk: UUID(as_uuid=True)}

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__} {', '.join(cols)}>"


metadata = MetaData()
