"""Clinical vitals analysis module with strict static typing."""

from collections.abc import Callable
from typing import Literal

# 1. Literal types (finite set of clinical states)
MAPStatus = Literal["Hypotension", "Normal", "Hypertension"]
BMICategory = Literal["Underweight", "Normal", "Overweight", "Obesity"]

# 2. Callable alias for metric adjustment functions
MetricAdjuster = Callable[[float, float], float]


def round_metric[T: (int, float)](value: T, decimals: int = 2) -> float:
    """Rounds numeric value ensuring int/float compatibility."""
    return round(float(value), decimals)


def calculate_map(
    systolic: float,
    diastolic: float,
) -> tuple[float, MAPStatus]:
    """
    Calculates Mean Arterial Pressure (MAP).
    Formula: MAP = (SBP + 2 * DBP) / 3
    """
    if systolic <= 0 or diastolic <= 0:
        raise ValueError("Blood pressure values must be greater than zero.")
    if systolic <= diastolic:
        raise ValueError("Systolic blood pressure must exceed diastolic.")

    map_val = round_metric((systolic + 2 * diastolic) / 3)

    if map_val < 65.0:
        status: MAPStatus = "Hypotension"
    elif map_val <= 100.0:
        status = "Normal"
    else:
        status = "Hypertension"

    return map_val, status


def calculate_bmi(
    weight_kg: float,
    height_m: float,
    adjuster: MetricAdjuster | None = None,
) -> tuple[float, BMICategory]:
    """
    Calculates Body Mass Index (BMI).
    Formula: BMI = weight / (height^2)
    """
    if weight_kg <= 0 or height_m <= 0:
        raise ValueError("Weight and height must be strictly positive.")
    if height_m > 2.8:
        raise ValueError("Provided height exceeds physiological bounds.")

    raw_bmi = weight_kg / (height_m**2)

    if adjuster is not None:
        final_bmi = adjuster(weight_kg, height_m)
    else:
        final_bmi = raw_bmi

    bmi = round_metric(final_bmi)

    if bmi < 18.5:
        category: BMICategory = "Underweight"
    elif bmi < 25.0:
        category = "Normal"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obesity"

    return bmi, category
