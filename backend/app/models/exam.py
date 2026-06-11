from __future__ import annotations

from sqlalchemy import Enum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.enums import ProblemArea


class Exam(Base):
    __tablename__ = "exams"
    __table_args__ = (
        UniqueConstraint("year", "round", "area", name="uq_exams_year_round_area"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    round: Mapped[str] = mapped_column(String(50), default="LEET", nullable=False)
    area: Mapped[ProblemArea] = mapped_column(Enum(ProblemArea, name="problem_area"), index=True)

    passages = relationship("Passage", back_populates="exam", cascade="all, delete-orphan")
    problems = relationship("Problem", back_populates="exam", cascade="all, delete-orphan")
