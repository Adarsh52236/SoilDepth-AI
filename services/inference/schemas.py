"""
SoilDepth-AI — Production Inference Schemas & Validation Contracts
Author: Senior Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Pydantic schemas defining standardized single-day and batch inference
         requests, responses, model metadata, and physical validation diagnostics.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DepthPrediction(BaseModel):
    """Prediction object for a discrete point-sensor depth."""
    nominal_depth_cm: float = Field(..., description="Nominal sensor depth in centimeters (e.g. 5.08, 10.16, 20.32, 50.80)")
    depth_m: float = Field(..., description="Metric sensor depth in meters (e.g. 0.0508, 0.1016, 0.2032, 0.5080)")
    volumetric_soil_moisture: float = Field(..., description="Estimated volumetric soil moisture in m³/m³")
    units: str = Field(default="m³/m³", description="Volumetric water content unit")
    model_id: str = Field(..., description="Unique model identifier")
    model_file: str = Field(..., description="Serialized model artifact filename")
    model_configuration: str = Field(..., description="Model configuration category (Weather-Only or Full Multimodal)")
    feature_count: int = Field(..., description="Number of predictor features utilized by the model")
    sensor_proxy_description: str = Field(
        default="Point-sensor depth proxy; NOT a direct physical measurement or layer-integrated average.",
        description="Scientific caveat regarding point-sensor interpretation"
    )


class ValidationInfo(BaseModel):
    """Input validation, feature completeness, and physical constraint diagnostics."""
    is_valid: bool = Field(default=True, description="Whether all required input features passed validation")
    missing_features_filled_with_default: List[str] = Field(
        default_factory=list,
        description="Features absent in input that were safely populated with station physical constants"
    )
    clamped_predictions: List[str] = Field(
        default_factory=list,
        description="Depths where raw model output was clamped to physical soil moisture limits [0.0, 0.60 m³/m³]"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Validation notes or warnings (e.g. stripped ground-truth columns, LOCF staleness)"
    )


class Model1PredictionResponse(BaseModel):
    """Standardized single-day prediction response for SoilDepth-AI Model 1."""
    station_id: str = Field(default="AAMU-JTG", description="Target SCAN station identifier")
    date: str = Field(..., description="Observation / prediction calendar date in YYYY-MM-DD format")
    model_version: str = Field(default="1.0.0", description="Model 1 production inference version")
    inference_timestamp_utc: str = Field(..., description="UTC ISO 8601 execution timestamp")
    status: str = Field(default="SUCCESS", description="Inference execution status (SUCCESS, WARNING, ERROR)")
    disclaimer: str = Field(
        default=(
            "Point-sensor depth estimates (~5 cm, ~10 cm, ~20 cm, ~50 cm) derived via remote sensing "
            "and meteorological proxies. These values are point-scale proxy estimates, NOT direct physical "
            "measurements or validated vertical layer averages."
        ),
        description="Standard operational ML disclaimer"
    )
    units: str = Field(default="m³/m³", description="Volumetric water content unit")
    predictions: Dict[str, DepthPrediction] = Field(
        ...,
        description="Point-depth predictions keyed by depth ('sm_5cm', 'sm_10cm', 'sm_20cm', 'sm_50cm')"
    )
    validation_info: ValidationInfo = Field(
        default_factory=ValidationInfo,
        description="Input verification and constraint checks"
    )


class Model1BatchPredictionResponse(BaseModel):
    """Standardized multi-day batch prediction response for SoilDepth-AI Model 1."""
    station_id: str = Field(default="AAMU-JTG", description="Target SCAN station identifier")
    model_version: str = Field(default="1.0.0", description="Model 1 production inference version")
    batch_size: int = Field(..., description="Number of daily records processed")
    date_start: Optional[str] = Field(None, description="Earliest date in batch")
    date_end: Optional[str] = Field(None, description="Latest date in batch")
    status: str = Field(default="SUCCESS", description="Batch execution status")
    disclaimer: str = Field(
        default=(
            "Point-sensor depth estimates (~5 cm, ~10 cm, ~20 cm, ~50 cm) derived via remote sensing "
            "and meteorological proxies. These values are point-scale proxy estimates, NOT direct physical "
            "measurements or validated vertical layer averages."
        ),
        description="Standard operational ML disclaimer"
    )
    units: str = Field(default="m³/m³", description="Volumetric water content unit")
    results: List[Model1PredictionResponse] = Field(
        ...,
        description="Chronological sequence of daily prediction responses"
    )


class PredictionRequest(BaseModel):
    """Single-day prediction request payload."""
    station_id: Optional[str] = Field(default="AAMU-JTG", description="Target station ID (default: AAMU-JTG)")
    date: Optional[str] = Field(None, description="Calendar date YYYY-MM-DD")
    features: Dict[str, Any] = Field(
        ...,
        description="Feature dictionary containing either pre-computed predictors or daily observation variables"
    )


class BatchPredictionRequest(BaseModel):
    """Batch prediction request payload."""
    station_id: Optional[str] = Field(default="AAMU-JTG", description="Target station ID (default: AAMU-JTG)")
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of daily feature dictionaries, each containing date and required predictor variables"
    )


class ModelDetail(BaseModel):
    """Metadata describing a single depth's operational model."""
    depth_key: str
    nominal_depth_cm: float
    depth_m: float
    model_file: str
    model_configuration: str
    feature_count: int
    features_required: List[str]
    val_rmse: float
    test_rmse: float
    test_r2: float
    test_pearson_r: float
    training_station_id: str = Field(default="AAMU-JTG", description="Benchmark training station")
    training_period: str = Field(default="2015-01-01 to 2020-12-31", description="Chronological training split")
    validation_period: str = Field(default="2021-01-01 to 2021-12-31", description="Validation tuning split")
    test_period: str = Field(default="2022-01-01 to 2023-12-31", description="Independent holdout test split")
    edaphic_source_layer: str = Field(default="", description="Associated HWSD / SoilGrids depth layer")
    limitations: str = Field(
        default="Trained on single SCAN pilot station AAMU-JTG (Alabama, USA). Point-sensor depth proxy.",
        description="Scientific limitations and regional constraints"
    )


class ModelCatalogResponse(BaseModel):
    """Model 1 operational deployment catalog and metadata."""
    station_id: str
    station_lat: float
    station_lon: float
    station_elev_m: float
    model_version: str
    status: str
    ground_sensor_dependence: str
    training_station_id: str = Field(default="AAMU-JTG", description="Baseline training station")
    training_period: str = Field(default="2015-01-01 to 2020-12-31", description="Training observation window")
    target_geography: str = Field(default="AAMU-JTG, Alabama, USA (Pilot Benchmark)", description="Validated geographic domain")
    limitations: str = Field(
        default="Model 1 weights are trained exclusively on Alabama AAMU-JTG data and must not be used as Maharashtra-trained weights without regional retuning on verified local ground truth.",
        description="Governing model limitations"
    )
    models: Dict[str, ModelDetail]
