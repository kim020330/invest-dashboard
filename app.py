import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 1. 페이지 설정 및 Apple Style UI 정의
st.set_page_config(page_title="Jiho's Grand Terminal", layout="wide", page_icon="🍏")

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

# 2. 데이터 영구 저장소 설정
PORTFOLIO_FILE = "jiho_grand_portfolio.csv"

def load_data():
    if os.path.exists(PORTFOLIO_FILE): return pd.read_csv(PORTFOLIO_FILE)
    return pd.DataFrame(columns=["Date", "Ticker", "Name", "Qty", "Price", "Sector", "Beta", "Yield", "Market"])

if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = load_data()

class JihoGrandEngine:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        self.model = "claude-sonnet-4-6"

    # [가치평가 통합 모델]
    def get_valuation(self, info):
        results = {}
        # 1. Graham Number (가치주)
        eps, bvps = info.get('trailingEps', 0), info.get('bookValue', 0)
        results['Graham'] = np.sqrt(22.5 * eps * bvps) if eps > 0 and bvps > 0 else None
        # 2. S-RIM (성장/수익성)
        roe, required = info.get('returnOnEquity', 0), 0.10
        results['S-RIM'] = bvps * (roe / required) if roe > 0 and bvps > 0 else None
        # 3. DDM (배당주)
        d0, g, r = info.get('dividendRate', 0), 0.05, 0.09
        results['DDM'] = (d0 * (1 + g)) / (r - g) if d0 > 0 and r > g else None
        return results

# 3. 사이드바 및 실시간 환율/매크로 데이터
engine = JihoGrandEngine()
fx_rate = yf.Ticker("USDKRW=X").info.get('regularMarketPrice', 1350.0)
vix = yf.Ticker("^VIX").info.get('regularMarketPrice', 0)

with st.sidebar:
    st.title("🏛️ Jiho Grand Terminal")
    menu = st.radio("Menu", ["1. Analysis & Valuation", "2. Portfolio Analytics", "3. Global Radar"])
    st.divider()
    st.metric("실시간 환율 (USD/KRW)", f"₩{fx_rate:,.2f}")
    st.metric("시장 공포지수 (VIX)", f"{vix:.2f}", "위험" if vix > 25 else "안정")
    st.caption(f"CEO: 지호 | System Active")

# 페이지 1: 지능형 통합 분석
if menu == "1. Analysis & Valuation":
    st.header("Intelligence Deep Analysis")
    col_in1, col_in2 = st.columns([2, 1])
    t_ticker = col_in1.text_input("Ticker Symbol (e.g., AAPL, O, 005930.KS)", "AAPL")
    t_qty = col_in2.number_input("Quantity", min_value=1, value=10)
    
    if st.button("전문가 분석 엔진 가동"):
        with st.spinner("AI와 퀀트 모델이 협업 중..."):
            stock = yf.Ticker(t_ticker)
            info, hist = stock.info, stock.history(period="1y")
            vals = engine.get_valuation(info)
            curr_price = info.get('currentPrice', 0)
            
            # 

            st.markdown("### 🎯 Multi-Valuation Dashboard")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("현재가", f"${curr_price}" if ".KS" not in t_ticker else f"₩{curr_price:,.0)
            m2.metric("S-RIM 적정가", f"${vals['S-RIM']:.2f}" if vals['S-RIM'] else "N/A")
            m3.metric("Graham 적정가", f"${vals['Graham']:.2f}" if vals['Graham'] else "N/A")
            m4.metric("배당 수익률", f"{info.get('dividendYield', 0)*100:.2f}%")
            
            # 포트폴리오 추가
            if st.button("Add to My Portfolio"):
                new_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Ticker": t_ticker, "Name": info.get('shortName'),
                           "Qty": t_qty, "Price": curr_price, "Sector": info.get('sector', 'ETC'), "Beta": info.get('beta', 1.0),
                           "Yield": info.get('dividendYield', 0), "Market": "KR" if ".KS" in t_ticker else "US"}
                st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.portfolio_df.to_csv(PORTFOLIO_FILE, index=False)
                st.toast("자산이 안전하게 등록되었습니다!")

            # AI 전략 리포트
            st.divider()
            resp = engine.client.messages.create(model=engine.model, max_tokens=2000, 
                                                messages=[{"role": "user", "content": f"{t_ticker}의 현재 주가 {curr_price}와 가치평가 모델값 {vals}를 비교해서 투자 전략을 짜줘."}])
            st.markdown(resp.content[0].text)

# 페이지 2: 포트폴리오 분석 및 리스크 시각화
elif menu == "2. Portfolio Analytics":
    st.header("Asset Allocation & Risk Intelligence")
    df = st.session_state.portfolio_df
    if not df.empty:
        # 환율 적용 계산
        df['Val_KRW'] = df.apply(lambda r: r['Qty']*r['Price']*fx_rate if r['Market']=="US" else r['Qty']*r['Price'], axis=1)
        total_krw = df['Val_KRW'].sum()
        
        c_r1, c_r2 = st.columns(2)
        c_r1.metric("총 자산 (KRW 환산)", f"₩{total_krw:,.0f}")
        avg_beta = (df['Beta'] * df['Val_KRW']).sum() / total_krw
        c_r2.metric("포트폴리오 베타 (시장 민감도)", f"{avg_beta:.2f}", "방어적" if avg_beta < 1 else "공격적")
        
        # 

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🥧 섹터별 비중")
            fig_sector = px.pie(df, values='Val_KRW', names='Sector', hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sector, use_container_width=True)
        with col_p2:
            st.markdown("#### 💹 종목별 비중")
            fig_ticker = px.pie(df, values='Val_KRW', names='Ticker', hole=.4)
            st.plotly_chart(fig_ticker, use_container_width=True)
            
        st.dataframe(df[['Ticker', 'Name', 'Qty', 'Price', 'Market', 'Val_KRW']], use_container_width=True)
    else:
        st.info("포트폴리오가 비어 있습니다.")
