import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 1. 페이지 설정 및 Apple Style CSS
st.set_page_config(page_title="Jiho's Pro Terminal V3", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F5F5F7; color: #1D1D1F; }
    .main .block-container { padding-top: 1.5rem; max-width: 1200px; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 20px; padding: 20px !important; box-shadow: 0 8px 30px rgba(0,0,0,0.04); border: 1px solid #E5E5E7; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #0071E3; color: white; border: none; padding: 10px; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E5E5E7; padding: 5px; border-radius: 15px; }
    section[data-testid="stSidebar"] { background-color: #F5F5F7; border-right: 1px solid #E5E5E7; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 영구 저장 (CSV) 관련 함수
PORTFOLIO_FILE = "jiho_portfolio_v3.csv"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    return pd.DataFrame(columns=["Date", "Ticker", "Name", "Qty", "Buy_Price", "Sector", "Yield"])

def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = load_portfolio()

class JihoEliteEngine:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        self.model = "claude-sonnet-4-6"

    # [보강 1] 정량적 가치평가 모델 (S-RIM 기반 간이 모델)
    def calculate_fair_value(self, info):
        try:
            roe = info.get('returnOnEquity', 0)
            bps = info.get('bookValue', 0)
            # 요구수익률 10% 가정 (지호가 나중에 수정 가능)
            required_return = 0.10
            if roe > 0 and bps > 0:
                fair_value = bps * (roe / required_return)
                return fair_value
            return None
        except: return None

    # [보강 2] 기술적 지표 (RSI) 계산
    def calculate_rsi(self, data, window=14):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

# 3. UI 로직 시작
engine = JihoEliteEngine()

with st.sidebar:
    st.title("🏛️ Jiho Terminal V3")
    menu = st.radio("Menu", ["Analysis & Valuation", "Portfolio Analytics", "Daily Briefing", "Stock Battle"])
    st.divider()
    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 페이지 1: 지능형 분석 및 수치 기반 가치 평가
if menu == "Analysis & Valuation":
    st.header("Intelligence & Valuation")
    c1, c2 = st.columns([2, 1])
    with c1: t_ticker = st.text_input("Ticker Symbol", "O")
    with c2: t_qty = st.number_input("Quantity", min_value=1, value=10)
    
    if st.button("전문가 분석 엔진 가동"):
        with st.spinner("데이터 로드 및 가치 평가 중..."):
            stock = yf.Ticker(t_ticker)
            info = stock.info
            hist = stock.history(period="1y")
            
            # 수치 데이터 추출
            fair_val = engine.calculate_fair_value(info)
            rsi_val = engine.calculate_rsi(hist)
            curr_price = info.get('currentPrice', 0)
            
            st.markdown("### 🎯 핵심 투자 지표")
            m1, m2, m3 = st.columns(3)
            m1.metric("현재가", f"${curr_price}")
            m2.metric("적정 주가 (S-RIM)", f"${fair_val:.2f}" if fair_val else "N/A", 
                      f"{((fair_val/curr_price)-1)*100:.1f}%" if fair_val else "N/A")
            m3.metric("RSI (14d)", f"{rsi_val:.1f}", "과매수" if rsi_val > 70 else "과매도" if rsi_val < 30 else "중립")
            
            # 
            
            if st.button(f"Add {t_ticker} to Portfolio"):
                new_row = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Ticker": t_ticker,
                    "Name": info.get('shortName'),
                    "Qty": t_qty,
                    "Buy_Price": curr_price,
                    "Sector": info.get('sector', 'Unknown'),
                    "Yield": info.get('dividendYield', 0)
                }
                st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, pd.DataFrame([new_row])], ignore_index=True)
                save_portfolio(st.session_state.portfolio_df)
                st.toast(f"{t_ticker}가 CSV 파일에 안전하게 저장되었습니다!")

            st.divider()
            # AI 리포트 생성
            resp = engine.client.messages.create(
                model=engine.model, max_tokens=2000,
                messages=[{"role": "user", "content": f"{t_ticker}에 대한 종합 분석 리포트를 작성해줘."}]
            )
            st.markdown(resp.content[0].text)

# 페이지 2: 포트폴리오 분석 (섹터 파이 차트 추가)
elif menu == "Portfolio Analytics":
    st.header("Portfolio Risk & Analytics")
    df = st.session_state.portfolio_df
    
    if not df.empty:
        df['Total_Value'] = df['Qty'] * df['Buy_Price']
        
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.markdown("#### 🥧 섹터별 비중 (Sector Mix)")
            fig_sector = px.pie(df, values='Total_Value', names='Sector', hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sector, use_container_width=True)
            
        with c_a2:
            st.markdown("#### 💹 종목별 비중")
            fig_ticker = px.pie(df, values='Total_Value', names='Ticker', hole=.4)
            st.plotly_chart(fig_ticker, use_container_width=True)
            
        st.dataframe(df, use_container_width=True)
        
        if st.button("Reset Portfolio"):
            if os.path.exists(PORTFOLIO_FILE): os.remove(PORTFOLIO_FILE)
            st.session_state.portfolio_df = load_portfolio()
            st.rerun()
    else:
        st.info("포트폴리오가 비어 있습니다. Analysis 탭에서 종목을 추가하세요.")

# 페이지 4: 종목 배틀 (경쟁사 비교)
elif menu == "Stock Battle":
    st.header("Competitor Battle")
    st.write("관심 종목과 경쟁사의 체급을 비교해 보세요.")
    peers = st.text_input("비교할 티커들을 입력하세요 (쉼표 구분)", "AAPL, MSFT, GOOGL")
    
    if st.button("Battle Start!"):
        battle_data = []
        for p in peers.split(","):
            s = yf.Ticker(p.strip()).info
            battle_data.append({
                "Ticker": p.strip(),
                "P/E": s.get('trailingPE'),
                "ROE": s.get('returnOnEquity', 0) * 100,
                "Div Yield": s.get('dividendYield', 0) * 100,
                "Operating Margin": s.get('operatingMargins', 0) * 100
            })
        st.table(pd.DataFrame(battle_data).set_index('Ticker'))
