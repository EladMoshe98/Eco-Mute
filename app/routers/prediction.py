from pathlib import Path
import pandas as pd
import joblib
from fastapi import APIRouter, HTTPException

from app.data_transfer_schemas.schemas import TripInput
from app.logger import get_logger

router = APIRouter(prefix="/predict", tags=["predict"])

logger = get_logger()

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "ride_time_model.pkl"
model = None

if MODEL_PATH.exists():
    try:
        model = joblib.load(MODEL_PATH)
        logger.info(f"ML model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Failed to load model from {MODEL_PATH}: {e}")
else:
    logger.warning(f"Model file not found at {MODEL_PATH}. Run: python -m app.ml.train")


@router.post("/duration")
def predict_duration(input: TripInput):
    logger.info(f"POST /predict/duration - distance_km={input.distance_km}, battery_level={input.battery_level}")

    if not model:
        logger.error("Prediction requested but model is not loaded")
        raise HTTPException(status_code=503, detail="Model not available. Please train the model first.")

    try:
        features = pd.DataFrame({'distance_km': [input.distance_km], 'battery_level': [input.battery_level]})
        prediction = model.predict(features)[0]
    except Exception as e:
        logger.error(f"Prediction failed for input {input}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    result = {
        "distance_km": input.distance_km,
        "estimated_minutes": round(float(prediction), 1)
    }
    logger.info(f"Response 200 - estimated_minutes={result['estimated_minutes']}")
    return result