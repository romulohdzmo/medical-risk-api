"""Cardiovascular risk model training script using clinical reference patterns."""

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "age",
    "systolic_bp",
    "cholesterol_mg_dl",
    "fasting_blood_sugar_mg_dl",
    "bmi",
    "is_smoker",
]


def generate_synthetic_cohort(samples: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Generates a physiologically plausible synthetic dataset for cardiovascular risk."""
    rng = np.random.default_rng(seed)

    age = rng.integers(20, 85, size=samples)
    systolic_bp = rng.normal(125, 18, size=samples).clip(85, 220)
    cholesterol = rng.normal(200, 35, size=samples).clip(110, 380)
    glucose = rng.normal(100, 25, size=samples).clip(60, 300)
    bmi = rng.normal(27, 5, size=samples).clip(16, 50)
    smoker = rng.choice([0, 1], size=samples, p=[0.75, 0.25])

    # Calibrated baseline ensuring healthy young profiles sit in Low risk (<5%)
    z = (
        -10.5
        + 0.07 * age
        + 0.02 * systolic_bp
        + 0.008 * cholesterol
        + 0.01 * glucose
        + 0.04 * bmi
        + 0.8 * smoker
    )
    prob = 1 / (1 + np.exp(-z))
    target = rng.binomial(1, prob)

    df = pd.DataFrame(
        {
            "age": age,
            "systolic_bp": systolic_bp,
            "cholesterol_mg_dl": cholesterol,
            "fasting_blood_sugar_mg_dl": glucose,
            "bmi": bmi,
            "is_smoker": smoker,
            "target": target,
        }
    )
    return df


def train_and_export_model() -> None:
    """Trains a calibrated scikit-learn pipeline and serializes it to disk."""
    df = generate_synthetic_cohort()
    x = df[FEATURE_NAMES]
    y = df["target"]

    base_pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(C=1.0, random_state=42),
            ),
        ]
    )

    calibrated_pipeline = CalibratedClassifierCV(
        estimator=base_pipe,
        method="sigmoid",
        cv=5,
    )
    calibrated_pipeline.fit(x, y)

    output_path = "src/medical_risk_api/models/cardiovascular_model.joblib"
    joblib.dump(
        {
            "pipeline": calibrated_pipeline,
            "feature_names": FEATURE_NAMES,
            "version": "1.0.0",
        },
        output_path,
    )
    print(f"Model artifact successfully saved to: {output_path}")


if __name__ == "__main__":
    train_and_export_model()
