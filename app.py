import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Quantamental 터미널", layout="wide", page_icon="🕵️‍♂️")

class HybridInvestmentEngine:
    def __init__(self):
        # API 키 로드
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("❌ [.streamlit/secrets.toml] 파일에 API 키가 없습니다.")
            st.stop()
            
        self.model = "claude-sonnet-4-6" 
        self.workspace_dir = "Dividend_Securities_Workspace"
        
        # 분석 파이프라인 구성 및 파일별 기본 지침 내용
        self.pipeline_config = {
            "01 핵심 철학": {"file": "01_Core_Philosophy.md", "guide": "당신은 배당 성장 투자 전문가입니다. 기업의 배당 정책이 장기적으로 지속 가능한지, 경영진의 주주 환원 의지가 강력한지 분석하세요."},
            "02 매크로 분석": {"file": "02_Macro_Analysis.md", "guide": "당신은 거시경제 전문가입니다. 현재의 금리 환경, 환율, 인플레이션이 해당 산업과 기업에 미치는 영향을 분석하세요."},
            "03 펀더멘탈": {"file": "03_Fundamental_Analysis.md", "guide": "당신은 재무 분석가입니다. 현금흐름표를 중심으로 기업의 실제 현금 창출 능력과 부채 상환 능력을 파헤치세요."},
            "04 리스크 관리": {"file": "04_Risk_Management.md", "guide": "당신은 리스크 관리자입니다. 경쟁사 출현, 규제 변화, 원가 상승 등 해당 기업의 배당을 위협할 모든 요소를 나열하세요."},
            "05 최종 결정 (CIO)": {"file": "05_CIO_Decision_Matrix.md", "guide": "당신은 최고투자책임자(CIO)입니다. 앞선 4단계의 분석을 종합하여 최종 '매수/보류/매도' 의견과 비중 조절 제안을 내리세요."}
        }

        # [자동화] 폴더 및 파일 자동 생성 로직
        self._ensure_workspace_setup()

    def _ensure_workspace_setup(self):
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
        
        for name, config in self.pipeline_config.items():
            path = os.path.join(self.workspace_dir, config["file"])
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"# {name} 분석 가이드\n{config['guide']}")

    def get_hybrid_signals(self, ticker_symbol):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            news = getattr(stock, 'news', [])
            
            # 기술 점수 계산 (간단 버전)
            tech_score = 0
            div_yield = info.get('dividendYield', 0) * 100
            if 3.0 <= div_yield <= 8.0: tech_score += 50
            if info.get('currentPrice', 0) > info.get('twoHundredDayAverage', 0): tech_score += 50
            
            # 뉴스 분석
            valid_titles = [n.get('title') or n.get('heading') for n in news[:5] if n.get('title') or n.get('heading')]
            news_context = "\n".join(valid_titles) if valid_titles else "최근 관련 뉴스 없음"
            
            prompt = f"{ticker_symbol} 관련 뉴스 요약:\n{news_context}\n\n위 뉴스를 기반으로 투자 심리를 '긍정/중립/주의'로 판별하고 이유를 1문장으로 써줘."
            resp = self.client.messages.create(model=self.model, max_tokens=500, messages=[{"role": "user", "content": prompt}])
            
            return {"tech_score": tech_score, "sentiment": resp.content[0].text, "info": info, "news": news[:5]}
        except Exception as e:
            st.error(f"데이터 수집 중 오류: {e}")
            return None

    def run_full_analysis(self, company_name, ticker, context_data):
        all_reports = {}
        progress_bar = st.progress(0)
        
        for i, (name, config) in enumerate(self.pipeline_config.items()):
            # 파일 읽기
            path = os.path.join(self.workspace_dir, config["file"])
            with open(path, "r", encoding="utf-8") as f:
                instruction = f.read()
            
            # AI 분석 요청
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=instruction,
                messages=[{"role": "user", "content": f"기업: {company_name}({ticker})\n맥락: {context_data}\n\n위 가이드에 맞춰 분석해줘."}]
            )
            all_reports[name] = response.content[0].text
            progress_bar.progress((i + 1) / len(self.pipeline_config))
        
        return all_reports

# UI 실행
engine = HybridInvestmentEngine()

st.success("✅ 지호의 투자 터미널이 가동 준비를 마쳤습니다!")

with st.sidebar:
    st.header("🏢 분석 설정")
    t_name = st.text_input("기업명", "리얼티인컴")
    t_ticker = st.text_input("티커", "O")
    analyze_btn = st.button("🚀 분석 엔진 점화")

if analyze_btn:
    with st.spinner("📡 데이터 수집 및 분석 중... (약 1분 소요)"):
        signals = engine.get_hybrid_signals(t_ticker)
        if signals:
            st.subheader(f"📡 {t_name} 실시간 시그널")
            c1, c2 = st.columns([1, 2])
            c1.metric("기술 점수", f"{signals['tech_score']}/100")
            c2.info(signals['sentiment'])
            
            reports = engine.run_full_analysis(t_name, t_ticker, signals['sentiment'])
            if reports:
                tabs = st.tabs(list(reports.keys()))
                for i, (name, content) in enumerate(reports.items()):
                    with tabs[i]:
                        st.markdown(content)
else:
    st.info("왼쪽 사이드바에 분석할 기업 정보를 넣고 버튼을 눌러주세요!")
