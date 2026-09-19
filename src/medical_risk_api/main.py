"""FastAPI application entrypoint for medical risk service."""

from fastapi import FastAPI, HTTPException, status

from medical_risk_api.schemas import (
    BloodPressureInput,
    BloodPressureOutput,
    BodyMassInput,
    BodyMassOutput,
)
from medical_risk_api.vitals import calculate_bmi, calculate_map

app = FastAPI(
    title="Clinical Risk Analysis API",
    description="Microservice for physiological metrics and vital sign assessment.",
    version="0.1.0",
)


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
