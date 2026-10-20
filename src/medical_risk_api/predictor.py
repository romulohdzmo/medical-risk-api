"""Cardiovascular risk inference engine and probability calibrator."""

from pathlib import Path
from typing import Any, Literal

import joblib
import pandas as pd

from medical_risk_api.schemas import CardiovascularRiskInput

RiskCategory = Literal["Low", "Borderline", "Intermediate", "High"]

MODEL_PATH = Path(__file__).resolve().parent / "models" / "cardiovascular_model.joblib"


class CardiovascularRiskPredictor:
    """Encapsulates model loading and clinical risk score prediction."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained model artifact not found at: {model_path}. "
                "Run `medical_risk_api.models.train` first."
            )
        artifact: dict[str, Any] = joblib.load(model_path)
        self.pipeline = artifact["pipeline"]
        self.feature_names: list[str] = artifact["feature_names"]
        self.version: str = artifact["version"]

    def predict_risk(
        self, patient: CardiovascularRiskInput
    ) -> tuple[float, RiskCategory]:
        """Calculates 10-year calibrated cardiovascular risk percentage and risk tier."""
        patient_data = {
            "age": [patient.age],
            "systolic_bp": [patient.systolic_bp],
            "cholesterol_mg_dl": [patient.cholesterol_mg_dl],
            "fasting_blood_sugar_mg_dl": [patient.fasting_blood_sugar_mg_dl],
            "bmi": [patient.bmi],
            "is_smoker": [1 if patient.is_smoker else 0],
        }
        df_features = pd.DataFrame(patient_data, columns=self.feature_names)

        # CalibratedClassifierCV returns probabilities for [class_0, class_1]
        risk_probability = float(self.pipeline.predict_proba(df_features)[0][1])
        risk_percent = round(risk_probability * 100, 2)

        if risk_percent < 5.0:
            category: RiskCategory = "Low"
        elif risk_percent < 7.5:
            category = "Borderline"
        elif risk_percent < 20.0:
            category = "Intermediate"
        else:
            category = "High"

        return risk_percent, category


# Singleton instance for dependency reuse
predictor = CardiovascularRiskPredictor()
