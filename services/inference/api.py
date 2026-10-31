"""
SoilDepth-AI — Model 1 Production FastAPI Service
Author: Senior Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: HTTP REST API serving Model 1 discrete point-sensor soil moisture estimation.
         Provides /health, /catalog, /predict (single-day), and /predict/batch endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse

from services.inference.schemas import (
    Model1PredictionResponse,
    Model1BatchPredictionResponse,
    PredictionRequest,
    BatchPredictionRequest,
    ModelCatalogResponse,
)
from services.inference.predictor import Model1Predictor


app = FastAPI(
    title="SoilDepth-AI — Model 1 Inference Service",
    description=(
        "Production inference service for discrete point-sensor root-zone soil moisture estimation "
        "at pilot station AAMU-JTG using 100% ground-sensor-independent models."
    ),
    version="1.0.0",
)

# Lazy singleton instance
_predictor: Optional[Model1Predictor] = None


def get_predictor() -> Model1Predictor:
    """Provides a singleton instance of Model1Predictor."""
    global _predictor
    if _predictor is None:
        _predictor = Model1Predictor()
    return _predictor


@app.get("/", tags=["System"])
def root():
    """API Root with service summary and documentation links."""
    return {
        "service": "SoilDepth-AI Model 1 Inference Service",
        "station_id": "AAMU-JTG",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "description": "Ground-sensor-independent point-depth soil moisture estimation (5, 10, 20, 50 cm)",
        "endpoints": {
            "health": "/health",
            "catalog": "/catalog",
            "predict_single": "/predict (POST)",
            "predict_batch": "/predict/batch (POST)",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["System"])
def health_check():
    """Confirms inference service readiness and model loading status."""
    try:
        predictor = get_predictor()
        loaded_models = list(predictor.models.keys())
        return {
            "status": "HEALTHY",
            "station_id": predictor.station_id,
            "models_loaded_count": len(loaded_models),
            "models_loaded": loaded_models,
            "ground_sensor_dependent": False,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Inference service unhealthy: {str(e)}",
        )


@app.get("/catalog", response_model=ModelCatalogResponse, tags=["Metadata"])
def get_model_catalog():
    """Returns the operational catalog describing all four active models, depths, and feature requirements."""
    predictor = get_predictor()
    return predictor.get_model_catalog()


@app.post("/predict", response_model=Model1PredictionResponse, tags=["Inference"])
def predict_single_day(payload: PredictionRequest):
    """
    Executes single-day point-depth soil moisture inference across all 4 sensor depths.
    Accepts daily weather and remote-sensing features.
    """
    predictor = get_predictor()
    try:
        response = predictor.predict_single(data=payload.features, date_str=payload.date)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inference failed: {str(e)}",
        )


@app.post("/predict/batch", response_model=Model1BatchPredictionResponse, tags=["Inference"])
def predict_batch_days(payload: BatchPredictionRequest):
    """
    Executes multi-day batch inference across a sequence of daily feature dictionaries.
    """
    predictor = get_predictor()
    try:
        response = predictor.predict_batch(records=payload.records)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch inference failed: {str(e)}",
        )

