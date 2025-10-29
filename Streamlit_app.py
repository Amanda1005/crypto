import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Crypto Next-Day High Dashboard", layout="wide")

if 'predictions' not in st.session_state:
    st.session_state.predictions = {}
if 'selected_coin' not in st.session_state:
    st.session_state.selected_coin = 'Bitcoin'

@st.cache_data(ttl=60)
def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin,ethereum,xrp,solana", "vs_currencies": "usd", "include_24hr_change": "true"}
    try:
        data = requests.get(url, params=params, timeout=5).json()
        if not data:
            raise ValueError("No data received")
        parts = []
        for coin, info in data.items():
            symbol = {"bitcoin": "BTC", "ethereum": "ETH", "xrp": "XRP", "solana": "SOL"}[coin]
            price = info.get("usd", 0)
            change = info.get("usd_24h_change", 0)
            arrow = "▲" if change >= 0 else "▼"
            color = "#2D9F4F" if change >= 0 else "#D9534F"
            parts.append(
                f"<span style='color:#2C2C2C;font-weight:600'>{symbol}/USD</span> "
                f"<span style='color:#5A5A5A'>{price:,.2f}</span> "
                f"<span style='color:{color};font-weight:600'>{arrow}{abs(change):.2f}%</span>"
            )
        return "  ".join(parts)
    except Exception:
        return "BTC/USD 67,450 ▲1.25% ETH/USD 3,120 ▲0.84% XRP/USD 0.512 ▼0.34% SOL/USD 102.4 ▲2.02%"

@st.cache_data(ttl=300)
def get_kraken_ohlc(pair):
    url = "https://api.kraken.com/0/public/OHLC"
    params = {"pair": pair, "interval": 1440}
    try:
        response = requests.get(url, params=params, timeout=10).json()
        if response.get("error") or not response.get("result"):
            return None
        key = list(response["result"].keys())[0]
        data = response["result"][key][-7:]
        result = []
        for row in data:
            result.append({
                "date": datetime.fromtimestamp(int(row[0])),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4])
            })
        return result
    except Exception:
        return None

def plot_candlestick(data, symbol):
    if not data:
        return None
    df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='#2D9F4F',
        decreasing_line_color='#D9534F'
    )])
    fig.update_layout(
        title=f"{symbol} 7-Day Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='#FAF8F3',
        plot_bgcolor='#FFFFFF',
        font=dict(color='#3A3A3A', size=10),
        xaxis=dict(gridcolor='rgba(0,0,0,0.08)', rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor='rgba(0,0,0,0.08)')
    )
    return fig

