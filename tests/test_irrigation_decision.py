"""
SoilDepth-AI — Unit Tests for Irrigation Decision Support Advisor
Author: Senior Agronomic ML & Precision Irrigation Engineer, SoilDepth-AI
"""

import pytest
from services.irrigation_decision.advisor import IrrigationAdvisor


@pytest.fixture
def advisor():
    return IrrigationAdvisor()


def test_advisor_critical_stress_trigger(advisor):
    """Verifies that dry soil exceeding RAW triggers IRRIGATE_IMMEDIATELY."""
    # Wilting point is ~0.18, field capacity is ~0.32. Setting moisture close to WP
    dry_preds = {
        "sm_5cm": 0.19,
        "sm_10cm": 0.19,
        "sm_20cm": 0.20,
        "sm_50cm": 0.20,
    }
    advice = advisor.generate_advice(
        crop_id="CROP-SOYBEAN",
        growth_stage="mid",
        depth_predictions=dry_preds,
    )
    assert advice["decision"]["urgency"] == "CRITICAL"
    assert advice["decision"]["action"] == "IRRIGATE_IMMEDIATELY"
    assert advice["decision"]["recommended_depth_mm"] > 0
    assert advice["decision"]["recommended_volume_m3_per_ha"] == advice["decision"]["recommended_depth_mm"] * 10.0


def test_advisor_excess_moisture_waterlogging_warning(advisor):
    """Verifies that moisture above field capacity triggers waterlogging warning for Vertisols."""
    wet_preds = {
        "sm_5cm": 0.38,
        "sm_10cm": 0.38,
        "sm_20cm": 0.39,
        "sm_50cm": 0.40,
    }
    advice = advisor.generate_advice(
        crop_id="CROP-COTTON",
        growth_stage="mid",
        depth_predictions=wet_preds,
        soil_clay_pct=45.0,
    )
    assert advice["decision"]["urgency"] == "EXCESS"
    assert advice["decision"]["action"] == "DO_NOT_IRRIGATE"
    assert advice["decision"]["recommended_depth_mm"] == 0.0
    assert "asphyxiation" in advice["decision"]["rationale"].lower()


def test_advisor_rain_forecast_deferral(advisor):
    """Verifies that upcoming rain forecast defers irrigation to conserve water."""
    dry_preds = {
        "sm_5cm": 0.20,
        "sm_10cm": 0.21,
        "sm_20cm": 0.21,
        "sm_50cm": 0.22,
    }
    advice = advisor.generate_advice(
        crop_id="CROP-WHEAT",
        growth_stage="mid",
        depth_predictions=dry_preds,
        forecast_rain_mm_48h=25.0,
    )
    assert advice["decision"]["weather_deferral_applied"]
    assert advice["decision"]["action"] == "DEFER_IRRIGATION_PENDING_RAIN"


def test_advisor_uncertainty_propagation(advisor):
    """Verifies propagation of prediction RMSE to depletion uncertainty range."""
    normal_preds = {
        "sm_5cm": 0.25,
        "sm_10cm": 0.26,
        "sm_20cm": 0.27,
        "sm_50cm": 0.28,
    }
    advice = advisor.generate_advice(
        crop_id="CROP-MAIZE",
        depth_predictions=normal_preds,
        model_rmse_vwc=0.035,
    )
    unc = advice["uncertainty_analysis"]
    assert unc["model_rmse_vwc"] == 0.035
    assert unc["depletion_uncertainty_plus_minus_mm"] > 0
    assert unc["depletion_range_mm"][0] <= unc["depletion_range_mm"][1]
