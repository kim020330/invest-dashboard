import streamlit as st
from anthropic import Anthropic
import os

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="지호의 배당주 투자 시스템",
    layout="wide",
    page_icon="🏢"
)

# 2. 분석 엔진 클래스 (자동 키 로드 및 5단계 연쇄 분석)
class DividendInvestmentEngine:
    def __init__(self):
        # secrets.toml에서 키를 자동으로 가져옴
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("❌ API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인하세요.")
            st.stop()
            
        self.model = "claude-3-5-sonnet-latest" # 가장 안정적인 최신 모델
        self.workspace_dir = "Dividend_Securities_Workspace"
        
        # 지호가 만든 5단계 파일 리스트
        self.pipeline = [
            {"name": "01 핵심 철학", "file": "01_Core_Philosophy.md"},
            {"name": "02 매크로 분석", "file": "02_Macro_Analysis.md"},
            {"name": "03 펀더멘탈", "file": "03_Fundamental_Analysis.md"},
            {"name": "04 리스크 관리", "file": "04_Risk_Management.md"},
            {"name": "05 최종 결정 (CIO)", "file": "05_CIO_Decision_Matrix.md"}
        ]

    def _read_md_file(self, filename):
        path = os.path.join(self.workspace_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"오류: {filename} 파일을 찾을 수 없습니다."

    def run_full_analysis(self, company_name):
        all_reports = {}
        accumulated_context = "" # 이전 단계 분석 내용을 누적해서 다음 단계로 전달

        # 화면에 진행 상황 표시를 위한 준비
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(self.pipeline):
            status_text.text(f"⏳ {step['name']} 단계 진행 중...")
            
            # 매뉴얼 읽기
            instruction = self._read_md_file(step["file"])
            
            # 프롬프트 구성 (이전 단계의 맥락을 포함시켜 논리가 이어지게 함)
            user_prompt = f"분석 대상 기업: {company_name}\n\n"
            if accumulated_context:
                user_prompt += f"--- 이전 단계 분석 요약 ---\n{accumulated_context}\n\n"
            user_prompt += f"위 내용을 바탕으로 현재 단계인 '{step['name']}'의 지침에 따라 심층 분석을 수행해줘."

            try:
                # 클로드 API 호출
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    temperature=0, # 분석의 일관성을 위해 0으로 설정
                    system=instruction,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                report_content = response.content[0].text
                all_reports[step["name"]] = report_content
                
                # 다음 단계가 참고할 수 있게 현재 단계 요약 누적
                accumulated_context += f"[{step['name']} 결과 요약]: {report_content[:400]}...\n"
                
            except Exception as e:
                all_reports[step["name"]] = f"⚠️ 분석 중 오류 발생: {str(e)}"
            
            # 진행 바 업데이트
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        status_text.text("✅ 모든 분석이 완료되었습니다!")
        return all_reports

# 3. 메인 UI 화면
st.title("🏛️ 지호의 배당주 가상 증권사")
st.info("Dividend Securities Workspace의 5단계 정밀 분석 프로세스를 가동합니다.")

# 엔진 초기화
engine = DividendInvestmentEngine()

# 사이드바: 진행 순서 안내
with st.sidebar:
    st.header("📊 분석 프로세스")
    for step in engine.pipeline:
        st.write(f"🔹 {step['name']}")
    st.divider()
    st.write("🔑 API Status: **Connected** (Auto-loaded)")

# 기업 입력 및 분석 실행
company = st.text_input("분석할 종목명을 입력하세요 (예: 엔비디아, 코카콜라, 삼성전자)", placeholder="대상 기업 입력")

if st.button("🚀 5단계 통합 분석 시작"):
    if company:
        # 분석 수행
        reports = engine.run_full_analysis(company)
        
        # 결과를 5개의 탭으로 나누어 시각화
        tabs = st.tabs(list(reports.keys()))
        
        for i, (tab_name, content) in enumerate(reports.items()):
            with tabs[i]:
                st.markdown(f"## 🔍 {tab_name} 보고서")
                st.markdown(content)
                
                # 마지막 CIO 탭에는 특별 강조 효과
                if i == 4:
                    st.success("🎯 CIO 최종 투자의견 도출 완료")
    else:
        st.warning("분석할 기업명을 입력해 주세요.")
