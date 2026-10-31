"""
SoilDepth-AI — Model 1 Production Inference Engine
Author: Senior Data Engineer & ML Pipeline Developer, SoilDepth-AI
"""

from services.inference.schemas import (
    DepthPrediction,
    ValidationInfo,
    Model1PredictionResponse,
    Model1BatchPredictionResponse,
    PredictionRequest,
    BatchPredictionRequest,
)
from services.inference.predictor import Model1Predictor

__all__ = [
    "Model1Predictor",
    "DepthPrediction",
    "ValidationInfo",
    "Model1PredictionResponse",
    "Model1BatchPredictionResponse",
    "PredictionRequest",
    "BatchPredictionRequest",
]

