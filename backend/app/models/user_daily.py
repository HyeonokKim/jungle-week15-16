from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class UserDaily(Base):
    __tablename__ = "user_daily"
    __table_args__ = (
        UniqueConstraint("user_id", "assigned_date", name="uq_user_daily_user_id_assigned_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assigned_date: Mapped[date] = mapped_column(Date, index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="daily_assignments")
    problem = relationship("Problem", back_populates="daily_assignments")
