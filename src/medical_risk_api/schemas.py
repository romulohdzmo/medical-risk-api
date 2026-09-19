"""Data validation schemas for clinical API endpoints."""

from pydantic import BaseModel, Field

from medical_risk_api.vitals import BMICategory, MAPStatus


class BloodPressureInput(BaseModel):
    systolic: float = Field(
        ...,
        gt=0,
        le=300.0,
        description="Systolic blood pressure in mmHg (must be > 0 and <= 300).",
        examples=[120.0],
    )
    diastolic: float = Field(
        ...,
        gt=0,
        le=200.0,
        description="Diastolic blood pressure in mmHg (must be > 0 and <= 200).",
        examples=[80.0],
    )


class BloodPressureOutput(BaseModel):
    mean_arterial_pressure: float
    status: MAPStatus


class BodyMassInput(BaseModel):
    weight_kg: float = Field(
        ...,
        gt=0,
        le=500.0,
        description="Patient weight in kilograms.",
        examples=[70.0],
    )
    height_m: float = Field(
        ...,
        gt=0,
        le=2.8,
        description="Patient height in meters.",
        examples=[1.75],
    )


class BodyMassOutput(BaseModel):
    body_mass_index: float
    category: BMICategory
