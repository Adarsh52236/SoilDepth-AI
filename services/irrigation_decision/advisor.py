"""
SoilDepth-AI — Agronomic Irrigation Decision Support Advisor
Author: Senior Agronomic ML & Precision Irrigation Engineer, SoilDepth-AI
Purpose: Translates AI root-zone soil moisture predictions and FAO-56 depletion
         into actionable, agronomically sound irrigation schedules for Maharashtra crops.
         Features:
         - Vertisol waterlogging and aeration risk mitigation
         - Rainfall forecast integration (irrigation deferral)
         - Uncertainty bounds propagation (+/- model RMSE)
         - Metric conversion (mm depth to m3/ha volume)
         - Critical growth stage protection
"""

from typing import Dict, Any, List, Optional
import numpy as np

from services.water_balance.fao56 import FAO56WaterBalance


class IrrigationAdvisor:
    """
    Expert precision irrigation advisory engine for Maharashtra crops.
    """

    def __init__(self, water_balance_engine: Optional[FAO56WaterBalance] = None):
        self.wb = water_balance_engine or FAO56WaterBalance()

    def generate_advice(
        self,
        crop_id: str,
        growth_stage: str = "mid",
        depth_predictions: Optional[Dict[str, float]] = None,
        et0_mm: float = 4.5,
        precip_mm: float = 0.0,
        forecast_rain_mm_48h: float = 0.0,
        soil_clay_pct: float = 42.0,
        model_rmse_vwc: float = 0.035,
    ) -> Dict[str, Any]:
        """
        Generates actionable irrigation decision support based on current root-zone moisture state.
        """
        # Run FAO-56 daily water balance step
        wb_state = self.wb.compute_daily_water_balance(
            crop_id=crop_id,
            growth_stage=growth_stage,
            et0_mm=et0_mm,
            precip_mm=precip_mm,
            depth_predictions=depth_predictions,
        )

        dr_mm = wb_state["depletion_dr_mm"]
        raw_mm = wb_state["raw_mm"]
        taw_mm = wb_state["taw_mm"]
        zr_m = wb_state["root_depth_m"]
        root_vwc = wb_state["root_zone_vwc"]
        fc = wb_state["field_capacity_vwc"]

        # 1. Uncertainty bounds based on prediction RMSE
        # delta_Dr = 1000 * RMSE * Zr
        uncertainty_dr_mm = round(1000.0 * model_rmse_vwc * zr_m, 1)
        dr_lower = max(0.0, dr_mm - uncertainty_dr_mm)
        dr_upper = min(taw_mm, dr_mm + uncertainty_dr_mm)

        # 2. Decision Logic
        action: str
        urgency: str
        rationale: str
        recommended_mm = 0.0

        if root_vwc > fc:
            urgency = "EXCESS"
            action = "DO_NOT_IRRIGATE"
            rationale = (
                f"Soil moisture ({root_vwc:.3f} m³/m³) exceeds field capacity ({fc:.3f} m³/m³). "
                f"High-clay Vertisols ({soil_clay_pct}% clay) are at severe risk of root asphyxiation "
                "and fungal pathogen propagation. Ensure field surface drainage is clear."
            )
        elif dr_mm >= raw_mm:
            urgency = "CRITICAL"
            action = "IRRIGATE_IMMEDIATELY"
            recommended_mm = round(dr_mm, 1)
            rationale = (
                f"Root-zone depletion ({dr_mm:.1f} mm) has exceeded Readily Available Water ({raw_mm:.1f} mm). "
                f"Crop is experiencing moisture stress (Ks = {wb_state['water_stress_coefficient_ks']}). "
                "Yield loss is imminent unless water is applied."
            )
        elif dr_mm >= 0.80 * raw_mm:
            urgency = "WARNING"
            action = "SCHEDULE_IRRIGATION_24_48H"
            recommended_mm = round(dr_mm, 1)
            rationale = (
                f"Root-zone moisture is approaching stress threshold (Depletion: {dr_mm:.1f} mm / RAW: {raw_mm:.1f} mm). "
                "Prepare irrigation system and schedule application within the next 24–48 hours."
            )
        elif dr_mm <= 0.20 * raw_mm:
            urgency = "OPTIMAL"
            action = "DO_NOT_IRRIGATE"
            rationale = "Soil moisture profile is nearly full. Crop has abundant available moisture."
        else:
            urgency = "ADEQUATE"
            action = "MAINTAIN_MONITORING"
            rationale = (
                f"Soil moisture is in the optimal vegetative comfort zone (Depletion: {dr_mm:.1f} mm, "
                f"RAW: {raw_mm:.1f} mm). No irrigation required today."
            )

        # 3. Forecast Adjustment (Deferral Rule)
        weather_deferral_applied = False
        if forecast_rain_mm_48h >= 10.0 and action in ["IRRIGATE_IMMEDIATELY", "SCHEDULE_IRRIGATION_24_48H"]:
            weather_deferral_applied = True
            action = "DEFER_IRRIGATION_PENDING_RAIN"
            rationale += (
                f" Rain event ({forecast_rain_mm_48h:.1f} mm) is forecast within 48 hours. "
                "Irrigation deferred to prevent excess drainage and soil waterlogging."
            )
            recommended_mm = max(0.0, recommended_mm - forecast_rain_mm_48h)

        # 4. Volume in m3/ha (1 mm depth over 1 ha = 10 m3)
        volume_m3_ha = round(recommended_mm * 10.0, 1)

        return {
            "crop_id": wb_state["crop_id"],
            "crop_name": wb_state["crop_name"],
            "growth_stage": growth_stage,
            "decision": {
                "action": action,
                "urgency": urgency,
                "recommended_depth_mm": recommended_mm,
                "recommended_volume_m3_per_ha": volume_m3_ha,
                "rationale": rationale,
                "weather_deferral_applied": weather_deferral_applied,
            },
            "root_zone_diagnostics": {
                "root_depth_m": zr_m,
                "root_zone_vwc": root_vwc,
                "field_capacity_vwc": fc,
                "wilting_point_vwc": wb_state["wilting_point_vwc"],
                "taw_mm": taw_mm,
                "raw_mm": raw_mm,
                "depletion_mm": dr_mm,
                "depletion_pct_taw": wb_state["depletion_pct_taw"],
                "water_stress_ks": wb_state["water_stress_coefficient_ks"],
            },
            "uncertainty_analysis": {
                "model_rmse_vwc": model_rmse_vwc,
                "depletion_uncertainty_plus_minus_mm": uncertainty_dr_mm,
                "depletion_range_mm": [round(dr_lower, 1), round(dr_upper, 1)],
            },
            "soil_characteristics": {
                "soil_clay_pct": soil_clay_pct,
                "soil_type_classification": "Deep Vertisol / Heavy Black Soil",
                "waterlogging_sensitivity": "HIGH" if soil_clay_pct > 35.0 else "MODERATE",
            },
            "scientific_disclaimer": (
                "Advisory generated via SoilDepth-AI satellite-derived root-zone soil moisture intelligence. "
                "Estimates represent point/profile proxies and must be verified against field observations, "
                "local soil texture, and canal/borewell availability prior to operational execution."
            ),
        }
