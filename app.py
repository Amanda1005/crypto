import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 使用非交互式後端

# ===================== 頁面設定 =====================
st.set_page_config(page_title="Crypto Next-Day High Dashboard", layout="wide")

# ===================== Session State 初始化 =====================
if 'predictions' not in st.session_state:
    st.session_state.predictions = {}

# ===================== CoinGecko 即時行情 =====================
@st.cache_data(ttl=60)
def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,ripple,solana",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        data = requests.get(url, params=params, timeout=5).json()
        if not data:
            raise ValueError("No data received")
        parts = []
        for coin, info in data.items():
            symbol = {"bitcoin": "BTC", "ethereum": "ETH", "ripple": "XRP", "solana": "SOL"}[coin]
            price = info.get("usd", 0)
            change = info.get("usd_24h_change", 0)
            arrow = "▲" if change >= 0 else "▼"
            color = "#00ff99" if change >= 0 else "#ff6666"
            parts.append(
                f"<span style='color:white'>{symbol}/USD</span> "
                f"<span style='color:#a3b8ef'>{price:,.2f}</span> "
                f"<span style='color:{color}'>{arrow}{abs(change):.2f}%</span>"
            )
        return "  ".join(parts)
    except Exception:
        return "BTC/USD 67,450 ▲1.25% ETH/USD 3,120 ▲0.84% XRP/USD 0.512 ▼0.34% SOL/USD 102.4 ▲2.02%"

