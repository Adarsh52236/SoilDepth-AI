"""
SoilDepth-AI — Unit Tests for FAO-56 Root-Zone Water Balance
Author: Senior Hydrological Modeling & Agronomic Systems Engineer, SoilDepth-AI
"""

import pytest
from services.water_balance.fao56 import FAO56WaterBalance


@pytest.fixture
def wb():
    return FAO56WaterBalance()


def test_taw_calculation(wb):
    """Verifies TAW calculation according to FAO-56 Eq. 82."""
    # (0.32 - 0.18) * 0.5m * 1000 = 70.0 mm
    taw = wb.compute_taw(root_depth_m=0.5, theta_fc=0.32, theta_wp=0.18)
    assert abs(taw - 70.0) < 1e-2


def test_raw_calculation(wb):
    """Verifies RAW calculation according to FAO-56 Eq. 83."""
    # 0.50 * 70.0 mm = 35.0 mm
    raw = wb.compute_raw(taw_mm=70.0, depletion_p=0.50)
    assert abs(raw - 35.0) < 1e-2


def test_etc_calculation(wb):
    """Verifies crop evapotranspiration calculation ETc = Kc * ET0."""
    etc = wb.compute_etc(et0_mm_day=5.0, kc=1.15)
    assert abs(etc - 5.75) < 1e-2


def test_water_stress_coefficient_ks(wb):
    """Verifies Ks stress reduction coefficient according to FAO-56 Eq. 84."""
    # No stress when Dr <= RAW (e.g. Dr = 20mm <= 35mm)
    assert wb.compute_ks(depletion_dr_mm=20.0, taw_mm=70.0, raw_mm=35.0) == 1.0

    # Half stress when Dr is halfway between RAW and TAW (e.g. Dr = 52.5mm)
    ks_mid = wb.compute_ks(depletion_dr_mm=52.5, taw_mm=70.0, raw_mm=35.0)
    assert abs(ks_mid - 0.5) < 1e-2

    # Severe stress when Dr >= TAW
    assert wb.compute_ks(depletion_dr_mm=70.0, taw_mm=70.0, raw_mm=35.0) == 0.0


def test_aggregate_root_zone_vwc(wb):
    """Verifies thickness-weighted root-zone average volumetric water content."""
    depth_preds = {
        "sm_5cm": 0.20,
        "sm_10cm": 0.25,
        "sm_20cm": 0.30,
        "sm_50cm": 0.32,
    }
    avg_vwc = wb.aggregate_root_zone_vwc(depth_preds, root_depth_m=0.50)
    assert 0.20 <= avg_vwc <= 0.32


def test_daily_water_balance_step_all_10_crops(wb):
    """Verifies water balance computation for all 10 registered Maharashtra crops."""
    crop_ids = [
        "CROP-SOYBEAN", "CROP-COTTON", "CROP-RICE", "CROP-WHEAT",
        "CROP-SUGARCANE", "CROP-MAIZE", "CROP-CHICKPEA", "CROP-PIGEONPEA",
        "CROP-GROUNDNUT", "CROP-SORGHUM",
    ]
    depth_preds = {
        "sm_5cm": 0.22,
        "sm_10cm": 0.24,
        "sm_20cm": 0.27,
        "sm_50cm": 0.29,
    }

    for cid in crop_ids:
        state = wb.compute_daily_water_balance(
            crop_id=cid,
            growth_stage="mid",
            et0_mm=4.5,
            depth_predictions=depth_preds,
        )
        assert state["crop_id"] == cid
        assert state["taw_mm"] > 0
        assert state["raw_mm"] > 0
        assert 0.0 <= state["water_stress_coefficient_ks"] <= 1.0
        assert state["stress_level"] in ["CRITICAL", "WARNING", "ADEQUATE", "EXCESS"]
