from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from app.extensions import db
from app.entities.user_entity import UserEntity
from app.entities.news_entity import NewsEntity

class UserNewsEntity(db.Model):
    __tablename__ = "user_news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False)
    is_favorite: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
