from datetime import datetime
from typing import Optional

from alchemical.aio import Alchemical
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

db = Alchemical('sqlite:///file.db')


class Todo(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]]
    done: Mapped[bool] = mapped_column(Boolean(), default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f'id={self.id}, name={self.name}, done={self.done}, created_at={self.created_at}'
