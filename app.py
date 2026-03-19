import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import os

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Quantamental 터미널", layout="wide", page_icon="🕵️‍♂️")

# 시스템 로드 확인 메시지
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
            # 뉴스 가져오기 (데이터가 없을 경우 대비 빈 리스트 설정)
            news = getattr(stock, 'news', [])
            
            # 1. 기술 점수 계산
            tech_score = 0
            div_yield = info.get('dividendYield', 0) * 100
            curr_price = info.get('currentPrice', 0)
            avg_200 = info.get('twoHundredDayAverage', 0)

            if 3.0 <= div_yield <= 8.0: tech_score += 50
            if curr_price > avg_200 and avg_200 > 0: tech_score += 50
            
            # 2. 뉴스 분석 (에러 방지용 안전 로직 추가)
            valid_news = []
            if news:
                for n in news[:5]:
                    # 'title' 키가 있는지 확인하고 없으면 '제목 없음'으로 대체
                    title = n.get('title') or n.get('heading') or "제목 정보 없음"
                    valid_news.append(title)
            
            if valid_news:
                news_context = "\n".join(valid_news)
                prompt = f"다음 뉴스들이 {ticker_symbol} 투자 심리에 미치는 영향을 분석해줘:\n{news_context}\n\n'긍정/중립/주의' 중 하나로 시작하고 짧게 이유를 적어줘."
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                sentiment = response.content[0].text
            else:
                sentiment = "최근 관련 뉴스가 발견되지 않았습니다. 기술 지표 위주로 분석하세요."

            return {
                "tech_score": tech_score, 
                "sentiment": sentiment, 
                "news": news[:5], 
                "info": info
            }
        except Exception as e:
            st.error(f"⚠️ 데이터 수집 중 오류 발생: {str(e)}")
            return None

    # 5단계 심층 분석 실행 함수
    def run_full_analysis(self, company_name, ticker, context_data):
        all_reports = {}
        pipeline = [
            {"name": "01 핵심 철학", "file": "01_Core_Philosophy.md"},
            {"name": "02 매크로 분석", "file": "02_Macro_Analysis.md"},
            {"name": "03 펀더멘탈", "file": "03_Fundamental_Analysis.md"},
            {"name": "04 리스크 관리", "file": "04_Risk_Management.md"},
            {"name": "05 최종 결정 (CIO)", "file": "05_CIO_Decision_Matrix.md"}
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(pipeline):
            status_text.text(f"⏳ {step['name']} 단계 분석 중...")
            try:
                path = os.path.join(self.workspace_dir, step["file"])
                with open(path, "r", encoding="utf-8") as f:
                    instruction = f.read()
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=instruction,
                    messages=[{"role": "user", "content": f"기업: {company_name}\n상황: {context_data}"}]
                )
                all_reports[step["name"]] = response.content[0].text
            except Exception as e:
                all_reports[step["name"]] = f"분석 실패: {e}"
            
            progress_bar.progress((i + 1) / len(pipeline))
        
        status_text.text("✅ 모든 분석이 완료되었습니다!")
        return all_reports

# --- UI 실행부 ---
engine = HybridInvestmentEngine()

with st.sidebar:
    st.header("🎯 분석 설정")
    t_name = st.text_input("기업명", "리얼티인컴")
    t_ticker = st.text_input("티커", "O")
    analyze_btn = st.button("🚀 하이브리드 분석 시작")

if not analyze_btn:
    st.info("💡 왼쪽 사이드바에서 기업 정보를 입력하고 버튼을 누르세요.")

if analyze_btn:
    with st.spinner("📡 시그널 수집 중..."):
        signals = engine.get_hybrid_signals(t_ticker)
    
    if signals:
        st.subheader(f"📡 {t_name} 실시간 시그널")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("기술 점수", f"{signals['tech_score']}/100")
            st.progress(signals['tech_score']/100)
        with c2:
            st.info(signals['sentiment'])
        
        st.divider()
        
        # 메인 분석 실행
        with st.spinner("🔍 5단계 심층 리포트 생성 중... (약 1분 소요)"):
            reports = engine.run_full_analysis(t_name, t_ticker, signals['sentiment'])
            if reports:
                tabs = st.tabs(list(reports.keys()))
                for i, (name, content) in enumerate(reports.items()):
                    with tabs[i]:
                        st.markdown(content)
