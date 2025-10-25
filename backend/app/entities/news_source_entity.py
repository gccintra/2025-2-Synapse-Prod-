from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class NewsSourceEntity(db.Model):
    __tablename__ = "news_sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))