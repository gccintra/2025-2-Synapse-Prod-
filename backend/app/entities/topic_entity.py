from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class TopicEntity(db.Model):
    __tablename__ = "topics"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    state: Mapped[int] = mapped_column(db.SmallInteger, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

