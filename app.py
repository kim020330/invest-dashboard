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

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

class JihoFullEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키가 없습니다. .streamlit/secrets.toml을 확인하세요.")
            st.stop()
        self.model = "claude-sonnet-4-6" 
        self.workspace_dir = "Dividend_Securities_Workspace"
        self._ensure_setup()

    def _ensure_setup(self):
        if not os.path.exists(self.workspace_dir): os.makedirs(self.workspace_dir)
        files = {"01_Core.md": "배당 성장 원칙", "02_Macro.md": "거시경제 분석", "03_Fund.md": "재무 건전성", "04_Risk.md": "리스크 관리", "05_CIO.md": "최종 결정"}
        for f_name, guide in files.items():
            path = os.path.join(self.workspace_dir, f_name)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f: f.write(f"# {guide} 가이드\n전문적으로 분석하십시오.")

    def get_signals(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            news = getattr(stock, 'news', [])
            titles = [n.get('title') or "뉴스 제목 없음" for n in news[:3]]
            prompt = f"{ticker} 뉴스 요약: {' / '.join(titles)}\n투자 심리를 '긍정/중립/주의' 중 하나로 판별하고 이유를 써줘."
            resp = self.client.messages.create(model=self.model, max_tokens=500, messages=[{"role": "user", "content": prompt}])
            return {"sentiment": resp.content[0].text, "info": info, "hist": stock.history(period="1y")}
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return None

    def run_deep_analysis(self, name, ticker, context):
        reports = {}
        prog = st.progress(0)
        files = ["01_Core.md", "02_Macro.md", "03_Fund.md", "04_Risk.md", "05_CIO.md"]
        for i, f_name in enumerate(files):
            path = os.path.join(self.workspace_dir, f_name)
            with open(path, "r", encoding="utf-8") as f: instruction = f.read()
            resp = self.client.messages.create(model=self.model, max_tokens=3000, system=instruction, messages=[{"role": "user", "content": f"대상: {name}({ticker})\n상황: {context}"}])
            reports[f_name] = resp.content[0].text
            prog.progress((i + 1) / len(files))
        return reports

    def get_market_briefing(self):
        try:
            search = yf.Search("Dividend Stocks", max_results=5)
            titles = [n['title'] for n in search.news]
            prompt = f"다음 뉴스 요약 브리핑을 3줄로 해줘:\n" + "\n".join(titles)
            resp = self.client.messages.create(model=self.model, max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            return resp.content[0].text, search.news
        except: return "뉴스를 가져오지 못했습니다.", []

    def compare_assets(self, t1, t2):
        s1, s2 = yf.Ticker(t1).info, yf.Ticker(t2).info
        prompt = f"{t1}와 {t2} 중 배당 투자 관점에서 어디가 더 나은지 비교해줘."
        resp = self.client.messages.create(model=self.model, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text, s1, s2

# UI
engine = JihoFullEngine()
with st.sidebar:
    st.title("🍏 Jiho Terminal")
    page = st.radio("Navigation", ["Home & Analysis", "Portfolio Tracker", "Morning Briefing", "Versus Analysis"])

if page == "Home & Analysis":
    st.header("Intelligence Deep Analysis")
    c1, c2 = st.columns(2)
    name_in = c1.text_input("Company Name", "리얼티인컴")
    ticker_in = c2.text_input("Ticker Symbol", "O")
    
    if st.button("Start Analysis"):
        signals = engine.get_signals(ticker_in)
        if signals:
            curr_price = signals['info'].get('currentPrice', 0)
            st.info(f"📡 AI Signal: {signals['sentiment']}")
            m1, m2 = st.columns(2)
            # 여기가 에러 났던 부분! 아주 깔끔하게 수정했어.
            price_display = f"${curr_price:,.2f}" if ".KS" not in ticker_in else f"₩{curr_price:,.0f}"
            m1.metric("Current Price", price_display)
            m2.metric("Dividend Yield", f"{signals['info'].get('dividendYield', 0)*100:.2f}%")
            
            if st.button(f"Add {ticker_in} to Portfolio"):
                st.session_state.portfolio.append({"Date": datetime.now().strftime("%Y-%m-%d"), "Ticker": ticker_in, "Price": price_display})
                st.toast("추가 완료!")

            t1, t2 = st.tabs(["📊 Market Chart", "🔍 Expert Reports"])
            with t1:
                fig = go.Figure(data=[go.Scatter(x=signals['hist'].index, y=signals['hist']['Close'], line=dict(color='#0071E3'))])
                st.plotly_chart(fig, use_container_width=True)
            with t2:
                reports = engine.run_deep_analysis(name_in, ticker_in, signals['sentiment'])
                for n, c in reports.items():
                    with st.expander(f"📄 {n} 리포트"): st.markdown(c)

elif page == "Portfolio Tracker":
    st.header("My Strategic Holdings")
    if st.session_state.portfolio:
        st.table(pd.DataFrame(st.session_state.portfolio))
        if st.button("Clear All"):
            st.session_state.portfolio = []
            st.rerun()
    else: st.info("비어 있습니다.")

elif page == "Morning Briefing":
    st.header("AI Morning Briefing")
    brief, news = engine.get_market_briefing()
    st.success(brief)
    for n in news: st.markdown(f"🔗 [{n['title']}]({n['link']})")

elif page == "Versus Analysis":
    st.header("Stock Versus Stock")
    v1, v2 = st.columns(2)
    t1 = v1.text_input("Ticker 1", "KO")
    t2 = v2.text_input("Ticker 2", "PEP")
    if st.button("Compare"):
        res, s1, s2 = engine.compare_assets(t1, t2)
        st.write(res)
