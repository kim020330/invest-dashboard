import streamlit as st
from anthropic import Anthropic
import os

# 1. 페이지 설정
st.set_page_config(page_title="지호의 배당주 분석 시스템", layout="wide", page_icon="📈")

# 2. 분석 엔진 클래스
class DividendInvestmentEngine:
    def __init__(self):
        # secrets.toml에서 키 로드
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("❌ [.streamlit/secrets.toml] 파일에서 API 키를 찾을 수 없습니다.")
            st.stop()
            
        # 지호가 워크벤치에서 확인한 최신 4-6 모델 적용
        self.model = "claude-3-5-sonnet-20241022" 
        self.workspace_dir = "Dividend_Securities_Workspace"
        
        # 분석 파이프라인 파일 목록
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
        except Exception as e:
            return f"❌ 파일 읽기 실패 ({filename}): {str(e)}"

    def run_full_analysis(self, company_name):
        all_reports = {}
        context = "" 
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, step in enumerate(self.pipeline):
            status_text.text(f"⏳ {step['name']} 분석 중...")
            instruction = self._read_md_file(step["file"])
            
            user_msg = f"기업명: {company_name}\n\n[이전 분석 요약]\n{context}\n\n위 흐름에 맞춰 '{step['name']}' 분석을 해줘."

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    system=instruction,
                    messages=[{"role": "user", "content": user_msg}]
                )
                result = response.content[0].text
                all_reports[step["name"]] = result
                context += f"[{step['name']}]: {result[:300]}...\n"
                
            except Exception as e:
                st.error(f"🚨 {step['name']} 단계 오류 발생!")
                st.code(f"Error: {str(e)}")
                break
            
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        return all_reports

# 3. UI 메인 실행부
st.title("🏛️ 지호의 배당주 가상 증권사")
st.divider()

engine = DividendInvestmentEngine()

target = st.text_input("분석할 기업명을 입력하세요", placeholder="예: 코카콜라, 리얼티인컴")

if st.button("🚀 5단계 파이프라인 분석 가동"):
    if target:
        results = engine.run_full_analysis(target)
        if results:
            tabs = st.tabs(list(results.keys()))
            for i, (name, content) in enumerate(results.items()):
                with tabs[i]:
                    st.markdown(content)
                    if i == 4:
                        st.success("🎯 최종 투자의견 도출 완료")
    else:
        st.warning("기업명을 입력해주세요.")
