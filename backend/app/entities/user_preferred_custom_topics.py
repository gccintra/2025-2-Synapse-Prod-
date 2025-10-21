from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint
from app.extensions import db

class UserPreferredCustomTopicEntity(db.Model):
    __tablename__ = "users_preferred_custom_topics"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey("custom_topics.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)
    created_at = mapped_column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    user = relationship("UserEntity", lazy="select")
    custom_topic = relationship("CustomTopicEntity", lazy="select")

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_users_preferred_custom_topics_user_topic"),
    )
