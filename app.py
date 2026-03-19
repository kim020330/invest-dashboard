import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Quantamental 터미널", layout="wide", page_icon="🕵️‍♂️")

class HybridInvestmentEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키를 확인해주세요.")
            st.stop()
            
        self.model = "claude-sonnet-4-6" 
        self.workspace_dir = "Dividend_Securities_Workspace"
        self.pipeline = [
            {"name": "01 핵심 철학", "file": "01_Core_Philosophy.md"},
            {"name": "02 매크로 분석", "file": "02_Macro_Analysis.md"},
            {"name": "03 펀더멘탈", "file": "03_Fundamental_Analysis.md"},
            {"name": "04 리스크 관리", "file": "04_Risk_Management.md"},
            {"name": "05 최종 결정 (CIO)", "file": "05_CIO_Decision_Matrix.md"}
        ]

    # [기술+전략] 하이브리드 시그널 추출
    def get_hybrid_signals(self, ticker_symbol):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            news = stock.news[:5] # 최신 뉴스 5개
            
            # 1. 기술적 지표 계산 (Quantitative)
            tech_score = 0
            div_yield = info.get('dividendYield', 0) * 100
            payout_ratio = info.get('payoutRatio', 0) * 100
            
            if 3.0 <= div_yield <= 8.0: tech_score += 40  # 적정 배당률
            if payout_ratio <= 70: tech_score += 30      # 안정적 배당 성향
            if info.get('currentPrice', 0) > info.get('twoHundredDayAverage', 0): tech_score += 30 # 상승 추세
            
            # 2. 전략적 뉴스 분석 (Qualitative)
            news_titles = "\n".join([n['title'] for n in news])
            prompt = f"다음 뉴스 헤드라인들이 {ticker_symbol}의 투자 심리와 배당 안정성에 미치는 영향을 분석해줘.\n{news_titles}\n\n결론을 '긍정/중립/주의' 중 하나로 시작하고 짧은 이유를 적어줘."
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            sentiment_analysis = response.content[0].text
            
            return {
                "tech_score": tech_score,
                "sentiment": sentiment_analysis,
                "news": news,
                "info": info
            }
        except:
            return None

    def run_full_analysis(self, company_name, ticker, context_data):
        all_reports = {}
        context = f"기초 데이터: {context_data}\n"
        progress_bar = st.progress(0)
        
        for i, step in enumerate(self.pipeline):
            path = os.path.join(self.workspace_dir, step["file"])
            with open(path, "r", encoding="utf-8") as f:
                instruction = f.read()
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=instruction,
                messages=[{"role": "user", "content": f"{company_name} 분석: {context}"}]
            )
            all_reports[step["name"]] = response.content[0].text
            progress_bar.progress((i + 1) / len(self.pipeline))
        return all_reports

# 3. UI 구성
st.title("🕵️‍♂️ 지호의 Quantamental 투자 터미널")
engine = HybridInvestmentEngine()

with st.sidebar:
    st.header("🎯 타겟 설정")
    t_name = st.text_input("기업명", "리얼티인컴")
    t_ticker = st.text_input("티커", "O")
    analyze_btn = st.button("🚀 하이브리드 분석 시작", use_container_width=True)

if analyze_btn:
    with st.spinner("기술 지표 및 최신 뉴스 분석 중..."):
        signals = engine.get_hybrid_signals(t_ticker)
    
    if signals:
        # --- 상단 시그널 보드 ---
        st.subheader("📡 실시간 AI 하이브리드 시그널")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("기술 점수 (Quantitative)", f"{signals['tech_score']} / 100")
            st.progress(signals['tech_score'] / 100)
            st.caption("배당수익률, 배당성향, 주가 추세 기반")
            
        with col2:
            st.info(f"**전략적 뉴스 분석 (Qualitative)**\n\n{signals['sentiment']}")

        st.divider()

        # --- 메인 분석 탭 ---
        tab1, tab2 = st.tabs(["📊 데이터 센터", "🔍 5단계 심층 리포트"])
        
        with tab1:
            # 주가 차트 및 뉴스 리스트
            st.subheader("최신 주요 뉴스")
            for n in signals['news']:
                st.write(f"🔗 [{n['title']}]({n['link']})")
                
        with tab2:
            final_context = f"기술점수: {signals['tech_score']}, 뉴스감성: {signals['sentiment']}"
            reports = engine.run_full_analysis(t_name, t_ticker, final_context)
            if reports:
                sub_tabs = st.tabs(list(reports.keys()))
                for i, (name, content) in enumerate(reports.items()):
                    with sub_tabs[i]:
                        st.markdown(content)
