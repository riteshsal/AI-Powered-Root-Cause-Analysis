from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_name: Mapped[str | None] = mapped_column(String(255))
    batch_number: Mapped[str | None] = mapped_column(String(100))
    incident_type: Mapped[str | None] = mapped_column(String(255))
    incident_date: Mapped[date | None] = mapped_column(Date)
    process_step: Mapped[str | None] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text)
    observed_result: Mapped[str | None] = mapped_column(Text)
    specification: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(50),
        default="Draft"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    evidence = relationship(
        "Evidence",
        back_populates="investigation",
        cascade="all, delete-orphan"
    )

    five_whys = relationship(
        "FiveWhy",
        back_populates="investigation",
        cascade="all, delete-orphan"
    )

    root_causes = relationship(
        "RootCause",
        back_populates="investigation",
        cascade="all, delete-orphan"
    )

    missing_evidence = relationship(
        "MissingEvidence",
        back_populates="investigation",
        cascade="all, delete-orphan"
    )

    capa_actions = relationship(
        "CapaAction",
        back_populates="investigation",
        cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id")
    )

    evidence_text: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    investigation = relationship(
        "Investigation",
        back_populates="evidence"
    )


class FiveWhy(Base):
    __tablename__ = "five_whys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id")
    )

    why_number: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50),
        default="AI Suggested"
    )

    investigation = relationship(
        "Investigation",
        back_populates="five_whys"
    )


class RootCause(Base):
    __tablename__ = "root_causes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id")
    )

    cause: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    supporting_evidence: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(
        String(50),
        default="Pending Review"
    )

    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)

    investigation = relationship(
        "Investigation",
        back_populates="root_causes"
    )


class MissingEvidence(Base):
    __tablename__ = "missing_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id")
    )

    evidence_required: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(50),
        default="Required"
    )

    investigation = relationship(
        "Investigation",
        back_populates="missing_evidence"
    )


class CapaAction(Base):
    __tablename__ = "capa_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id")
    )

    action_type: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    effectiveness_check: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(50),
        default="Proposed"
    )

    owner: Mapped[str | None] = mapped_column(String(255))
    due_date: Mapped[date | None] = mapped_column(Date)

    investigation = relationship(
        "Investigation",
        back_populates="capa_actions"
    )