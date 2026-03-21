"""
app.py

Jiho Quant Terminal — Streamlit 대시보드 진입점.

페이지별 렌더링 로직은 dashboard/ 패키지에 위임한다.
이 파일은 설정, CSS 주입, 자동 갱신, 라우팅만 담당한다.
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from dashboard.theme import inject_css
from dashboard.components.sidebar import render_sidebar
from dashboard.pages import portfolio, strategy, journal

# ── 브로커 연결 (캐시) ────────────────────────────────────────
import mojito

KIS_KEY    = st.secrets["KIS_APP_KEY"]
KIS_SECRET = st.secrets["KIS_APP_SECRET"]
ACC_NO     = st.secrets["KIS_ACCOUNT"]


@st.cache_resource
def _get_broker():
    try:
        return mojito.KoreaInvestment(
            api_key=KIS_KEY, api_secret=KIS_SECRET,
            acc_no=ACC_NO, exchange="나스닥", mock=True,
        )
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
# 앱 설정 — 반드시 최상단에서 단 1회 호출
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Jiho Quant Terminal",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded",
)

# CSS 주입 (1회, React 안전)
inject_css()

# 10초 자동 갱신
st_autorefresh(interval=10_000, key="auto_refresh")

# ── 라우팅 ────────────────────────────────────────────────────
page   = render_sidebar()
broker = _get_broker()

if page == "📊 포트폴리오 관제":
    portfolio.render(broker)

elif page == "🤖 AI 전략실":
    strategy.render()

elif page == "📜 매매 장부":
    journal.render()
