"""
SoilDepth-AI — FAO-56 Root-Zone Water Balance Engine
Author: Senior Hydrological Modeling & Agronomic Systems Engineer, SoilDepth-AI
Purpose: Implements standard FAO Irrigation and Drainage Paper No. 56 (FAO-56)
         daily root-zone soil water balance, calculating:
         - Total Available Water (TAW)
         - Readily Available Water (RAW)
         - Crop Evapotranspiration (ETc = Kc * ET0)
         - Water Stress Coefficient (Ks)
         - Root-Zone Depletion (Dr)
         - Net Irrigation Requirement (I_req)
         Integrated with Maharashtra multi-crop registry (10 major regional crops).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CROP_REGISTRY = REPO_ROOT / "dataset" / "Maharashtra" / "metadata" / "crop_registry.csv"

# Standard Vertisol / Black Soil physical hydro-pedological defaults for Maharashtra
DEFAULT_FIELD_CAPACITY = 0.320   # m3/m3
DEFAULT_WILTING_POINT = 0.180    # m3/m3
DEFAULT_SATURATION = 0.480       # m3/m3


class FAO56WaterBalance:
    """
    Standard FAO-56 daily root-zone soil water balance computation engine.
    """

    def __init__(
        self,
        crop_registry_path: Optional[Path] = None,
        default_fc: float = DEFAULT_FIELD_CAPACITY,
        default_wp: float = DEFAULT_WILTING_POINT,
    ):
        self.crop_registry_path = crop_registry_path or DEFAULT_CROP_REGISTRY
        self.default_fc = default_fc
        self.default_wp = default_wp
        self.crop_registry = self._load_crop_registry()

    def _load_crop_registry(self) -> Dict[str, Dict[str, Any]]:
        """Loads and parses Maharashtra crop agronomic parameters from registry."""
        registry: Dict[str, Dict[str, Any]] = {}
        if self.crop_registry_path.exists():
            df = pd.read_csv(self.crop_registry_path)
            for _, r in df.iterrows():
                cid = str(r["crop_id"]).strip().upper()
                # Parse root depth
                root_str = str(r.get("effective_root_depth_cm", "40-60")).replace("cm", "").strip()
                try:
                    if "-" in root_str:
                        parts = root_str.split("-")
                        zr_cm = (float(parts[0]) + float(parts[1])) / 2.0
                    else:
                        zr_cm = float(root_str)
                except ValueError:
                    zr_cm = 50.0

                registry[cid] = {
                    "crop_name": str(r.get("crop_name", "")),
                    "botanical_name": str(r.get("botanical_name", "")),
                    "dominant_season": str(r.get("dominant_season", "")),
                    "effective_root_depth_m": zr_cm / 100.0,
                    "initial_kc": float(r.get("initial_kc", 0.40)),
                    "mid_season_kc": float(r.get("mid_season_kc", 1.15)),
                    "end_season_kc": float(r.get("end_season_kc", 0.50)),
                    "allowable_depletion_p": float(r.get("allowable_depletion_p", 0.50)),
                    "critical_stages": str(r.get("critical_growth_stages", "")),
                }

        # Ensure fallback defaults if file missing or incomplete
        if not registry:
            registry["CROP-SOYBEAN"] = {
                "crop_name": "Soybean",
                "effective_root_depth_m": 0.40,
                "initial_kc": 0.40,
                "mid_season_kc": 1.15,
                "end_season_kc": 0.50,
                "allowable_depletion_p": 0.50,
            }
        return registry

    def compute_taw(
        self,
        root_depth_m: float,
        theta_fc: Optional[float] = None,
        theta_wp: Optional[float] = None,
    ) -> float:
        """
        Total Available Water (TAW) in the root zone (FAO-56 Eq. 82):
        TAW = 1000 * (theta_FC - theta_WP) * Zr [mm]
        """
        fc = theta_fc if theta_fc is not None else self.default_fc
        wp = theta_wp if theta_wp is not None else self.default_wp
        if fc <= wp:
            raise ValueError(f"Field capacity ({fc}) must be greater than wilting point ({wp})")
        return round(1000.0 * (fc - wp) * root_depth_m, 2)

    def compute_raw(self, taw_mm: float, depletion_p: float) -> float:
        """
        Readily Available Water (RAW) without moisture stress (FAO-56 Eq. 83):
        RAW = p * TAW [mm]
        """
        p_clamped = max(0.10, min(0.85, depletion_p))
        return round(p_clamped * taw_mm, 2)

    def compute_etc(self, et0_mm_day: float, kc: float) -> float:
        """
        Potential Crop Evapotranspiration (FAO-56 Eq. 56):
        ETc = Kc * ET0 [mm/day]
        """
        return round(max(0.0, et0_mm_day * kc), 2)

    def compute_ks(self, depletion_dr_mm: float, taw_mm: float, raw_mm: float) -> float:
        """
        Water Stress Reduction Coefficient Ks (FAO-56 Eq. 84):
        Ks = 1.0 (if Dr <= RAW)
        Ks = (TAW - Dr) / (TAW - RAW) (if Dr > RAW)
        """
        if depletion_dr_mm <= raw_mm:
            return 1.0
        if depletion_dr_mm >= taw_mm:
            return 0.0
        ks = (taw_mm - depletion_dr_mm) / max(taw_mm - raw_mm, 0.01)
        return round(float(np.clip(ks, 0.0, 1.0)), 3)

    def aggregate_root_zone_vwc(
        self,
        depth_predictions: Dict[str, float],
        root_depth_m: float = 0.50,
    ) -> float:
        """
        Computes layer-thickness-weighted root-zone average volumetric water content (m3/m3)
        from discrete depth predictions (e.g. 5, 10, 20, 50 cm).
        """
        depth_map: List[Tuple[float, float, str]] = [
            (0.0, 0.075, "sm_5cm"),     # 0 to 7.5 cm (centered at ~5cm)
            (0.075, 0.15, "sm_10cm"),   # 7.5 to 15 cm (centered at ~10cm)
            (0.15, 0.35, "sm_20cm"),    # 15 to 35 cm (centered at ~20cm)
            (0.35, 1.00, "sm_50cm"),    # 35 to 100 cm (centered at ~50cm)
        ]

        total_weight = 0.0
        weighted_sum = 0.0

        for z_top, z_bot, key in depth_map:
            if z_top >= root_depth_m:
                continue
            effective_bot = min(z_bot, root_depth_m)
            thickness = effective_bot - z_top
            if thickness <= 0:
                continue

            vwc_val = depth_predictions.get(key)
            if vwc_val is not None and np.isfinite(vwc_val):
                weighted_sum += thickness * vwc_val
                total_weight += thickness

        if total_weight > 0:
            return round(weighted_sum / total_weight, 5)

        # Fallback to mean of all valid values
        valid_vals = [v for v in depth_predictions.values() if v is not None and np.isfinite(v)]
        return round(float(np.mean(valid_vals)), 5) if valid_vals else self.default_fc

    def compute_daily_water_balance(
        self,
        crop_id: str,
        growth_stage: str = "mid",
        et0_mm: float = 4.5,
        precip_mm: float = 0.0,
        irrigation_mm: float = 0.0,
        depth_predictions: Optional[Dict[str, float]] = None,
        previous_depletion_mm: Optional[float] = None,
        theta_fc: Optional[float] = None,
        theta_wp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Executes a single-day FAO-56 root-zone water balance step.
        """
        cid = crop_id.upper()
        if cid not in self.crop_registry:
            # Fallback to first available or standard crop
            crop_meta = list(self.crop_registry.values())[0]
        else:
            crop_meta = self.crop_registry[cid]

        fc = theta_fc if theta_fc is not None else self.default_fc
        wp = theta_wp if theta_wp is not None else self.default_wp
        zr_m = crop_meta["effective_root_depth_m"]

        # Select stage Kc
        if growth_stage.lower() in ["initial", "ini", "early"]:
            kc = crop_meta["initial_kc"]
        elif growth_stage.lower() in ["end", "late", "maturity"]:
            kc = crop_meta["end_season_kc"]
        else:
            kc = crop_meta["mid_season_kc"]

        p = crop_meta["allowable_depletion_p"]
        taw_mm = self.compute_taw(root_depth_m=zr_m, theta_fc=fc, theta_wp=wp)
        raw_mm = self.compute_raw(taw_mm=taw_mm, depletion_p=p)
        etc_pot = self.compute_etc(et0_mm_day=et0_mm, kc=kc)

        # Estimate depletion directly from root-zone VWC if model predictions provided
        if depth_predictions:
            root_vwc = self.aggregate_root_zone_vwc(depth_predictions, root_depth_m=zr_m)
            # Depletion Dr = 1000 * (theta_FC - theta_root) * Zr
            dr_from_vwc = 1000.0 * (fc - root_vwc) * zr_m
            dr_current = float(np.clip(dr_from_vwc, 0.0, taw_mm))
        elif previous_depletion_mm is not None:
            # Step forward via precipitation, irrigation, and ET
            peff = max(0.0, precip_mm - 0.2 * etc_pot)
            dr_prev = previous_depletion_mm
            ks_prev = self.compute_ks(dr_prev, taw_mm, raw_mm)
            etc_actual = ks_prev * etc_pot
            dr_current = float(np.clip(dr_prev - peff - irrigation_mm + etc_actual, 0.0, taw_mm))
            root_vwc = fc - (dr_current / (1000.0 * zr_m))
        else:
            # Default to mid-depletion (50% RAW)
            dr_current = 0.5 * raw_mm
            root_vwc = fc - (dr_current / (1000.0 * zr_m))

        ks = self.compute_ks(dr_current, taw_mm, raw_mm)
        etc_actual = round(ks * etc_pot, 2)
        depletion_pct = round(100.0 * dr_current / max(taw_mm, 1e-4), 1)

        # Net irrigation requirement to replenish root zone to field capacity
        if dr_current >= raw_mm:
            irrigation_req_mm = round(dr_current, 1)
            stress_level = "CRITICAL"
        elif dr_current >= 0.8 * raw_mm:
            irrigation_req_mm = round(dr_current, 1)
            stress_level = "WARNING"
        elif dr_current <= 0.1 * raw_mm:
            irrigation_req_mm = 0.0
            stress_level = "EXCESS"
        else:
            irrigation_req_mm = 0.0
            stress_level = "ADEQUATE"

        return {
            "crop_id": cid,
            "crop_name": crop_meta.get("crop_name", cid),
            "growth_stage": growth_stage,
            "kc": kc,
            "root_depth_m": zr_m,
            "field_capacity_vwc": fc,
            "wilting_point_vwc": wp,
            "root_zone_vwc": round(root_vwc, 5),
            "taw_mm": taw_mm,
            "raw_mm": raw_mm,
            "allowable_depletion_fraction_p": p,
            "depletion_dr_mm": round(dr_current, 2),
            "depletion_pct_taw": depletion_pct,
            "water_stress_coefficient_ks": ks,
            "potential_etc_mm": etc_pot,
            "actual_etc_mm": etc_actual,
            "irrigation_requirement_mm": irrigation_req_mm,
            "stress_level": stress_level,
        }
