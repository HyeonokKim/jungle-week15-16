from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class BoardPost(Base):
    __tablename__ = "board_posts"
    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_board_posts_user_id_problem_id"),
        CheckConstraint("selected_index BETWEEN 1 AND 5", name="selected_index_between_1_and_5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    selected_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    problem = relationship("Problem", back_populates="board_posts")
    user = relationship("User", back_populates="board_posts")