# ===================== 折線圖繪製（30天） =====================
def plot_chart(coin_id, title):
    """不使用緩存，每次都重新繪製"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "30"}
    try:
        res = requests.get(url, params=params, timeout=10).json()
        prices = res.get("prices", [])
        if not prices:
            return None
            
        x = [datetime.fromtimestamp(p[0]/1000) for p in prices]
        y = [p[1] for p in prices]

        # 創建新的 figure
        fig = plt.figure(figsize=(4, 2))
        ax = fig.add_subplot(111)
        ax.plot(x, y, color="#00bfff", linewidth=2.0)
        ax.fill_between(x, y, color="#00bfff", alpha=0.2)
        ax.set_title(title, fontsize=11, color="#a3c9ff", pad=10)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        plt.xticks(rotation=25)
        plt.tight_layout()
        return fig
    except Exception as e:
        print(f"Error: {e}")
        return None

# ===================== API 預測函數 =====================
def predict(api_url, payload):
    try:
        response = requests.get(api_url, params=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            # 嘗試多種可能的鍵名
            prediction = result.get('predicted_next_day_high') or \
                        result.get('prediction') or \
                        result.get('predicted_high') or \
                        result.get('next_day_high')
            if prediction is not None:
                return prediction
            # 如果找不到預期的鍵，返回整個結果
            return str(result)
        else:
            return f"API Error: {response.status_code} - {response.text[:100]}"
    except requests.exceptions.Timeout:
        return "Request Timeout - API took too long to respond"
    except requests.exceptions.ConnectionError:
        return "Connection Error - Unable to reach API"
    except Exception as e:
        return f"Error: {str(e)}"

# ===================== 全域 CSS（韓風 + 無閃爍按鈕） =====================
st.markdown("""
<style>
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }
.stApp {
    background: linear-gradient(135deg, #0e131f, #080b12);
    color: #e6e9ef;
    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
}
.ticker {
    width: 100%;
    background: linear-gradient(90deg, #0a0f18, #111827);
    border-bottom: 1px solid rgba(255,255,255,0.08);
    overflow: hidden; white-space: nowrap;
    height: 36px; line-height: 36px;
}
.ticker span {
    display: inline-block;
    animation: ticker-scroll 30s linear infinite;
    padding-right: 2rem;
}
@keyframes ticker-scroll { 0% {transform:translateX(100%);} 100% {transform:translateX(-100%);} }
h1, h2, h3, h4 { color: #cdd6f4 !important; font-weight: 600; }
.result-box {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    border: 1px solid rgba(0,150,255,0.3);
    padding: 1rem; margin-top: 1rem;
    text-align: center;
}
.result-box h3 { color: #7dd3fc; font-weight: 700; }

/* 完全禁用按鈕動畫和閃爍 */
div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #00c3ff, #0066ff) !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 1rem !important;
    box-shadow: 0 2px 8px rgba(0,150,255,0.3) !important;
}

div[data-testid="stButton"] button:hover {
    background: linear-gradient(90deg, #0099cc, #0052cc) !important;
    box-shadow: 0 4px 12px rgba(0,150,255,0.4) !important;
}

div[data-testid="stButton"] button:active,
div[data-testid="stButton"] button:focus {
    background: linear-gradient(90deg, #0088bb, #0044bb) !important;
    outline: none !important;
}

/* 完全移除所有動畫效果 */
div[data-testid="stButton"] button,
div[data-testid="stButton"] button * {
    transition: none !important;
    animation: none !important;
    transform: none !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== 動態行情列 =====================
prices_html = get_crypto_prices()
st.markdown(f"<div class='ticker'><span>{prices_html}</span></div>", unsafe_allow_html=True)

# ===================== 主標題 =====================
st.title("💹 Crypto Next-Day High Price Prediction Dashboard")
st.markdown("Select a cryptocurrency to view its **30-day price trend** and predict tomorrow's high price.")

# ===================== Tabs =====================
tabs = st.tabs(["Bitcoin", "Ethereum", "XRP", "Solana"])
coins = [
    ("bitcoin", "BTC", "https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/btc.png", "Random Forest Model (Student A)", "https://your-bitcoin-fastapi.onrender.com/predict"),
    ("ethereum", "ETH", "https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/eth.png", "XGBoost Model (Student B)", "https://your-ethereum-fastapi.onrender.com/predict"),
    ("ripple", "XRP", "https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/xrp.png", "Gradient Boosting Model (Student C)", "https://your-xrp-fastapi.onrender.com/predict"),
    ("solana", "SOL", "https://s2.coinmarketcap.com/static/img/coins/128x128/5426.png", "LightGBM Model (Nian-Ya Weng)", "https://solana-fastapi.onrender.com/predict")
]

# ===================== 幣別分頁內容 =====================
for i, (cid, symbol, icon_url, model_name, api_url) in enumerate(coins):
    with tabs[i]:
        # 顯示圖示
        try:
            st.image(icon_url, width=50)
        except:
            st.write(f"🪙 {symbol}")
        
        st.subheader(f"{symbol} — {model_name}")

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # 每次都重新繪製圖表
            fig = plot_chart(cid, f"{symbol} 30-Day Price Trend (USD)")
            if fig:
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info(f"📊 Loading {symbol} chart...")

        with col_right:
            # 使用 session_state 來保存預測結果
            if st.button(f"🚀 Predict {symbol} High", key=f"{symbol}_predict"):
                with st.spinner(f'Predicting {symbol}...'):
                    prediction = predict(api_url, {
                        "open": 100, "high": 105, "low": 95, "close": 102,
                        "volume": 3000000, "marketCap": 1.0e9,
                        "price_diff": 5, "daily_range": 10, "SMA_7": 101
                    })
                    st.session_state.predictions[symbol] = prediction
                    # 調試用：顯示 API URL
                    if symbol == "SOL":
                        st.session_state[f'{symbol}_api_url'] = api_url
            
            # 顯示預測結果
            if symbol in st.session_state.predictions:
                result = st.session_state.predictions[symbol]
                if isinstance(result, (int, float)):
                    st.markdown(
                        f"<div class='result-box'><h3>Predicted Next-Day High: ${result:,.2f}</h3></div>", 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='result-box'><h3>Predicted Next-Day High: {result}</h3></div>", 
                        unsafe_allow_html=True
                    )
                
                # 調試資訊（只對 Solana 顯示）
                if symbol == "SOL" and f'{symbol}_api_url' in st.session_state:
                    with st.expander("🔍 Debug Info"):
                        st.write(f"API URL: {st.session_state[f'{symbol}_api_url']}")
                        st.write(f"Response: {result}")