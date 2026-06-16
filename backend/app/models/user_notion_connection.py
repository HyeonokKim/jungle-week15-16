from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class UserNotionConnection(Base):
    __tablename__ = "user_notion_connections"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_notion_connections_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str] = mapped_column(String(100), nullable=False)
    workspace_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workspace_icon: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bot_id: Mapped[str] = mapped_column(String(100), nullable=False)
    duplicated_template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="notion_connection")
