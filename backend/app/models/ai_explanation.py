from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class AIExplanation(Base):
    __tablename__ = "ai_explanations"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    final_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_reasoning_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    wrong_choice_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discarded_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critic_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    critic_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    references_used: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    candidate_summaries: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    attempt = relationship("Attempt", back_populates="ai_explanation")
    user = relationship("User", back_populates="ai_explanations")
    problem = relationship("Problem", back_populates="ai_explanations")
