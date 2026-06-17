from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.enums import ProblemScope


class UserSetting(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("timer_limit_sec IN (120, 180, 240)", name="timer_limit_sec_allowed_values"),
        CheckConstraint("review_interval_days IS NULL OR review_interval_days IN (3, 5, 7)", name="review_interval_days_allowed_values"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    problem_scope: Mapped[ProblemScope] = mapped_column(Enum(ProblemScope, name="problem_scope"), default=ProblemScope.all_random, nullable=False)
    timer_limit_sec: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    review_interval_days: Mapped[int | None] = mapped_column(Integer, default=3, nullable=True)
    weak_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="settings")
