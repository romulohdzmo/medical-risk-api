"""SQLAlchemy models for clinical assessment records."""

import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from medical_risk_api.db import Base


class AssessmentAudit(Base):
    """Persisted clinical assessment audit record for traceability."""

    __tablename__ = "assessment_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    patient_age: Mapped[int] = mapped_column(Integer, nullable=False)
    systolic_bp: Mapped[float] = mapped_column(Float, nullable=False)
    cholesterol_mg_dl: Mapped[float] = mapped_column(Float, nullable=False)
    fasting_blood_sugar_mg_dl: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False)
    is_smoker: Mapped[bool] = mapped_column(nullable=False)
    risk_score_percent: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[str] = mapped_column(String(32), nullable=False)
    model_version: Mapped[str] = mapped_column(String(16), nullable=False)
    top_risk_factors: Mapped[list[dict[str, str | float]]] = mapped_column(
        JSON, nullable=False
    )
