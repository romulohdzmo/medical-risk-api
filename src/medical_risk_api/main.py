"""FastAPI application entrypoint for medical risk service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from medical_risk_api.db import Base, engine, get_db_session
from medical_risk_api.middleware import ClinicalAuditMiddleware
from medical_risk_api.models_db import AssessmentAudit
from medical_risk_api.predictor import predictor
from medical_risk_api.schemas import (
    AssessmentAuditRecord,
    BloodPressureInput,
    BloodPressureOutput,
    BodyMassInput,
    BodyMassOutput,
    CardiovascularRiskInput,
    CardiovascularRiskOutput,
    FactorContribution,
)
from medical_risk_api.vitals import calculate_bmi, calculate_map


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages database connection lifecycle and creates tables if needed."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Clinical Risk Analysis API",
    description="Microservice for physiological metrics, vital sign assessment, and ML risk modeling.",
    version="0.1.0",
    lifespan=lifespan,
)

# Register clinical audit middleware
app.add_middleware(ClinicalAuditMiddleware)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """Basic health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.post(
    "/vitals/map",
    response_model=BloodPressureOutput,
    status_code=status.HTTP_200_OK,
)
def compute_map(payload: BloodPressureInput) -> BloodPressureOutput:
    """Calculates Mean Arterial Pressure from systolic and diastolic values."""
    try:
        map_val, map_status = calculate_map(
            systolic=payload.systolic,
            diastolic=payload.diastolic,
        )
        return BloodPressureOutput(
            mean_arterial_pressure=map_val,
            status=map_status,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@app.post(
    "/vitals/bmi",
    response_model=BodyMassOutput,
    status_code=status.HTTP_200_OK,
)
def compute_bmi(payload: BodyMassInput) -> BodyMassOutput:
    """Calculates Body Mass Index given weight and height."""
    try:
        bmi_val, bmi_cat = calculate_bmi(
            weight_kg=payload.weight_kg,
            height_m=payload.height_m,
        )
        return BodyMassOutput(
            body_mass_index=bmi_val,
            category=bmi_cat,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@app.post(
    "/risk/cardiovascular",
    response_model=CardiovascularRiskOutput,
    status_code=status.HTTP_200_OK,
)
async def estimate_cardiovascular_risk(
    payload: CardiovascularRiskInput,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CardiovascularRiskOutput:
    """Predicts 10-year cardiovascular risk probability and persists audit records."""
    try:
        risk_score, category, top_factors = predictor.predict_risk(payload)
        correlation_id = request.headers.get("X-Correlation-ID", "unknown-session")

        audit_entry = AssessmentAudit(
            correlation_id=correlation_id,
            patient_age=payload.age,
            systolic_bp=payload.systolic_bp,
            cholesterol_mg_dl=payload.cholesterol_mg_dl,
            fasting_blood_sugar_mg_dl=payload.fasting_blood_sugar_mg_dl,
            bmi=payload.bmi,
            is_smoker=payload.is_smoker,
            risk_score_percent=risk_score,
            risk_category=category,
            model_version=predictor.version,
            top_risk_factors=[item.model_dump() for item in top_factors],
        )
        db.add(audit_entry)
        await db.commit()

        return CardiovascularRiskOutput(
            risk_score_percent=risk_score,
            risk_category=category,
            model_version=predictor.version,
            top_risk_factors=top_factors,
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failure during cardiovascular assessment.",
        ) from err


@app.get(
    "/audits/records",
    response_model=list[AssessmentAuditRecord],
    status_code=status.HTTP_200_OK,
)
async def list_audit_records(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[AssessmentAuditRecord]:
    """Retrieves paginated clinical assessment audit records for regulatory compliance."""
    stmt = (
        select(AssessmentAudit)
        .order_by(AssessmentAudit.id.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        AssessmentAuditRecord(
            id=r.id,
            correlation_id=r.correlation_id,
            timestamp=r.timestamp.isoformat() if r.timestamp else "",
            patient_age=r.patient_age,
            systolic_bp=r.systolic_bp,
            cholesterol_mg_dl=r.cholesterol_mg_dl,
            fasting_blood_sugar_mg_dl=r.fasting_blood_sugar_mg_dl,
            bmi=r.bmi,
            is_smoker=r.is_smoker,
            risk_score_percent=r.risk_score_percent,
            risk_category=r.risk_category,
            model_version=r.model_version,
            top_risk_factors=[
                FactorContribution(
                    feature=str(item["feature"]),
                    contribution_weight=float(item["contribution_weight"]),
                )
                for item in r.top_risk_factors
            ],
        )
        for r in records
    ]
