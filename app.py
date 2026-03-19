import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 1. 페이지 설정
st.set_page_config(page_title="지호의 Pro 배당주 터미널", layout="wide", page_icon="🏦")

class DividendVisualEngine:
    def __init__(self):
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("API 키가 없습니다.")
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

    # [신규] 시각화용 데이터 가져오기 (주가 및 배당)
    def get_history_data(self, ticker_symbol):
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="1y") # 1년치 데이터
        dividends = stock.dividends
        return hist, dividends, stock.info

    def _read_md_file(self, filename):
        path = os.path.join(self.workspace_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "파일 읽기 실패"

    def run_full_analysis(self, company_name, ticker, info):
        all_reports = {}
        # AI에게 수치 데이터를 요약해서 전달
        context = f"기업: {company_name}\nPER: {info.get('trailingPE')}\n배당수익률: {info.get('dividendYield', 0)*100:.2f}%\n"
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(self.pipeline):
            status_text.text(f"⏳ {step['name']} 단계 분석 중...")
            instruction = self._read_md_file(step["file"])
            user_msg = f"{company_name} 분석 데이터:\n{context}\n\n위 내용을 바탕으로 '{step['name']}' 단계를 수행해줘."

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
                context += f"[{step['name']}]: {result[:200]}...\n"
            except Exception as e:
                st.error(f"오류: {str(e)}")
                break
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        return all_reports

# 3. UI 메인
st.title("🏦 지호의 Pro 배당주 터미널")
engine = DividendVisualEngine()

with st.sidebar:
    st.header("⚙️ 분석 설정")
    company_name = st.text_input("기업명", "리얼티인컴")
    ticker = st.text_input("티커", "O")
    run_btn = st.button("🚀 통합 분석 및 시각화 시작")

if run_btn:
    with st.spinner("데이터 로드 중..."):
        hist, dividends, info = engine.get_history_data(ticker)
        
    # 상단 요약 지표
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재 주가", f"{info.get('currentPrice', 0):,.2f} {info.get('currency', 'USD')}")
    col2.metric("배당 수익률", f"{info.get('dividendYield', 0)*100:.2f}%")
    col3.metric("PER (주가수익비율)", f"{info.get('trailingPE', 'N/A')}")
    col4.metric("시가총액", f"{info.get('marketCap', 0)/1e9:.1f}B")

    # 탭 구성 (시각화 탭 + AI 분석 탭)
    main_tabs = st.tabs(["📊 데이터 센터", "🔍 AI 정밀 분석"])

    with main_tabs[0]:
        st.subheader(f"📈 {company_name} 주가 및 배당 흐름")
        
        # 주가 차트 (Plotly)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="주가", line=dict(color="#1f77b4", width=2)))
        
        # 배당금 표시 (있는 경우)
        if not dividends.empty:
            recent_divs = dividends[dividends.index >= hist.index[0]]
            fig.add_trace(go.Bar(x=recent_divs.index, y=recent_divs.values, name="배당금", marker_color="#2ca02c", opacity=0.6), secondary_y=True)
            
        fig.update_layout(title_text=f"{company_name} 1년 주가 흐름", hovermode="x unified", template="plotly_white")
        fig.update_yaxes(title_text="주가 ($)", secondary_y=False)
        fig.update_yaxes(title_text="배당금 ($)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    with main_tabs[1]:
        # AI 분석 실행
        results = engine.run_full_analysis(company_name, ticker, info)
        if results:
            sub_tabs = st.tabs(list(results.keys()))
            for i, (name, content) in enumerate(results.items()):
                with sub_tabs[i]:
                    st.markdown(content)

else:
    st.info("왼쪽 사이드바에서 기업 정보를 입력하고 분석 버튼을 눌러주세요.")
