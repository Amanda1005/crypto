from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import os

# ===================== FastAPI Initialization =====================
app = FastAPI(
    title="Solana Price Prediction API",
    description="Predict Solana next-day high price using LightGBM model",
    version="1.0.0"
)

# ===================== CORS Settings ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== Loading Model =====================
MODEL_PATH = "models/solana_lightgbm_model.pkl"

try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"Model loaded successfully from {MODEL_PATH}")
    else:
        model = None
        print(f"Warning: Model file not found at {MODEL_PATH}")
        print("   Using fallback prediction (high * 1.02)")
except Exception as e:
    model = None
    print(f"Error loading model: {e}")

# ===================== Request Format Definition ====================
class PredictionRequest(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    marketCap: float
    price_diff: float
    daily_range: float
    SMA_7: float

    class Config:
        json_schema_extra = {
            "example": {
                "open": 102.5,
                "high": 105.3,
                "low": 100.8,
                "close": 104.2,
                "volume": 3500000,
                "marketCap": 48000000000,
                "price_diff": 4.5,
                "daily_range": 4.4,
                "SMA_7": 103.1
            }
        }

# ==================== Root Path =====================
@app.get("/")
def read_root():
    """API Basic Information"""
    return {
        "message": "Solana (SOL) Price Prediction API",
        "model": "LightGBM",
        "author": "Student D (Nian-Ya Weng)",
        "version": "1.0.0",
        "status": "operational" if model is not None else "fallback mode",
        "endpoints": {
            "GET /": "API 資訊",
            "GET /predict": "預測明日最高價 (Query Parameters)",
            "POST /predict": "預測明日最高價 (JSON Body)",
            "GET /health": "健康檢查"
        },
        "example_request": "GET /predict?open=100&high=105&low=95&close=102&volume=3000000&marketCap=1e9&price_diff=5&daily_range=10&SMA_7=101"
    }

# ===================== Predict Endpoint (GET) =====================
@app.get("/predict")
def predict_get(
    open: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    marketCap: float,
    price_diff: float,
    daily_range: float,
    SMA_7: float
):
    try:
        # Combined feature vectors
        features = np.array([[
            open, high, low, close, volume, marketCap,
            price_diff, daily_range, SMA_7
        ]])
        
        # Execute Prediction
        if model is not None:
            prediction = float(model.predict(features)[0])
            prediction_source = "LightGBM Model"
        else:
           # Fallback: Simple Estimation
            prediction = high * 1.02  # Assuming tomorrow's high is 2% higher than today's
            prediction_source = "Fallback Estimation (Model not loaded)"
        
        return {
            "predicted_next_day_high": round(prediction, 4),
            "currency": "Solana (SOL)",
            "model": prediction_source,
            "input_features": {
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "marketCap": marketCap,
                "price_diff": price_diff,
                "daily_range": daily_range,
                "SMA_7": SMA_7
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction error: {str(e)}"
        )

# ===================== Predict Endpoint (POST) =====================
@app.post("/predict")
def predict_post(request: PredictionRequest):
    try:
        features = np.array([[
            request.open, request.high, request.low, request.close,
            request.volume, request.marketCap, request.price_diff,
            request.daily_range, request.SMA_7
        ]])
        
        if model is not None:
            prediction = float(model.predict(features)[0])
            prediction_source = "LightGBM Model"
        else:
            prediction = request.high * 1.02
            prediction_source = "Fallback Estimation"
        
        return {
            "predicted_next_day_high": round(prediction, 4),
            "currency": "Solana (SOL)",
            "model": prediction_source
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# ===================== Health Check =====================
@app.get("/health")
def health_check():
    """Check API and model status"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH)
    }

# ==================== Test Endpoints =====================
@app.get("/test")
def test_prediction():
    """Quick Test Prediction Function"""
    test_data = {
        "open": 102.5,
        "high": 105.3,
        "low": 100.8,
        "close": 104.2,
        "volume": 3500000,
        "marketCap": 48000000000,
        "price_diff": 4.5,
        "daily_range": 4.4,
        "SMA_7": 103.1
    }
    
    result = predict_get(**test_data)
    return {
        "message": "Test prediction successful",
        "test_input": test_data,
        "prediction_result": result
    }

# ===================== Startup Instructions =====================
if __name__ == "__main__":
    import uvicorn
    print("Starting Solana FastAPI server...")
    print("Visit http://localhost:8000/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)