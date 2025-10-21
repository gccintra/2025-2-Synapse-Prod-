from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint
from app.extensions import db

class UserSavedNewsEntity(db.Model):
    __tablename__ = "user_saved_news"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    is_favorite: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_at = mapped_column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = relationship("UserEntity", viewonly=True)
    news = relationship("NewsEntity", viewonly=True)

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="uq_user_saved_news_user_news"),
    )
