import streamlit as st
from anthropic import Anthropic
import os

# 1. 초기 설정 및 페이지 레이아웃
st.set_page_config(page_title="지호의 배당주 투자 시스템", layout="wide", page_icon="📈")

# 커스텀 CSS (UI를 좀 더 깔끔하게)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff; border-radius: 5px; padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 분석 엔진 (오케스트레이터) 정의
class DividendInvestmentEngine:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
        # 404 에러를 방지하기 위한 가장 안정적인 모델명 사용
        self.model = "claude-3-5-sonnet-20241022"
        # 지호가 만든 워크스페이스 파일 경로
        self.workspace_dir = "Dividend_Securities_Workspace"
        self.pipeline = [
            {"id": "01", "name": "핵심 철학", "file": "01_Core_Philosophy.md"},
            {"name": "매크로 분석", "file": "02_Macro_Analysis.md"},
            {"name": "펀더멘탈", "file": "03_Fundamental_Analysis.md"},
            {"name": "리스크 관리", "file": "04_Risk_Management.md"},
            {"name": "최종 결정", "file": "05_CIO_Decision_Matrix.md"}
        ]

    def _read_md_file(self, filename):
        path = os.path.join(self.workspace_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: {filename} 파일을 {self.workspace_dir} 폴더에서 찾을 수 없습니다."

    def run_full_analysis(self, company_name):
        all_reports = {}
        context = "" # 이전 단계 결과들을 누적할 텍스트

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(self.pipeline):
            status_text.text(f"⏳ {step['name']} 단계 분석 중...")
            
            instruction = self._read_md_file(step["file"])
            
            # 클로드에게 전달할 프롬프트 구성 (이전 단계 컨텍스트 포함)
            user_msg = f"분석 대상 기업: {company_name}\n\n"
            if context:
                user_msg += f"[참고: 이전 단계 분석 데이터]\n{context}\n\n"
            user_msg += f"위 내용을 바탕으로 현재 단계인 '{step['name']}'의 분석 매뉴얼에 따라 보고서를 작성해줘."

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    temperature=0.2,
                    system=instruction,
                    messages=[{"role": "user", "content": user_msg}]
                )
                report_content = response.content[0].text
                all_reports[step["name"]] = report_content
                
                # 다음 단계를 위해 현재 결과를 요약해서 컨텍스트에 추가
                context += f"\n--- {step['name']} 분석 요약 ---\n{report_content[:500]}...\n"
                
            except Exception as e:
                all_reports[step["name"]] = f"분석 중 오류 발생: {str(e)}"
            
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        status_text.text("✅ 모든 분석이 완료되었습니다!")
        return all_reports

# 3. 메인 UI 화면 구성
st.title("🏛️ 지호의 배당주 가상 증권사")
st.caption("Dividend Securities Workspace 기반 5단계 정밀 분석 파이프라인")

# API 키 확인
if "ANTHROPIC_API_KEY" not in st.secrets:
    st.error("❌ API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인하세요.")
    st.stop()

# 엔진 초기화
engine = DividendInvestmentEngine(st.secrets["ANTHROPIC_API_KEY"])

# 사이드바 설정
with st.sidebar:
    st.header("🏢 증권사 정보")
    st.info("현재 5개의 정예 에이전트가 가동 중입니다.")
    st.divider()
    st.write("1. 핵심 투자 철학 검토")
    st.write("2. 글로벌 매크로 환경 분석")
    st.write("3. 펀더멘탈 및 해자 검증")
    st.write("4. 리스크 및 변동성 통제")
    st.write("5. CIO 최종 의사결정")

# 기업 입력창
col1, col2 = st.columns([3, 1])
with col1:
    company = st.text_input("분석할 기업명을 입력하세요", placeholder="예: 삼성전자, 리얼티인컴, 엔비디아")

# 분석 실행
if st.button("🚀 5단계 통합 분석 시작"):
    if company:
        reports = engine.run_full_analysis(company)
        
        # 결과를 탭으로 나누어 표시
        tabs = st.tabs(list(reports.keys()))
        
        for i, (tab_name, report_text) in enumerate(reports.items()):
            with tabs[i]:
                st.markdown(f"### 📊 {tab_name} 보고서")
                st.markdown(report_text)
                
                # 마지막 CIO 결정 탭에는 특별한 디자인 추가
                if i == 4:
                    st.success("🎯 투자의견 결재가 완료되었습니다.")
    else:
        st.warning("기업명을 입력해주세요.")
