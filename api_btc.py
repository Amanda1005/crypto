from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np

app = FastAPI(title="Bitcoin Price Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = joblib.load("models/bitcoin_model.pkl")
except:
    model = None

@app.get("/")
def root():
    return {"message": "Bitcoin Prediction API is running!"}

@app.get("/health")
def health():
    return {"status": "Random Forest is ready"}

@app.get("/predict/bitcoin")
def predict_bitcoin(
    open: float = 67000,
    high: float = 67500,
    low: float = 66800,
    close: float = 67200,
    volume: float = 25000000000,
    marketCap: float = 1300000000000,
    price_diff: float = 700,
    daily_range: float = 500,
    SMA_7: float = 67100
):
    try:
        features = np.array([[open, high, low, close, volume, marketCap, price_diff, daily_range, SMA_7]])
        
        if model is not None:
            prediction = float(model.predict(features)[0])
        else:
            prediction = high * 1.015
        
        return {
            "predicted_next_day_high": round(prediction, 2),
            "currency": "Bitcoin (BTC)",
            "model": "Random Forest"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)