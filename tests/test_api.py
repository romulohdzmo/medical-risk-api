"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from medical_risk_api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_compute_map_success():
    payload = {"systolic": 120.0, "diastolic": 80.0}
    response = client.post("/vitals/map", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mean_arterial_pressure"] == 93.33
    assert data["status"] == "Normal"


def test_compute_map_inconsistent_pressures_returns_400():
    # Systolic cannot be lower than diastolic
    payload = {"systolic": 70.0, "diastolic": 90.0}
    response = client.post("/vitals/map", json=payload)
    assert response.status_code == 400
    assert "must exceed" in response.json()["detail"]


def test_compute_map_out_of_bounds_returns_422():
    # Exceeding schema boundaries (> 300 mmHg)
    payload = {"systolic": 350.0, "diastolic": 80.0}
    response = client.post("/vitals/map", json=payload)
    assert response.status_code == 422


def test_compute_bmi_success():
    payload = {"weight_kg": 70.0, "height_m": 1.75}
    response = client.post("/vitals/bmi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["body_mass_index"] == 22.86
    assert data["category"] == "Normal"


def test_compute_bmi_invalid_height_returns_422():
    # Height exceeds 2.8m defined in Pydantic schema
    payload = {"weight_kg": 70.0, "height_m": 3.2}
    response = client.post("/vitals/bmi", json=payload)
    assert response.status_code == 422


def test_correlation_id_and_latency_headers_present():
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert "X-Process-Time-MS" in response.headers


def test_estimate_cardiovascular_risk_low():
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


def test_estimate_cardiovascular_risk_high():
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


def test_estimate_cardiovascular_risk_invalid_age_returns_422():
    payload = {
        "age": 15,  # Below minimum clinical threshold of 18
        "systolic_bp": 120.0,
        "cholesterol_mg_dl": 180.0,
        "fasting_blood_sugar_mg_dl": 90.0,
        "bmi": 22.0,
        "is_smoker": False,
    }
    response = client.post("/risk/cardiovascular", json=payload)
    assert response.status_code == 422
