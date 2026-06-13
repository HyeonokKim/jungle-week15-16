from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "provider_id", name="uq_users_auth_provider_provider_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    auth_provider: Mapped[str] = mapped_column(String(50))
    provider_id: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")
    daily_assignments = relationship("UserDaily", back_populates="user", cascade="all, delete-orphan")
    board_posts = relationship("BoardPost", back_populates="user", cascade="all, delete-orphan")
    board_comments = relationship("BoardComment", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan", uselist=False)
    review_queue_items = relationship("ReviewQueue", back_populates="user", cascade="all, delete-orphan")
