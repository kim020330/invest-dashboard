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
    /* 전체 배경 및 폰트 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F5F5F7; /* Apple Light Gray */
        color: #1D1D1F;
    }

    /* 메인 컨테이너 패딩 */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* 카드 스타일 (지표용) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 20px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.04);
        border: 1px solid #E5E5E7;
    }

    /* 버튼 스타일 (Apple Blue) */
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
    .stButton>button:hover {
        background-color: #0077ED;
        box-shadow: 0 4px 15px rgba(0,113,227,0.3);
    }

    /* 탭 스타일 (Segmented Control 느낌) */
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

    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #F5F5F7;
        border-right: 1px solid #E5E5E7;
    }

    /* 정보 박스 스타일 */
    .stAlert {
        border-radius: 15px;
        border: none;
        background-color: #FFFFFF;
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

class HybridInvestmentEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키를 확인해주세요.")
            st.stop()
            
        self.model = "claude-sonnet-4-6" 
        self.workspace_dir = "Dividend_Securities_Workspace"
        self.pipeline_config = {
            "01 핵심 철학": {"file": "01_Core_Philosophy.md", "guide": "당신은 배당 성장 투자 전문가입니다. 기업의 배당 정책이 장기적으로 지속 가능한지 분석하세요."},
            "02 매크로 분석": {"file": "02_Macro_Analysis.md", "guide": "당신은 거시경제 전문가입니다. 현재 금리 환경과 인플레이션 영향을 분석하세요."},
            "03 펀더멘탈": {"file": "03_Fundamental_Analysis.md", "guide": "당신은 재무 분석가입니다. 현금창출 능력과 부채 상환 능력을 파헤치세요."},
            "04 리스크 관리": {"file": "04_Risk_Management.md", "guide": "당신은 리스크 관리자입니다. 경쟁사 및 규제 변화 등 배당 위협 요소를 나열하세요."},
            "05 최종 결정": {"file": "05_CIO_Decision_Matrix.md", "guide": "당신은 CIO입니다. 종합하여 최종 매수/보류/매도 의견을 내리세요."}
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
            
            # 기술 점수
            tech_score = 0
            div_yield = info.get('dividendYield', 0) * 100
            if 3.0 <= div_yield <= 8.0: tech_score += 50
            if info.get('currentPrice', 0) > info.get('twoHundredDayAverage', 0): tech_score += 50
            
            # 뉴스 분석
            titles = [n.get('title') or "제목 없음" for n in news[:5]]
            prompt = f"{ticker} 뉴스 요약: {' / '.join(titles)}\n투자 심리를 '긍정/중립/주의'로 판별하고 이유를 써줘."
            resp = self.client.messages.create(model=self.model, max_tokens=500, messages=[{"role": "user", "content": prompt}])
