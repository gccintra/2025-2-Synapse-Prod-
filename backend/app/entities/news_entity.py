from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text
from app.extensions import db

class NewsEntity(db.Model):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(db.String(500), unique=True, nullable=False)
    image_url: Mapped[str] = mapped_column(db.String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False) 
    published_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False)
    
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    source = relationship("NewsSourceEntity", lazy="select")
    topic = relationship("TopicEntity", lazy="select")

    saved_by_users = relationship(
        "UserEntity",
        secondary="user_saved_news",
        back_populates="saved_news"
    )
    
    read_by_users = relationship(
        "UserReadHistoryEntity", 
        back_populates="news", 
        cascade="all, delete-orphan"
    )