import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import os
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 Apple Style CSS 주입
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

# 2. 세션 상태 초기화 (데이터 유지용)
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
        self.pipeline_config = {
            "01 핵심 철학": {"file": "01_Core.md", "guide": "배당 성장 투자 원칙을 기준으로 기업을 평가하십시오."},
            "02 매크로 분석": {"file": "02_Macro.md", "guide": "현재 금리와 환율 등 거시경제 지표가 기업에 미치는 영향을 분석하십시오."},
            "03 펀더멘탈": {"file": "03_Fund.md", "guide": "현금 흐름과 부채 비율 등 재무적 건전성을 분석하십시오."},
            "04 리스크 관리": {"file": "04_Risk.md", "guide": "배당 삭감 가능성 및 시장 경쟁 리스크를 분석하십시오."},
            "05 최종 결정 (CIO)": {"file": "05_CIO.md", "guide": "앞선 분석을 종합하여 매수/보류/매도 의견을 제시하십시오."}
        }
        self._ensure_setup()

    def _ensure_setup(self):
        if not os.path.exists(self.workspace_dir): os.makedirs(self.workspace_dir)
        for config in self.pipeline_config.values():
            path = os.path.join(self.workspace_dir, config["file"])
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f: f.write(f"# 지침\n{config['guide']}")

    # 기능 1: 하이브리드 시그널 (수치 + 뉴스)
    def get_signals(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            news = getattr(stock, 'news', [])
            titles = [n.get('title') or "제목 없음" for n in news[:3]]
            
            prompt = f"{ticker} 뉴스 요약: {' / '.join(titles)}\n현재 투자 심리를 '긍정/중립/주의' 중 하나로 판별하고 이유를 써줘."
            resp = self.client.messages.create(model=self.model, max_tokens=500, messages=[{"role": "user", "content": prompt}])
            
            return {
                "sentiment": resp.content[0].text, 
                "info": info, 
                "hist": stock.history(period="1y"),
                "yield": info.get('dividendYield', 0) * 100
            }
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return None

    # 기능 2: 5단계 심층 분석
    def run_deep_analysis(self, name, ticker, context):
        reports = {}
        prog = st.progress(0)
        for i, (step_name, config) in enumerate(self.pipeline_config.items()):
            path = os.path.join(self.workspace_dir, config["file"])
            with open(path, "r", encoding="utf-8") as f: instruction = f.read()
            
            resp = self.client.messages.create(
                model=self.model, max_tokens=3000, system=instruction,
                messages=[{"role": "user", "content": f"대상: {name}({ticker})\n상황: {context}"}]
            )
            reports[step_name] = resp.content[0].text
            prog.progress((i + 1) / len(self.pipeline_config))
        return reports

    # 기능 3: 모닝 브리핑
    def get_market_briefing(self):
        search = yf.Search("Dividend Growth Stocks", max_results=5)
        titles = [n['title'] for n in search.news]
        prompt = f"다음 뉴스들을 바탕으로 오늘 배당주 투자자가 알아야 할 핵심 브리핑을 3줄로 요약해줘:\n" + "\n".join(titles)
        resp = self.client.messages.create(model=self.model, max_tokens=1000, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text, search.news

    # 기능 4: 종목 비교
    def compare_assets(self, t1, t2):
        s1, s2 = yf.Ticker(t1).info, yf.Ticker(t2).info
        prompt = f"종목 A({t1}, 배당 {s1.get('dividendYield',0)*100:.1f}%)와 종목 B({t2}, 배당 {s2.get('dividendYield',0)*100:.1f}%) 중 배당 성장 관점에서 어디가 더 유리한지 비교 분석해줘."
        resp = self.client.messages.create(model=self.model, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text, s1, s2

# 3. UI 메인 로직
engine = JihoFullEngine()

with st.sidebar:
    st.title("🍏 Jiho Terminal")
    st.caption("AI-Powered Dividend Boutique")
    page = st.radio("Navigation", ["Home & Analysis", "Portfolio Tracker", "Morning Briefing", "Versus Analysis"])
    st.divider()
    st.write("Logged in as: **Jiho Admin**")

# 페이지 1: 분석 및 홈
if page == "Home & Analysis":
    st.header("Intelligence Deep Analysis")
    c_in1, c_in2 = st.columns(2)
    with c_in1: target_name = st.text_input("Company Name", "리얼티인컴")
    with c_in2: target_ticker = st.text_input("Ticker Symbol", "O")
    
    if st.button("Start Analysis"):
        signals = engine.get_signals(target_ticker)
        if signals:
            st.markdown("### 📡 Intelligence Signal")
            st.info(signals['sentiment'])
            
            col_a, col_b = st.columns(2)
            col_a.metric("Dividend Yield", f"{signals['yield']:.2f}%")
            if col_b.button(f"Add {target_ticker} to Portfolio"):
                st.session_state.portfolio.append({"Date": datetime.now().strftime("%Y-%m-%d"), "Ticker": target_ticker, "Price": signals['info'].get('currentPrice')})
                st.toast("포트폴리오에 추가되었습니다!")

            t1, t2 = st.tabs(["📊 Market Data", "🔍 Deep Expert Reports"])
            with t1:
                fig = go.Figure(data=[go.Scatter(x=signals['hist'].index, y=signals['hist']['Close'], line=dict(color='#0071E3', width=2))])
                fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=20, b=0), height=400)
                st.plotly_chart(fig, use_container_width=True)
            with t2:
                reports = engine.run_deep_analysis(target_name, target_ticker, signals['sentiment'])
                sub_tabs = st.tabs(list(reports.keys()))
                for i, (n, c) in enumerate(reports.items()):
                    with sub_tabs[i]: st.markdown(c)

# 페이지 2: 포트폴리오 관리
elif page == "Portfolio Tracker":
    st.header("My Strategic Holdings")
    if st.session_state.portfolio:
        st.table(pd.DataFrame(st.session_state.portfolio))
        if st.button("Clear Portfolio"):
            st.session_state.portfolio = []
            st.rerun()
    else:
        st.info("담긴 종목이 없습니다. 분석 탭에서 마음에 드는 종목을 추가하세요.")

# 페이지 3: 모닝 브리핑
elif page == "Morning Briefing":
    st.header("AI Morning Briefing")
    with st.spinner("Analyzing Global News..."):
        brief, news = engine.get_market_briefing()
        st.success(brief)
        st.divider()
        for n in news: st.markdown(f"🔗 [{n['title']}]({n['link']})")

# 페이지 4: 비교 분석
elif page == "Versus Analysis":
    st.header("Stock Versus Stock")
    c_v1, c_v2 = st.columns(2)
    with c_v1: v1 = st.text_input("Ticker 1", "KO")
    with c_v2: v2 = st.text_input("Ticker 2", "PEP")
    
    if st.button("Start Comparison"):
        with st.spinner("Calculating..."):
            res, s1, s2 = engine.compare_assets(v1, v2)
            st.markdown(f"### 🥊 AI Verdict: {v1} vs {v2}")
            st.write(res)
