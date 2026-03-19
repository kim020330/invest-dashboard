import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Quantamental 터미널", layout="wide", page_icon="🕵️‍♂️")

# [디버깅] 메인 화면에 즉시 로드 확인 메시지 출력
st.success("✅ 시스템 엔진 로드 완료! 왼쪽 사이드바에서 기업을 입력하세요.")

class HybridInvestmentEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("❌ API 키를 찾을 수 없습니다. secrets.toml 파일을 확인하세요.")
            st.stop()
            
        self.model = "claude-sonnet-4-6" 
        self.workspace_dir = "Dividend_Securities_Workspace"

    def get_hybrid_signals(self, ticker_symbol):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            news = stock.news[:5]
            
            # 기술 점수 계산
            tech_score = 0
            div_yield = info.get('dividendYield', 0) * 100
            if 3.0 <= div_yield <= 8.0: tech_score += 50
            if info.get('currentPrice', 0) > info.get('twoHundredDayAverage', 0): tech_score += 50
            
            # 뉴스 분석
            news_titles = "\n".join([n['title'] for n in news])
            prompt = f"다음 뉴스들이 {ticker_symbol} 투자에 긍정적인지 '긍정/중립/주의'로 판단해줘:\n{news_titles}"
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"tech_score": tech_score, "sentiment": response.content[0].text, "news": news, "info": info}
        except Exception as e:
            st.error(f"데이터 수집 중 오류: {e}")
            return None

# UI 구성
engine = HybridInvestmentEngine()

# 사이드바 (여기가 중요해 지호야!)
with st.sidebar:
    st.header("🎯 분석 설정")
    t_name = st.text_input("기업명", "리얼티인컴")
    t_ticker = st.text_input("티커", "O")
    analyze_btn = st.button("🚀 하이브리드 분석 시작")

# 메인 화면 초기 안내
if not analyze_btn:
    st.info("💡 **사용 방법:** 왼쪽 사이드바에서 기업명(예: 애플)과 티커(예: AAPL)를 입력하고 버튼을 누르세요.")
    st.write("---")
    st.markdown("### 📊 현재 감시 중인 추천 종목 예시")
    st.code("미국: O (리얼티인컴), AVGO (브로드컴), AAPL (애플)\n한국: 005930.KS (삼성전자), 088980.KS (맥쿼리인프라)")

if analyze_btn:
    # (이후 분석 로직은 기존과 동일...)
    signals = engine.get_hybrid_signals(t_ticker)
    if signals:
        st.subheader(f"📡 {t_name} 실시간 시그널")
        st.write(signals['sentiment'])
        # ... 추가 분석 내용 ...
