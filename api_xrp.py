from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np

app = FastAPI(title="XRP Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model
try:
    pipeline = joblib.load("models/25660135_at3_pipeline.pkl")
    model = joblib.load("models/25660135_at3_ridge.pkl")
    print("Models loaded successfully")
except Exception as e:
    model = None
    print(f"Error loading model: {e}")

@app.get("/")
def root():
    return {"message": "XRP Prediction API is running!"}

@app.get("/health")
def health():
    return {
        "status": "Ridge Regressor is ready" if model else "Model not loaded",
        "model_loaded": model is not None
    }

@app.get("/predict_latest")
def predict_latest():
    try:
        if model is None:
            return {"error": "Model not loaded"}
        
        # Predict using fixed data (without calling external APIs)
        latest_data = pd.DataFrame({
            'open': [0.5],
            'high': [0.52],
            'low': [0.49],
            'close': [0.51],
            'volume': [1000000],
            'marketCap': [25000000000],
            'price_diff': [0.03],
            'daily_range': [0.03],
            'SMA_7': [0.505]
        })
        
        prediction = model.predict(latest_data)
        return {"high": str(prediction[0])}
        
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)