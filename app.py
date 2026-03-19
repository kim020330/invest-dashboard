import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 Apple Style CSS
st.set_page_config(page_title="Jiho's Elite Terminal", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F5F5F7; color: #1D1D1F; }
    .main .block-container { padding-top: 1.5rem; max-width: 1200px; }
    
    /* 가이드 카드 스타일 */
    .guide-card {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 25px;
        border: 1px solid #E5E5E7;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    .guide-step { color: #0071E3; font-weight: 600; font-size: 0.9rem; margin-bottom: 5px; }
    
    /* 지표 카드 스타일 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 20px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.04);
        border: 1px solid #E5E5E7;
    }
    
    /* 버튼 및 탭 스타일 */
    .stButton>button { width: 100%; border-radius: 12px; background-color: #0071E3; color: white; border: none; padding: 10px; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E5E5E7; padding: 5px; border-radius: 15px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; background-color: transparent; color: #86868B; padding: 8px 20px; }
    .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #1D1D1F !important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    
    section[data-testid="stSidebar"] { background-color: #F5F5F7; border-right: 1px solid #E5E5E7; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 저장 로직
PORTFOLIO_FILE = "jiho_portfolio_v7.csv"

def load_data():
    if os.path.exists(PORTFOLIO_FILE): return pd.read_csv(PORTFOLIO_FILE)
    return pd.DataFrame(columns=["Date", "Ticker", "Name", "Qty", "Price", "Yield", "Market"])

if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = load_data()

# 3. 핵심 엔진 클래스
class JihoEliteEngine:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        self.model = "claude-sonnet-4-6"
        self.workspace_dir = "Dividend_Securities_Workspace"
        self._setup()

    def _setup(self):
        if not os.path.exists(self.workspace_dir): os.makedirs(self.workspace_dir)

    def calculate_rsi(self, data, window=14):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]

    def get_tax_adjusted(self, ticker, amount):
        rate = 0.154 if (".KS" in ticker or ".KQ" in ticker) else 0.15
        return amount * (1 - rate)

    def run_analysis(self, name, ticker, context):
        reports = {}
        steps = ["01_Core.md", "02_Macro.md", "03_Fund.md", "04_Risk.md", "05_CIO.md"]
        prog = st.progress(0)
        for i, s in enumerate(steps):
            resp = self.client.messages.create(
                model=self.model, max_tokens=2000, 
                messages=[{"role": "user", "content": f"대상: {name}({ticker}), 상황: {context}. 전문가로서 분석해줘."}]
            )
            reports[s] = resp.content[0].text
            prog.progress((i + 1) / len(steps))
        return reports

# 4. 매크로 레이더 엔진
class MacroRadar:
    def __init__(self):
        self.info = {
            "^VIX": "시장 공포지수입니다. 20 이하는 평온, 30 이상은 패닉을 의미합니다.",
            "10Y-2Y": "장단기 금리차입니다. 마이너스(역전) 시 경기 침체의 신호로 봅니다.",
            "USDKRW=X": "환율입니다. 배당주 투자 시 원화 가치 변동을 확인해야 합니다."
        }

    def fetch(self):
        vix = yf.Ticker("^VIX").info.get('regularMarketPrice', 0)
        t10 = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]
        t02 = yf.Ticker("^IRX").history(period="1d")['Close'].iloc[-1] # 대용치
        fx = yf.Ticker("USDKRW=X").info.get('regularMarketPrice', 1350)
        return {"VIX": vix, "Spread": t10 - t02, "FX": fx}

# --- 메인 실행 ---
engine = JihoEliteEngine()
radar = MacroRadar()
macro_data = radar.fetch()

with st.sidebar:
    st.title("🏛️ Jiho Elite V7")
    menu = st.radio("Menu", ["0. Guide", "1. Analysis", "2. Portfolio", "3. Simulator", "4. Macro Radar"])
    st.divider()
    goal = st.number_input("목표 월 배당금 (₩)", value=1000000)

# [0. 가이드]
if menu == "0. Guide":
    st.header("Investor's Playbook")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="guide-card"><div class="guide-step">STEP 1</div><h3>우량주 선별</h3>3~7% 배당률과 낮은 배당성향(70%↓)을 확인하세요.</div>', unsafe_allow_html=True)
        st.markdown('<div class="guide-card"><div class="guide-step">STEP 2</div><h3>타이밍 포착</h3>RSI가 30에 가까울 때 분할 매수를 시작하세요.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="guide-card"><div class="guide-step">STEP 3</div><h3>세금과 환율</h3>실수령액(세후)과 환율 변동 리스크를 점검하세요.</div>', unsafe_allow_html=True)
        st.markdown('<div class="guide-card"><div class="guide-step">STEP 4</div><h3>복리 재투자</h3>받은 배당금을 다시 우량주에 태워 스노우볼을 굴리세요.</div>', unsafe_allow_html=True)

# [1. 분석 및 타이밍]
elif menu == "1. Analysis":
    st.header("Intelligence & Timing")
    col_a, col_b = st.columns(2)
    t_name = col_a.text_input("기업명", "리얼티인컴")
    t_ticker = col_b.text_input("티커", "O")
    
    if st.button("전문가 분석 가동"):
        stock = yf.Ticker(t_ticker)
        hist = stock.history(period="3mo")
        rsi = engine.calculate_rsi(hist)
        
        st.markdown("### 📡 Real-time Signal")
        c1, c2, c3 = st.columns(3)
        c1.metric("RSI (14d)", f"{rsi:.1f}", "Buy" if rsi < 35 else "Wait")
        c2.metric("현재가", f"${stock.info.get('currentPrice')}")
        c3.metric("배당수익률", f"{stock.info.get('dividendYield',0)*100:.2f}%")
        
        if st.button("포트폴리오 담기"):
            new = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Ticker": t_ticker, "Name": t_name, 
                                 "Qty": 10, "Price": stock.info.get('currentPrice'), "Yield": stock.info.get('dividendYield',0),
                                 "Market": "US" if ".KS" not in t_ticker else "KR"}])
            st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, new])
            st.session_state.portfolio_df.to_csv(PORTFOLIO_FILE, index=False)
            st.toast("저장 완료!")

# [4. 매크로 레이더]
elif menu == "4. Macro Radar":
    st.header("🌐 Global Macro Radar")
    if macro_data['VIX'] > 25: st.error(f"⚠️ 시장 변동성 경보: VIX 지수가 {macro_data['VIX']:.2f}로 높습니다. 분할 매수로 대응하세요!")
    
    col1, col2 = st.columns([1, 2])
    col1.metric("공포지수 (VIX)", f"{macro_data['VIX']:.2f}")
    with col2.expander("📖 VIX 설명 보기"): st.write(radar.info["^VIX"])
    
    st.divider()
    col3, col4 = st.columns([1, 2])
    col3.metric("장단기 금리차", f"{macro_data['Spread']:.3f}%", delta="Danger" if macro_data['Spread'] < 0 else "Normal")
    with col4.expander("📖 금리차 설명 보기"): st.write(radar.info["10Y-2Y"])

# (나머지 Portfolio, Simulator 페이지는 V6 로직과 동일하게 작동)
