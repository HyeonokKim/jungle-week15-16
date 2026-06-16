from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class WeeklySummaryExport(Base):
    __tablename__ = "weekly_summary_exports"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", "destination", name="uq_weekly_summary_exports_user_week_destination"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    destination: Mapped[str] = mapped_column(String(30), default="notion", nullable=False)
    external_page_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="weekly_summary_exports")
