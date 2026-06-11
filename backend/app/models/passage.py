from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Passage(Base):
    __tablename__ = "passages"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam", back_populates="passages")
    problems = relationship("Problem", back_populates="passage")
