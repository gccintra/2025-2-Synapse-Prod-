from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.extensions import db

class UserProviderEntity(db.Model):
    __tablename__ = "user_providers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    provider_name: Mapped[str] = mapped_column(
        db.String(50),
        nullable=False
    )
    provider_user_id: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )
    provider_email: Mapped[str] = mapped_column(
        db.String(255),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("UserEntity", back_populates="providers")
