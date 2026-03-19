import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Pro 배당주 분석기", layout="wide", page_icon="📈")

class DividendProEngine:
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

    # [신규] 실시간 금융 데이터 가져오기 함수
    def get_stock_data(self, ticker_symbol):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # 주요 지표 추출
            data = {
                "현재가": info.get("currentPrice", "N/A"),
                "시가총액": info.get("marketCap", "N/A"),
                "배당수익률": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else "N/A",
                "PER": info.get("trailingPE", "N/A"),
                "52주 최고가": info.get("fiftyTwoWeekHigh", "N/A"),
                "52주 최저가": info.get("fiftyTwoWeekLow", "N/A"),
                "통화": info.get("currency", "USD")
            }
            return data
        except:
            return None

    def _read_md_file(self, filename):
        path = os.path.join(self.workspace_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "파일을 읽을 수 없습니다."

    def run_full_analysis(self, company_name, ticker, market_data):
        all_reports = {}
        # 실시간 데이터를 AI에게 맥락으로 전달
        context = f"--- [실시간 시장 데이터: {company_name} ({ticker})] ---\n"
        for k, v in market_data.items():
            context += f"{k}: {v}\n"
        context += "-------------------------------------------\n\n"

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(self.pipeline):
            status_text.text(f"⏳ {step['name']} 분석 중...")
            instruction = self._read_md_file(step["file"])
            
            user_msg = f"기업명: {company_name}\n\n[현재 시장 상황 및 이전 분석]\n{context}\n\n위 데이터를 기반으로 '{step['name']}' 분석을 수행해."

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=instruction,
                    messages=[{"role": "user", "content": user_msg}],
                    thinking={"type": "disabled"}
                )
                result = response.content[0].text
                all_reports[step["name"]] = result
                context += f"[{step['name']} 결과]: {result[:300]}...\n"
            except Exception as e:
                st.error(f"오류: {str(e)}")
                break
            
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        return all_reports

# 3. UI 부분
st.title("🏛️ 지호의 Pro 배당주 분석 시스템")
engine = DividendProEngine()

# 입력창을 두 개로 분리 (이름과 티커)
col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("기업명 (예: 애플)", placeholder="삼성전자")
with col2:
    ticker = st.text_input("티커/종목코드 (예: AAPL, 005930.KS)", placeholder="005930.KS")

if st.button("🚀 실시간 데이터 기반 통합 분석 시작"):
    if company_name and ticker:
        with st.spinner("실시간 시장 데이터를 수집 중..."):
            market_data = engine.get_stock_data(ticker)
            
        if market_data:
            # 상단에 시장 데이터 요약 표시
            st.success(f"📊 {company_name} 실시간 지표 로드 완료")
            cols = st.columns(len(market_data))
            for idx, (label, value) in enumerate(market_data.items()):
                cols[idx].metric(label, f"{value:,}" if isinstance(value, (int, float)) else value)
            
            # AI 분석 실행
            results = engine.run_full_analysis(company_name, ticker, market_data)
            
            if results:
                tabs = st.tabs(list(results.keys()))
                for i, (name, content) in enumerate(results.items()):
                    with tabs[i]:
                        st.markdown(content)
        else:
            st.error("티커가 올바르지 않거나 데이터를 가져올 수 없습니다.")
    else:
        st.warning("기업명과 티커를 모두 입력해주세요.")
