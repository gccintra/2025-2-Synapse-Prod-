from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint, func
from app.extensions import db

class CustomTopicEntity(db.Model):
    __tablename__ = "custom_topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
