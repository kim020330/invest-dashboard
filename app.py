import streamlit as st
import pandas as pd
import numpy as np
import os
import mojito
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 다크 테마 느낌의 스타일링
st.set_page_config(page_title="Jiho's Quant Command", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border: 1px solid #f0f2f6; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .agent-card { padding: 20px; border-radius: 15px; margin-bottom: 20px; color: white; }
    .alpha-card { background: linear-gradient(135deg, #007AFF, #00C6FF); }
    .guardian-card { background: linear-gradient(135deg, #FF9500, #FFCC00); }
    </style>
    """, unsafe_allow_html=True)

# 🔥 10초 자동 갱신
st_autorefresh(interval=10000, key="f5_refresh")

# 2. 증권사 연결 설정
KIS_KEY = "PSgiUu1bjrkWomUVvox8tsQtJPS71JHJeuPi"
KIS_SECRET = "B1put3i5vYVCEiaqbvWdHgHh7oPPi/JSLEDTV3kvUEPS4WV10SuxYOth2mQh9vEjlzjY7QUwWT46ww3zz16tF0hwQOS9Z8iNqv9bcENmMPeshcvBMFN7j0mrhihgziFjffQWE2oBscFHaXQanfK57Z8YcdR9q66D0Inn2xXsiZZDYiMO8bU="
ACC_NO = "50177946-01"

@st.cache_resource
def get_broker():
    try: return mojito.KoreaInvestment(api_key=KIS_KEY, api_secret=KIS_SECRET, acc_no=ACC_NO, exchange='나스닥', mock=True)
    except: return None

broker = get_broker()

# 3. 사이드바 내비게이션
with st.sidebar:
    st.title("🏛️ Jiho Terminal")
    st.info(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
    page = st.radio("섹션 선택", ["📊 포트폴리오 관제", "👥 AI 에이전트 전략실", "📜 전체 매매 장부"])
    st.divider()
    st.caption("Engine: V22 Hybrid AI")

# ==========================================
# [섹션 1] 포트폴리오 관제 (차트 강화)
# ==========================================
if page == "📊 포트폴리오 관제":
    st.header("Real-Time Portfolio Analysis")
    
    if broker:
        bal = broker.fetch_present_balance()
        holdings = bal.get('output1', [])
        
        if holdings:
            df = pd.DataFrame(holdings)
            df['profit'] = df['evlu_pfls_rt'].astype(float)
            df['amt'] = df['evlu_amt'].astype(float)
            
            # 💎 핵심 지표 (Metric Cards)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 평가 자산", f"${df['amt'].sum():,.2f}")
            m2.metric("평균 수익률", f"{df['profit'].mean():.2f}%", delta=f"{df['profit'].mean():.2f}%")
            m3.metric("최고 수익", f"{df['profit'].max():.2f}%", delta_color="normal")
            m4.metric("보유 종목", f"{len(df)} / 7")

            st.divider()

            # 📊 대시보드 차트 영역
            col1, col2 = st.columns([1, 1.2])
            with col1:
                st.subheader("🍕 자산 배분 비중")
                fig_pie = px.pie(df, values='amt', names='prdt_name', hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("📈 종목별 실시간 수익률")
                # 수익률에 따라 색상 자동 변경
                fig_bar = px.bar(df, x='prdt_name', y='profit', color='profit',
                                 color_continuous_scale='RdYlGn', range_color=[-1.5, 1.5])
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("📝 상세 보유 현황")
            st.dataframe(df[['prdt_name', 'ccld_qty_1', 'pchs_avg_pric', 'now_pric', 'profit']], use_container_width=True)
        else:
            st.info("현재 운용 중인 종목이 없습니다. 봇이 사냥을 시작하면 데이터가 나타납니다.")

# ==========================================
# [섹션 2] AI 에이전트 전략실 (브리핑 복구)
# ==========================================
elif page == "👥 AI 에이전트 전략실":
    st.header("AI Strategy Briefing")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="agent-card alpha-card">
            <h3>📈 추세 분석가 '지호-알파'</h3>
            <hr>
            <p><b>현재 전략:</b> 공격적 스캘핑</p>
            <p>RSI가 낮은 애플과 엔비디아의 저점 매수 기회를 노리고 있습니다. 예측 수익률 0.3% 이상일 때 적극적으로 진입합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("""
        <div class="agent-card guardian-card">
            <h3>🛡️ 리스크 관리자 '지호-가디언'</h3>
            <hr>
            <p><b>현재 전략:</b> 자산 방어 우선</p>
            <p>최대 종목 수를 7개로 제한하여 예수금을 확보했습니다. -1.5% 도달 시 기계적인 손절을 준비 중입니다.</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# [섹션 3] 전체 매매 장부 (로그)
# ==========================================
elif page == "📜 전체 매매 장부":
    st.header("Full Trade History")
    if os.path.exists('quant_trade_log.csv'):
        # 에러 방지용 on_bad_lines='skip' 유지
        df_log = pd.read_csv('quant_trade_log.csv', on_bad_lines='skip')
        st.dataframe(df_log.iloc[::-1], use_container_width=True)
    else:
        st.write("아직 기록된 매매가 없습니다.")
