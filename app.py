import streamlit as st
import pandas as pd
import numpy as np
import os
import mojito
import plotly.express as px
from datetime import datetime

# 1. 페이지 레이아웃 및 스타일 (Apple-Style)
st.set_page_config(page_title="Jiho's AI Strategy Terminal", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #ffffff; border: 1px solid #e1e4e8; padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .agent-card { background-color: #f8f9fa; border-left: 5px solid #007aff; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 증권사 연결 설정 (정보 입력 필수!)
KIS_KEY = "PSgiUu1bjrkWomUVvox8tsQtJPS71JHJeuPi"
KIS_SECRET = "B1put3i5vYVCEiaqbvWdHgHh7oPPi/JSLEDTV3kvUEPS4WV10SuxYOth2mQh9vEjlzjY7QUwWT46ww3zz16tF0hwQOS9Z8iNqv9bcENmMPeshcvBMFN7j0mrhihgziFjffQWE2oBscFHaXQanfK57Z8YcdR9q66D0Inn2xXsiZZDYiMO8bU="
ACC_NO = "50177946-01"

@st.cache_resource
def get_broker():
    try:
        return mojito.KoreaInvestment(api_key=KIS_KEY, api_secret=KIS_SECRET, acc_no=ACC_NO, exchange='나스닥', mock=True)
    except: return None

broker = get_broker()

# 3. 사이드바 내비게이션
with st.sidebar:
    st.title("🏛️ Jiho Terminal")
    st.caption("AI Quant Trading System V19.1")
    page = st.radio("전략실 이동", ["📊 실시간 관제 센터", "👥 AI 에이전트 브리핑", "📑 전체 매매 히스토리"])
    st.divider()
    if broker:
        try:
            balance = broker.fetch_present_balance()
            cash = balance.get('output2', [{}])[0].get('frcr_dnca_tot_amt', 0)
            st.metric("🏦 가용 예수금", f"${float(cash):,.2f}")
        except: st.error("계좌 연결 확인 필요")

# ==========================================
# [섹션 1] 실시간 관제 센터
# ==========================================
if page == "📊 실시간 관제 센터":
    st.header("Real-Time Control Center")
    
    # 상단 요약 요약 (보유 잔고 기반)
    if broker:
        bal_resp = broker.fetch_present_balance()
        holdings = bal_resp.get('output1', [])
        
        if holdings:
            df_h = pd.DataFrame(holdings)
            df_h = df_h[['prdt_name', 'ccld_qty_1', 'pchs_avg_pric', 'now_pric', 'evlu_pfls_rt']]
            df_h.columns = ['종목명', '수량', '평단가', '현재가', '수익률(%)']
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📦 현재 보유 포트폴리오")
                st.dataframe(df_h.style.background_gradient(subset=['수익률(%)'], cmap='RdYlGn'), use_container_width=True)
            with c2:
                st.subheader("🎯 자산 배분 현황")
                fig = px.pie(df_h, values='수량', names='종목명', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("현재 보유 중인 종목이 없습니다. 봇의 사냥을 기다려주세요.")

    st.divider()
    
    # 최근 매매 내역 (로그 기반)
    st.subheader("⚡ 최근 AI 매매 시그널")
    LOG_FILE = 'quant_trade_log.csv'
    if os.path.exists(LOG_FILE):
        # [해결책] on_bad_lines='skip'을 사용하여 데이터 불일치 에러 방지
        df_log = pd.read_csv(LOG_FILE, on_bad_lines='skip').sort_values(by=['Date', 'Time'], ascending=False)
        if not df_log.empty:
            st.dataframe(df_log.head(10), use_container_width=True)
        else: st.write("로그 데이터가 비어있습니다.")

# ==========================================
# [섹션 2] AI 에이전트 브리핑
# ==========================================
elif page == "👥 AI 에이전트 브리핑":
    st.header("AI Strategy Briefing")
    st.write("로컬 AI 엔진이 분석한 시장의 거시적 흐름입니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="agent-card">
            <h3>📈 추세 분석가 '지호-알파'</h3>
            <p><b>포지션:</b> 공격적 수익 추구</p>
            <p>익절가를 0.8%로 낮춘 전략은 현재의 높은 변동성 장세에 최적화되어 있습니다. 단기 상승 추세가 뚜렷한 종목에 🔥강력 배팅 시그널을 보내고 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="agent-card" style="border-left-color: #FF9500;">
            <h3>🛡️ 리스크 관리자 '지호-가디언'</h3>
            <p><b>포지션:</b> 보수적 방어</p>
            <p>손절 라인을 -1.5%로 조정하여 급락에 대비하고 있습니다. 평단가 대비 1.2% 하락 시에만 추가 매수를 허용하여 자산의 안전성을 확보 중입니다.</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# [섹션 3] 전체 매매 히스토리
# ==========================================
elif page == "📑 전체 매매 히스토리":
    st.header("Full Trade History")
    LOG_FILE = 'quant_trade_log.csv'
    if os.path.exists(LOG_FILE):
        df_full = pd.read_csv(LOG_FILE, on_bad_lines='skip')
        st.download_button("엑셀(CSV)로 다운로드", data=df_full.to_csv(index=False).encode('utf-8-sig'), file_name="trade_history.csv")
        st.dataframe(df_full.sort_values(by=['Date', 'Time'], ascending=False), use_container_width=True)
