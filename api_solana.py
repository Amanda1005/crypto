"""
Solana (SOL) 價格預測 API
模型: LightGBM
作者: Student D (Nian-Ya Weng)
部署: Render (https://solana-fastapi.onrender.com)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import os

# ===================== FastAPI 初始化 =====================
app = FastAPI(
    title="Solana Price Prediction API",
    description="Predict Solana next-day high price using LightGBM model",
    version="1.0.0"
)

# ===================== CORS 設定（允許 Streamlit 跨域請求） =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境建議改為具體的 Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 載入 LightGBM 模型 =====================
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
    print(f"❌ Error loading model: {e}")

# ===================== 請求格式定義 =====================
class PredictionRequest(BaseModel):
    """
    輸入特徵說明:
    - open: 開盤價
    - high: 當日最高價
    - low: 當日最低價
    - close: 收盤價
    - volume: 交易量
    - marketCap: 市值
    - price_diff: 價差 (high - low)
    - daily_range: 日波動範圍
    - SMA_7: 7日簡單移動平均
    """
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

# ===================== 根路徑 =====================
@app.get("/")
def read_root():
    """API 基本資訊"""
    return {
        "message": "🚀 Solana (SOL) Price Prediction API",
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

# ===================== 預測端點 (GET) =====================
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
    """
    使用 Query Parameters 進行預測
    範例: GET /predict?open=100&high=105&low=95&close=102&volume=3000000&marketCap=1e9&price_diff=5&daily_range=10&SMA_7=101
    """
    try:
        # 組合特徵向量（順序必須與訓練時一致！）
        features = np.array([[
            open, high, low, close, volume, marketCap,
            price_diff, daily_range, SMA_7
        ]])
        
        # 執行預測
        if model is not None:
            prediction = float(model.predict(features)[0])
            prediction_source = "LightGBM Model"
        else:
            # Fallback: 簡單估算（僅供測試用）
            prediction = high * 1.02  # 假設明天高點比今天高 2%
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

# ===================== 預測端點 (POST) =====================
@app.post("/predict")
def predict_post(request: PredictionRequest):
    """
    使用 JSON Body 進行預測
    範例 Body:
    {
        "open": 100, "high": 105, "low": 95, "close": 102,
        "volume": 3000000, "marketCap": 1e9,
        "price_diff": 5, "daily_range": 10, "SMA_7": 101
    }
    """
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

# ===================== 健康檢查 =====================
@app.get("/health")
def health_check():
    """檢查 API 和模型狀態"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH)
    }

# ===================== 測試端點 =====================
@app.get("/test")
def test_prediction():
    """快速測試預測功能"""
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

# ===================== 啟動說明 =====================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Solana FastAPI server...")
    print("📝 Visit http://localhost:8000/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)