import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Final 배당주 터미널", layout="wide", page_icon="🏛️")

class DividendFinalEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키가 없습니다. .streamlit/secrets.toml을 확인하세요.")
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

    def get_history_data(self, ticker_symbol):
        try:
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(period="1y")
            dividends = stock.dividends
            return hist, dividends, stock.info
        except Exception as e:
            st.error(f"데이터 로드 실패: {e}")
            return None, None, None

    def _read_md_file(self, filename):
        path = os.path.join(self.workspace_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "지침 파일을 찾을 수 없습니다."

    def run_full_analysis(self, company_name, ticker, info):
        all_reports = {}
        context = f"기업명: {company_name}\n티커: {ticker}\n현재가: {info.get('currentPrice')}\n배당수익률: {info.get('dividendYield', 0)*100:.2f}%\n"
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(self.pipeline):
            status_text.text(f"⏳ {step['name']} 단계 분석 중...")
            instruction = self._read_md_file(step["file"])
            user_msg = f"분석 대상: {company_name}\n실시간 수치: {context}\n\n위 데이터를 바탕으로 '{step['name']}' 분석 리포트를 작성해줘."

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
                context += f"\n[{step['name']} 요약]: {result[:200]}..."
            except Exception as e:
                st.error(f"API 오류: {e}")
                break
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        status_text.text("✅ 분석 완료!")
        return all_reports

# 3. UI 메인 레이아웃
st.title("🏛️ 지호의 Final 배당주 투자 터미널")
st.caption(f"접속 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.divider()

engine = DividendFinalEngine()

# 사이드바 설정
with st.sidebar:
    st.header("🔍 분석 타겟 설정")
    target_name = st.text_input("기업 이름", "리얼티인컴")
    target_ticker = st.text_input("티커 (예: O, AAPL, 005930.KS)", "O")
    st.divider()
    run_btn = st.button("🚀 통합 분석 시스템 가동", use_container_width=True)
    st.info("Tip: 한국 주식은 종목코드 뒤에 .KS를 붙이세요.")

if run_btn:
    hist, divs, info = engine.get_history_data(target_ticker)
    
    if info:
        # 1. 상단 요약 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{info.get('currentPrice', 0):,.2f} {info.get('currency', 'USD')}")
        c2.metric("배당수익률", f"{info.get('dividendYield', 0)*100:.2f}%")
        c3.metric("PER", f"{info.get('trailingPE', 'N/A')}")
        c4.metric("시가총액", f"{info.get('marketCap', 0)/1e9:.1f}B")

        # 2. 메인 탭 구성
        t1, t2, t3 = st.tabs(["📊 차트 분석", "🔍 AI 심층 리포트", "📥 결과 저장"])

        with t1:
            st.subheader("실시간 주가 및 배당 히스토리")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="주가", line=dict(color="#1f77b4")))
            if not divs.empty:
                fig.add_trace(go.Bar(x=divs.index, y=divs.values, name="배당금", marker_color="#2ca02c", opacity=0.5), secondary_y=True)
            fig.update_layout(hovermode="x unified", template="plotly_white", height=500)
            st.plotly_chart(fig, use_container_width=True)

        with t2:
            reports = engine.run_full_analysis(target_name, target_ticker, info)
            if reports:
                sub_tabs = st.tabs(list(reports.keys()))
                full_report_text = f"=== {target_name} ({target_ticker}) 투자 분석 보고서 ===\n"
                full_report_text += f"날짜: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                
                for i, (name, content) in enumerate(reports.items()):
                    with sub_tabs[i]:
                        st.markdown(content)
                        full_report_text += f"## {name}\n{content}\n\n"

        with t3:
            st.subheader("분석 결과 내보내기")
            st.write("생성된 5단계 리포트를 텍스트 파일로 저장할 수 있습니다.")
            if 'full_report_text' in locals():
                st.download_button(
                    label="📥 전체 리포트 다운로드 (.txt)",
                    data=full_report_text,
                    file_name=f"{target_name}_분석보고서_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                st.success("리포트가 준비되었습니다. 위 버튼을 눌러 저장하세요.")
            else:
                st.warning("분석을 먼저 완료해주세요.")

else:
    st.write("← 사이드바에서 기업 정보를 입력하고 분석을 시작하세요.")
