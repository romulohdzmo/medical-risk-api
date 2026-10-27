"""Integration tests for FastAPI application endpoints."""

import pytest
from fastapi.testclient import TestClient

from medical_risk_api.main import app


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient managing the application lifespan."""
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_compute_map_success(client):
    payload = {"systolic": 120.0, "diastolic": 80.0}
    response = client.post("/vitals/map", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mean_arterial_pressure"] == 93.33
    assert data["status"] == "Normal"


def test_compute_map_inconsistent_pressures_returns_400(client):
    payload = {"systolic": 80.0, "diastolic": 120.0}
    response = client.post("/vitals/map", json=payload)
    assert response.status_code == 400


def test_compute_map_out_of_bounds_returns_422(client):
    payload = {"systolic": 350.0, "diastolic": 80.0}
    response = client.post("/vitals/map", json=payload)
    assert response.status_code == 422


def test_compute_bmi_success(client):
    payload = {"weight_kg": 70.0, "height_m": 1.75}
    response = client.post("/vitals/bmi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["body_mass_index"] == 22.86
    assert data["category"] == "Normal"


def test_compute_bmi_invalid_height_returns_422(client):
    payload = {"weight_kg": 70.0, "height_m": 0.0}
    response = client.post("/vitals/bmi", json=payload)
    assert response.status_code == 422


def test_correlation_id_and_latency_headers_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert "X-Process-Time-MS" in response.headers


def test_estimate_cardiovascular_risk_low(client):
    payload = {
        "age": 25,
        "systolic_bp": 110.0,
        "cholesterol_mg_dl": 160.0,
        "fasting_blood_sugar_mg_dl": 85.0,
        "bmi": 21.5,
        "is_smoker": False,
    }
    response = client.post("/risk/cardiovascular", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_category"] == "Low"
    assert data["model_version"] == "1.0.0"
    assert data["risk_score_percent"] < 5.0


def test_estimate_cardiovascular_risk_high(client):
    payload = {
        "age": 75,
        "systolic_bp": 175.0,
        "cholesterol_mg_dl": 280.0,
        "fasting_blood_sugar_mg_dl": 160.0,
        "bmi": 34.0,
        "is_smoker": True,
    }
    response = client.post("/risk/cardiovascular", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_category"] == "High"
    assert data["risk_score_percent"] >= 20.0


def test_estimate_cardiovascular_risk_invalid_age_returns_422(client):
    payload = {
        "age": 15,
        "systolic_bp": 120.0,
        "cholesterol_mg_dl": 180.0,
        "fasting_blood_sugar_mg_dl": 90.0,
        "bmi": 22.0,
        "is_smoker": False,
    }
    response = client.post("/risk/cardiovascular", json=payload)
    assert response.status_code == 422


def test_estimate_cardiovascular_risk_explains_top_factors(client):
    payload = {
        "age": 62,
        "systolic_bp": 160.0,
        "cholesterol_mg_dl": 250.0,
        "fasting_blood_sugar_mg_dl": 110.0,
        "bmi": 30.0,
        "is_smoker": True,
    }
    response = client.post("/risk/cardiovascular", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "top_risk_factors" in data
    assert len(data["top_risk_factors"]) == 3
    weights = [item["contribution_weight"] for item in data["top_risk_factors"]]
    assert weights == sorted(weights, reverse=True)


def test_audit_records_endpoint_retrieves_assessments(client):
    payload = {
        "age": 52,
        "systolic_bp": 142.0,
        "cholesterol_mg_dl": 215.0,
        "fasting_blood_sugar_mg_dl": 105.0,
        "bmi": 27.8,
        "is_smoker": False,
    }
    post_res = client.post("/risk/cardiovascular", json=payload)
    assert post_res.status_code == 200

    audit_res = client.get("/audits/records?limit=5")
    assert audit_res.status_code == 200
    records = audit_res.json()
    assert len(records) >= 1
    latest = records[0]
    assert latest["patient_age"] == 52
    assert latest["systolic_bp"] == 142.0
    assert "top_risk_factors" in latest
