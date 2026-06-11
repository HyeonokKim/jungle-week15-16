from __future__ import annotations

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.enums import ProblemArea


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (
        UniqueConstraint("exam_id", "number", name="uq_problems_exam_id_number"),
        CheckConstraint("answer_index BETWEEN 1 AND 5", name="answer_index_between_1_and_5"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    passage_id: Mapped[int | None] = mapped_column(ForeignKey("passages.id", ondelete="SET NULL"), nullable=True, index=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area: Mapped[ProblemArea] = mapped_column(Enum(ProblemArea, name="problem_area"), index=True)

    exam = relationship("Exam", back_populates="problems")
    passage = relationship("Passage", back_populates="problems")
    choices = relationship("Choice", back_populates="problem", cascade="all, delete-orphan", order_by="Choice.idx")
    attempts = relationship("Attempt", back_populates="problem", cascade="all, delete-orphan")
    daily_assignments = relationship("UserDaily", back_populates="problem")
    board_posts = relationship("BoardPost", back_populates="problem", cascade="all, delete-orphan")
    review_queue_items = relationship("ReviewQueue", back_populates="problem", cascade="all, delete-orphan")
