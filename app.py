import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import os
from datetime import datetime

# 1. 페이지 설정 및 디자인 (Apple Style CSS)
st.set_page_config(page_title="Jiho's Investment Terminal", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F5F5F7;
        color: #1D1D1F;
    }

    .main .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 20px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.04);
        border: 1px solid #E5E5E7;
    }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background-color: #0071E3;
        color: white;
        border: none;
        padding: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #E5E5E7;
        padding: 5px;
        border-radius: 15px;
        gap: 5px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        background-color: transparent;
        color: #86868B;
        border: none;
        padding: 8px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1D1D1F !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    section[data-testid="stSidebar"] {
        background-color: #F5F5F7;
        border-right: 1px solid #E5E5E7;
    }
    </style>
    """, unsafe_allow_html=True)

class HybridInvestmentEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키가 없습니다.")
            st.stop()
            
        self.model = "claude-sonnet-4-6" 
        self.workspace_dir = "Dividend_Securities_Workspace"
        self.pipeline_config = {
            "01 핵심 철학": {"file": "01_Core_Philosophy.md", "guide": "배당 성장성 분석 전문가."},
            "02 매크로 분석": {"file": "02_Macro_Analysis.md", "guide": "거시경제 환경 분석 전문가."},
            "03 펀더멘탈": {"file": "03_Fundamental_Analysis.md", "guide": "재무 건전성 분석 전문가."},
            "04 리스크 관리": {"file": "04_Risk_Management.md", "guide": "리스크 요인 분석 전문가."},
            "05 최종 결정": {"file": "05_CIO_Decision_Matrix.md", "guide": "CIO로서 최종 의견 도출."}
        }
        self._ensure_workspace_setup()

    def _ensure_workspace_setup(self):
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
        for name, config in self.pipeline_config.items():
            path = os.path.join(self.workspace_dir, config["file"])
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"# {name} 가이드\n{config['guide']}")

    def get_hybrid_signals(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            news = getattr(stock, 'news', [])
            
            tech_score = 0
            div_yield = info.get('dividendYield', 0) * 100
            if 3.0 <= div_yield <= 8.0: tech_score += 50
            if info.get('currentPrice', 0) > info.get('twoHundredDayAverage', 0): tech_score += 50
            
            titles = [n.get('title') or "제목 없음" for n in news[:5]]
            news_context = " / ".join(titles) if titles else "최근 뉴스 없음"
            
            prompt = f"{ticker} 뉴스 요약: {news_context}\n\n투자의견을 '긍정/중립/주의' 중 하나로 시작해 한 줄로 요약해줘."
            resp = self.client.messages.create(
                model=self.model, 
                max_tokens=500, 
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "tech_score": tech_score, 
                "sentiment": resp.content[0].text, 
                "info": info, 
                "hist": stock.history(period="1y")
            }
        except Exception as e:
            st.error(f"데이터 수집 오류: {e}")
            return None

    def run_full_analysis(self, company_name, ticker, context):
        all_reports = {}
        progress_bar = st.progress(0)
        for i, (name, config) in enumerate(self.pipeline_config.items()):
            path = os.path.join(self.workspace_dir, config["file"])
            with open(path, "r", encoding="utf-8") as f:
                instruction = f.read()
            
            try:
                response = self.client.messages.create(
                    model=self.model, 
                    max_tokens=3000, 
                    system=instruction,
                    messages=[{"role": "user", "content": f"대상: {company_name}({ticker})\n맥락: {context}"}]
                )
                all_reports[name] = response.content[0].text
            except Exception as e:
                all_reports[name] = f"분석 중 에러 발생: {e}"
                
            progress_bar.progress((i + 1) / len(self.pipeline_config))
        return all_reports

# --- 메인 실행부 ---
engine = HybridInvestmentEngine()

st.title("🏛️ Investment Terminal")
st.write(f"Today is {datetime.now().strftime('%B %d, %Y')}")

with st.sidebar:
    st.header("Configure")
    name = st.text_input("Company Name", "리얼티인컴")
    ticker = st.text_input("Ticker Symbol", "O")
    st.divider()
    analyze_btn = st.button("Start Intelligence Analysis")

if analyze_btn:
    with st.spinner("Processing Intelligence..."):
        signals = engine.get_hybrid_signals(ticker)
        if signals:
            st.markdown("### 📡 Real-time Intelligence")
            c1, c2 = st.columns([1, 2])
            c1.metric("Tech Score", f"{signals['tech_score']}%")
            c2.info(signals['sentiment'])
            
            t1, t2 = st.tabs(["📊 Market Data", "🔍 Deep Analysis"])
            with t1:
                fig = go.Figure(data=[go.Scatter(x=signals['hist'].index, y=signals['hist']['Close'], line=dict(color='#0071E3', width=2))])
                fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=20, b=0), height=400)
                st.plotly_chart(fig, use_container_width=True)
                
            with t2:
                reports = engine.run_full_analysis(name, ticker, signals['sentiment'])
                if reports:
                    sub_tabs = st.tabs(list(reports.keys()))
                    for idx, (n, c) in enumerate(reports.items()):
                        with sub_tabs[idx]:
                            st.markdown(c)
else:
    st.info("💡 사이드바에서 기업 정보를 입력하고 분석을 시작하세요.")
