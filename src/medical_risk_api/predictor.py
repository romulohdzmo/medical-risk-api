"""Cardiovascular risk inference engine and probability calibrator."""

from pathlib import Path
from typing import Any, Literal

import joblib
import pandas as pd

from medical_risk_api.schemas import CardiovascularRiskInput, FactorContribution

RiskCategory = Literal["Low", "Borderline", "Intermediate", "High"]

MODEL_PATH = Path(__file__).resolve().parent / "models" / "cardiovascular_model.joblib"


class CardiovascularRiskPredictor:
    """Encapsulates model loading, clinical risk score prediction, and feature explainability."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained model artifact not found at: {model_path}. "
                "Run `medical_risk_api.models.train` first."
            )
        artifact: dict[str, Any] = joblib.load(model_path)
        self.calibrated_pipeline = artifact["pipeline"]
        self.feature_names: list[str] = artifact["feature_names"]
        self.version: str = artifact["version"]

        # Extract underlying base estimator for linear feature contributions
        calibrated_classifier = self.calibrated_pipeline.calibrated_classifiers_[0]
        self.base_pipeline = calibrated_classifier.estimator
        self.scaler = self.base_pipeline.named_steps["scaler"]
        self.classifier = self.base_pipeline.named_steps["classifier"]

    def _compute_top_factors(
        self, df_features: pd.DataFrame
    ) -> list[FactorContribution]:
        """Calculates standardized feature contributions to linear log-odds."""
        x_scaled = self.scaler.transform(df_features)
        coefficients = self.classifier.coef_[0]

        contributions = x_scaled[0] * coefficients
        factor_items = [
            FactorContribution(
                feature=name,
                contribution_weight=round(float(weight), 3),
            )
            for name, weight in zip(self.feature_names, contributions, strict=True)
        ]

        factor_items.sort(key=lambda x: x.contribution_weight, reverse=True)
        return factor_items[:3]

    def predict_risk(
        self, patient: CardiovascularRiskInput
    ) -> tuple[float, RiskCategory, list[FactorContribution]]:
        """Calculates 10-year calibrated cardiovascular risk percentage, tier, and top drivers."""
        patient_data = {
            "age": [patient.age],
            "systolic_bp": [patient.systolic_bp],
            "cholesterol_mg_dl": [patient.cholesterol_mg_dl],
            "fasting_blood_sugar_mg_dl": [patient.fasting_blood_sugar_mg_dl],
            "bmi": [patient.bmi],
            "is_smoker": [1 if patient.is_smoker else 0],
        }
        df_features = pd.DataFrame(patient_data, columns=self.feature_names)

        risk_probability = float(
            self.calibrated_pipeline.predict_proba(df_features)[0][1]
        )
        risk_percent = round(risk_probability * 100, 2)

        if risk_percent < 5.0:
            category: RiskCategory = "Low"
        elif risk_percent < 7.5:
            category = "Borderline"
        elif risk_percent < 20.0:
            category = "Intermediate"
        else:
            category = "High"

        top_factors = self._compute_top_factors(df_features)
        return risk_percent, category, top_factors


# Singleton instance for dependency reuse
predictor = CardiovascularRiskPredictor()
