import pytest

from medical_risk_api.vitals import calculate_bmi, calculate_map


def test_calculate_map_normal():
    map_val, status = calculate_map(120.0, 80.0)
    assert map_val == 93.33
    assert status == "Normal"


def test_calculate_map_hypotension():
    map_val, status = calculate_map(85.0, 50.0)
    assert map_val == 61.67
    assert status == "Hypotension"


def test_calculate_map_invalid_pressures():
    with pytest.raises(ValueError, match="must exceed"):
        calculate_map(80.0, 120.0)


def test_calculate_bmi_classification():
    bmi, category = calculate_bmi(70.0, 1.75)
    assert bmi == 22.86
    assert category == "Normal"


def test_calculate_bmi_invalid_height():
    with pytest.raises(ValueError, match="physiological bounds"):
        calculate_bmi(70.0, 3.0)