def predict(api_url, payload):
    try:
        response = requests.get(api_url, params=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            prediction = result.get('predicted_next_day_high') or result.get('prediction') or result.get('predicted_high') or result.get('next_day_high')
            if prediction is not None:
                return prediction
            return str(result)
        else:
            return f"API Error: {response.status_code}"
    except requests.exceptions.Timeout:
        return "Request Timeout"
    except requests.exceptions.ConnectionError:
        return "Connection Error"
    except Exception as e:
        return f"Error: {str(e)}"

st.markdown("""
<style>
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }
.stApp {
    background: linear-gradient(135deg, #FAF8F3, #F5F1E8);
    color: #2C2C2C;
    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
}
.ticker {
    width: 100%;
    background: linear-gradient(90deg, #E8E4D9, #DED9CC);
    border-bottom: 1px solid rgba(0,0,0,0.08);
    overflow: hidden; white-space: nowrap;
    height: 36px; line-height: 36px;
}
.ticker span {
    display: inline-block;
    animation: ticker-scroll 30s linear infinite;
    padding-right: 2rem;
}
@keyframes ticker-scroll { 0% {transform:translateX(100%);} 100% {transform:translateX(-100%);} }
h1 { color: #1A1A1A !important; font-weight: 700; }
h2, h3, h4 { color: #3A3A3A !important; font-weight: 600; }
.result-box {
    background: linear-gradient(135deg, #FFF9F0, #FFF5E6);
    border-radius: 8px;
    border: 1px solid #D4C5B0;
    padding: 0.6rem;
    margin-top: 0.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(180,150,120,0.15);
}
.result-box h3 { 
    color: #8B7355; 
    font-weight: 600;
    font-size: 1.1rem;
    margin: 0;
}
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #C9A57B, #A68B6A) !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.4rem 0.8rem !important;
    font-size: 0.9rem !important;
    box-shadow: 0 2px 6px rgba(169,139,106,0.3) !important;
    height: 38px !important;
}
div[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #B89968, #957A59) !important;
    box-shadow: 0 3px 8px rgba(169,139,106,0.4) !important;
}
div[data-testid="stButton"] button:active,
div[data-testid="stButton"] button:focus {
    background: linear-gradient(135deg, #A68B6A, #8B7355) !important;
    outline: none !important;
}
div[data-testid="stButton"] button,
div[data-testid="stButton"] button * {
    transition: none !important;
    animation: none !important;
    transform: none !important;
}
div[data-testid="stMarkdown"] p {
    color: #4A4A4A;
}
</style>
""", unsafe_allow_html=True)

prices_html = get_crypto_prices()
st.markdown(f"<div class='ticker'><span>{prices_html}</span></div>", unsafe_allow_html=True)

st.title("Crypto Next-Day High Price Prediction Dashboard")
st.markdown("View **7-day candlestick charts** and predict tomorrow's high price.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Bitcoin", key="tab_btc", use_container_width=True):
        st.session_state.selected_coin = 'Bitcoin'
with col2:
    if st.button("Ethereum", key="tab_eth", use_container_width=True):
        st.session_state.selected_coin = 'Ethereum'
with col3:
    if st.button("XRP", key="tab_xrp", use_container_width=True):
        st.session_state.selected_coin = 'XRP'
with col4:
    if st.button("Solana", key="tab_sol", use_container_width=True):
        st.session_state.selected_coin = 'Solana'

st.markdown("---")

API_URLS = {
    "BTC": "https://bitcoin-api-studentA.onrender.com/predict",
    "ETH": "https://ethereum-api-studentB.onrender.com/predict",
    "XRP": "https://xrp-api-studentC.onrender.com/predict",
    "SOL": "https://solana-fastapi.onrender.com/predict"
}

coins_data = {
    "Bitcoin": ("bitcoin", "BTC", "XXBTZUSD", "https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/btc.png", "Random Forest Model (Student A)", API_URLS["BTC"]),
    "Ethereum": ("ethereum", "ETH", "XETHZUSD", "https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/eth.png", "XGBoost Model (Student B)", API_URLS["ETH"]),
    "XRP": ("xrp", "XRP", "XXRPZUSD", "https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/xrp.png", "Gradient Boosting Model (Student C)", API_URLS["XRP"]),
    "Solana": ("solana", "SOL", "SOLUSD", "https://s2.coinmarketcap.com/static/img/coins/128x128/5426.png", "LightGBM Model (Student D - Nian-Ya Weng)", API_URLS["SOL"])
}

cid, symbol, kraken_pair, icon_url, model_name, api_url = coins_data[st.session_state.selected_coin]

try:
    st.image(icon_url, width=50)
except:
    st.write(f"🪙 {symbol}")

st.subheader(f"{symbol} — {model_name}")

col_btn, col_result = st.columns([1, 2])

with col_btn:
    predict_btn = st.button(f"🚀 Predict {symbol} High", key=f"{symbol}_predict")

with col_result:
    if predict_btn:
        with st.spinner(f'Predicting {symbol}...'):
            prediction = predict(api_url, {
                "open": 100, "high": 105, "low": 95, "close": 102,
                "volume": 3000000, "marketCap": 1.0e9,
                "price_diff": 5, "daily_range": 10, "SMA_7": 101
            })
            st.session_state.predictions[symbol] = prediction
    
    if symbol in st.session_state.predictions:
        result = st.session_state.predictions[symbol]
        if isinstance(result, (int, float)):
            st.markdown(f"<div class='result-box'><h3>Predicted High: ${result:,.2f}</h3></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='result-box'><h3>Predicted High: {result}</h3></div>", unsafe_allow_html=True)

st.markdown("---")

kraken_data = get_kraken_ohlc(kraken_pair)
if kraken_data:
    candle_fig = plot_candlestick(kraken_data, symbol)
    if candle_fig:
        st.plotly_chart(candle_fig, use_container_width=True)
else:
    st.error(f"Unable to load {symbol} candlestick chart")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #8B7355; padding: 1rem;'><p>Data: CoinGecko API | Kraken API | Group Project AT3</p></div>", unsafe_allow_html=True)