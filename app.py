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
            reports[f_name] =
