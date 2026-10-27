"""Data validation schemas for clinical API endpoints."""

from typing import Literal

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


class CardiovascularRiskInput(BaseModel):
    age: int = Field(
        ...,
        ge=18,
        le=120,
        description="Patient age in years (must be between 18 and 120).",
        examples=[55],
    )
    systolic_bp: float = Field(
        ...,
        gt=0,
        le=300.0,
        description="Systolic blood pressure in mmHg.",
        examples=[140.0],
    )
    cholesterol_mg_dl: float = Field(
        ...,
        ge=50.0,
        le=600.0,
        description="Total cholesterol in mg/dL.",
        examples=[220.0],
    )
    fasting_blood_sugar_mg_dl: float = Field(
        ...,
        ge=40.0,
        le=500.0,
        description="Fasting blood glucose in mg/dL.",
        examples=[105.0],
    )
    bmi: float = Field(
        ...,
        ge=10.0,
        le=70.0,
        description="Body mass index in kg/m^2.",
        examples=[28.4],
    )
    is_smoker: bool = Field(
        ...,
        description="Current smoking status.",
        examples=[True],
    )


class FactorContribution(BaseModel):
    feature: str = Field(..., description="Clinical risk factor name.")
    contribution_weight: float = Field(
        ..., description="Standardized linear contribution score to log-odds."
    )


class CardiovascularRiskOutput(BaseModel):
    risk_score_percent: float = Field(
        ...,
        description="Estimated 10-year cardiovascular risk probability formatted as percentage.",
        examples=[14.5],
    )
    risk_category: Literal["Low", "Borderline", "Intermediate", "High"]
    model_version: str
    top_risk_factors: list[FactorContribution] = Field(
        default_factory=list,
        description="Ranked clinical risk factors driving the probability score.",
    )
