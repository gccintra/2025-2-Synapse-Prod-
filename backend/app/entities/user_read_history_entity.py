from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.extensions import db

class UserReadHistoryEntity(db.Model):
    __tablename__ = 'user_read_history'
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    news_id: Mapped[int] = mapped_column(ForeignKey('news.id', ondelete="CASCADE"), primary_key=True)
    read_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), primary_key=True, server_default=func.now())
    
    user = relationship("UserEntity", back_populates="read_history")
    news = relationship("NewsEntity", back_populates="read_by_users")

    def __repr__(self):
        return f"<UserReadHistoryEntity user_id={self.user_id} news_id={self.news_id} read_at='{self.read_at}'>"
