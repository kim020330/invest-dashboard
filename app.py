import streamlit as st
from anthropic import Anthropic
import os

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="지호의 배당주 분석 시스템 (디버깅 모드)", layout="wide")

# 2. 분석 엔진 클래스 (에러 추적 강화형)
class DividendInvestmentEngine:
    def __init__(self):
        # secrets.toml 확인
        if "ANTHROPIC_API_KEY" in st.secrets:
            self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        else:
            st.error("❌ [.streamlit/secrets.toml] 파일에서 API 키를 찾을 수 없습니다.")
            st.stop()
            
        # 404 에러가 나면 이 모델 이름을 하나씩 바꿔볼 거야
       # 1순위 추천: 가장 똑똑한 4.6 모델
self.model = "claude-4-6-sonnet-latest" 

# 만약 위 이름이 안 되면, 지호가 본 번호 그대로 명시:
# self.model = "claude-4-6-sonnet-20260115" (워크벤치에서 확인한 날짜가 있다면) 
        self.workspace_dir = "Dividend_Securities_Workspace"
        
        # 분석 파이프라인 구성
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
            status_text.text(f"⏳ {step['name']} 분석 중 (모델: {self.model})...")
            instruction = self._read_md_file(step["file"])
            
            user_msg = f"기업명: {company_name}\n\n[이전 단계 요약]\n{context}\n\n위 내용을 바탕으로 '{step['name']}' 단계를 수행해줘."

            try:
                # --- API 호출부 ---
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
                # 🛠️ 지호야, 이 부분이 핵심이야! 에러의 정체를 화면에 낱낱이 공개해.
                error_type = type(e).__name__
                error_msg = str(e)
                
                # 화면에 빨간 경고창 띄우기
                st.error(f"🚨 {step['name']} 단계에서 서버 응답 오류가 발생했습니다!")
                with st.expander("🔍 상세 에러 로그 보기 (이 내용을 나한테 알려줘)"):
                    st.code(f"Error Type: {error_type}\nMessage: {error_msg}")
                
                all_reports[step["name"]] = f"⚠️ 분석 실패: {error_type}"
                # 에러가 나면 더 진행하지 않고 멈춤
                break
            
            progress_bar.progress((i + 1) / len(self.pipeline))
        
        return all_reports

# 3. UI 메인 화면
st.title("🏛️ 지호의 배당주 가상 증권사")
st.divider()

engine = DividendInvestmentEngine()

# 기업 입력
target = st.text_input("분석할 기업명을 입력하세요", placeholder="예: 코카콜라, 리얼티인컴")

if st.button("🚀 전체 파이프라인 가동"):
    if target:
        results = engine.run_full_analysis(target)
        
        if results:
            tabs = st.tabs(list(results.keys()))
            for i, (name, content) in enumerate(results.items()):
                with tabs[i]:
                    st.markdown(content)
    else:
        st.warning("기업명을 입력해주세요.")
