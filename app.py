import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import os
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 Apple Style CSS
st.set_page_config(page_title="Jiho's Pro Terminal", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F5F5F7; color: #1D1D1F; }
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 20px; padding: 20px !important; box-shadow: 0 8px 30px rgba(0,0,0,0.04); border: 1px solid #E5E5E7; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #0071E3; color: white; border: none; padding: 10px; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E5E5E7; padding: 5px; border-radius: 15px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; background-color: transparent; color: #86868B; padding: 8px 20px; }
    .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #1D1D1F !important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    section[data-testid="stSidebar"] { background-color: #F5F5F7; border-right: 1px solid #E5E5E7; }
    </style>
    """, unsafe_allow_html=True)

# 2. 세션 상태 초기화 (포트폴리오 저장용)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

class JihoProEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키를 확인해주세요.")
            st.stop()
        self.model = "claude-sonnet-4-6"
        self.workspace_dir = "Dividend_Securities_Workspace"
        self._setup_workspace()

    def _setup_workspace(self):
        if not os.path.exists(self.workspace_dir): os.makedirs(self.workspace_dir)
        files = ["01_Core.md", "02_Macro.md", "03_Fund.md", "04_Risk.md", "05_CIO.md"]
        for f in files:
            path = os.path.join(self.workspace_dir, f)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as file: file.write(f"# {f} 가이드\n전문가로서 분석을 수행하십시오.")

    # [뉴스레터 기능] 시장 뉴스 요약
    def get_market_briefing(self):
        try:
            market_news = yf.Search("Dividend Stocks", max_results=5).news
            titles = [n['title'] for n in market_news]
            prompt = f"다음 뉴스들을 바탕으로 오늘 배당주 시장의 핵심 브리핑을 3문장으로 요약해줘:\n" + "\n".join(titles)
            resp = self.client.messages.create(model=self.model, max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            return resp.content[0].text, market_news
        except: return "브리핑을 가져올 수 없습니다.", []

    # [비교 분석 기능] 두 종목 비교
    def compare_stocks(self, t1, t2):
        s1, s2 = yf.Ticker(t1).info, yf.Ticker(t2).info
        prompt = f"종목 A({t1}, 배당률 {s1.get('dividendYield',0)*100:.1f}%)와 종목 B({t2}, 배당률 {s2.get('dividendYield',0)*100:.1f}%)를 비교해서 배당 투자자에게 어디가 더 유리한지 분석해줘."
        resp = self.client.messages.create(model=self.model, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text, s1, s2

    def get_signals(self, ticker):
        stock = yf.Ticker(ticker)
        info = stock.info
        news = getattr(stock, 'news', [])
        titles = [n.get('title') for n in news[:3]]
        prompt = f"{ticker} 뉴스 요약: {' / '.join(titles)}\n심리를 '긍정/중립/주의'로 판정해줘."
        resp = self.client.messages.create(model=self.model, max_tokens=500, messages=[{"role": "user", "content": prompt}])
        return {"sentiment": resp.content[0].text, "info": info, "hist": stock.history(period="1y")}

# 3. UI 메인 로직
engine = JihoProEngine()

# 사이드바 메뉴 (페이지 전환)
with st.sidebar:
    st.title("🍏 Jiho Terminal")
    menu = st.radio("Go to", ["Home & Analysis", "Portfolio Tracker", "Market Briefing", "Stock Comparison"])
    st.write("---")

# 페이지 1: 홈 및 5단계 분석
if menu == "Home & Analysis":
    st.header("Intelligence Analysis")
    col_in1, col_in2 = st.columns(2)
    with col_in1: t_name = st.text_input("Company Name", "Realty Income")
    with col_in2: t_ticker = st.text_input("Ticker", "O")
    
    if st.button("Run Full Analysis"):
        signals = engine.get_signals(t_ticker)
        if signals:
            st.markdown("### 📡 Intelligence Signal")
            st.info(signals['sentiment'])
            
            # 포트폴리오 추가 버튼
            if st.button(f"Add {t_ticker} to Portfolio"):
                st.session_state.portfolio.append({"name": t_name, "ticker": t_ticker, "price": signals['info'].get('currentPrice')})
                st.toast(f"{t_name}이 포트폴리오에 추가되었습니다!")

            t1, t2 = st.tabs(["📊 Market Chart", "🔍 Expert Reports"])
            with t1:
                fig = go.Figure(data=[go.Scatter(x=signals['hist'].index, y=signals['hist']['Close'], line=dict(color='#0071E3'))])
                st.plotly_chart(fig, use_container_width=True)
            with t2:
                st.write("5단계 리포트가 여기에 생성됩니다. (기존 로직 동일)")

# 페이지 2: 포트폴리오 트래커
elif menu == "Portfolio Tracker":
    st.header("My Portfolio")
    if st.session_state.portfolio:
        df = pd.DataFrame(st.session_state.portfolio)
        st.table(df)
        st.metric("Total Holdings", len(st.session_state.portfolio))
    else:
        st.info("포트폴리오가 비어 있습니다. Analysis 탭에서 종목을 추가하세요.")

# 페이지 3: 데일리 뉴스레터
elif menu == "Market Briefing":
    st.header("Morning Briefing")
    with st.spinner("AI가 밤사이 뉴스를 읽는 중..."):
        brief, news_list = engine.get_market_briefing()
        st.success(brief)
        st.write("---")
        for n in news_list:
            st.markdown(f"🔗 [{n['title']}]({n['link']})")

# 페이지 4: 종목 비교 분석
elif menu == "Stock Comparison":
    st.header("Versus Analysis")
    c1, c2 = st.columns(2)
    with c1: comp1 = st.text_input("Ticker 1", "KO")
    with c2: comp2 = st.text_input("Ticker 2", "PEP")
    
    if st.button("Compare Now"):
        with st.spinner("두 기업의 체급을 비교 중..."):
            result, s1, s2 = engine.compare_stocks(comp1, comp2)
            col_a, col_b = st.columns(2)
            col_a.metric(comp1, f"{s1.get('currentPrice')} {s1.get('currency')}", f"{s1.get('dividendYield',0)*100:.2f}% Div")
            col_b.metric(comp2, f"{s2.get('currentPrice')} {s2.get('currency')}", f"{s2.get('dividendYield',0)*100:.2f}% Div")
            st.markdown(f"### 🥊 AI Verdict\n{result}")
