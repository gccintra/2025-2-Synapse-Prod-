from datetime import datetime
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class UserPreferredNewsSourceEntity(db.Model):
    __tablename__ = "user_preferred_news_sources"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)
    created_at = mapped_column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    
    user = relationship("UserEntity", lazy="select")
    source = relationship("NewsSourceEntity", lazy="select")

    __table_args__ = (
        UniqueConstraint("user_id", "source_id", name="uq_user_news_sources_user_source"),
    )
