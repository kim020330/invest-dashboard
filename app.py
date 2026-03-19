import streamlit as st
import pandas as pd
import numpy as np
import os
import mojito
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh # 자동 새로고침 도구

# 1. 페이지 설정
st.set_page_config(page_title="Jiho's Live Terminal", layout="wide", page_icon="📈")

# 🔥 [실시간 핵심] 10초마다 페이지를 자동으로 새로고침합니다.
st_autorefresh(interval=10000, key="datarefresh")

# 2. 증권사 연결
KIS_KEY = "PSgiUu1bjrkWomUVvox8tsQtJPS71JHJeuPi"
KIS_SECRET = "B1put3i5vYVCEiaqbvWdHgHh7oPPi/JSLEDTV3kvUEPS4WV10SuxYOth2mQh9vEjlzjY7QUwWT46ww3zz16tF0hwQOS9Z8iNqv9bcENmMPeshcvBMFN7j0mrhihgziFjffQWE2oBscFHaXQanfK57Z8YcdR9q66D0Inn2xXsiZZDYiMO8bU="
ACC_NO = "50177946-01"

@st.cache_resource
def get_broker():
    try: return mojito.KoreaInvestment(api_key=KIS_KEY, api_secret=KIS_SECRET, acc_no=ACC_NO, exchange='나스닥', mock=True)
    except: return None

broker = get_broker()

# 3. 사이드바
with st.sidebar:
    st.title("🏛️ Jiho Live V21")
    st.info(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
    menu = st.radio("메뉴", ["🔴 실시간 모니터링", "📜 매매 히스토리"])

# ==========================================
# [메인] 실시간 모니터링 섹션
# ==========================================
if menu == "🔴 실시간 모니터링":
    st.header("Live Portfolio Performance")
    
    if broker:
        bal = broker.fetch_present_balance()
        holdings = bal.get('output1', [])
        
        if holdings:
            df_h = pd.DataFrame(holdings)
            df_h['evlu_amt'] = df_h['evlu_amt'].astype(float)
            df_h['profit_rt'] = df_h['evlu_pfls_rt'].astype(float)
            
            # 상단 핵심 지표
            total_val = df_h['evlu_amt'].sum()
            avg_rt = df_h['profit_rt'].mean()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("총 자산 가치", f"${total_val:,.2f}")
            col2.metric("평균 수익률", f"{avg_rt:.2f}%", delta=f"{avg_rt:.2f}%")
            col3.metric("운용 종목", f"{len(df_h)}개")

            st.divider()

            # 💹 실시간 수익률 변동 차트 (종목별 비교)
            st.subheader("📊 종목별 실시간 수익률 현황")
            # 수익률에 따라 색상 자동 변경 (초록/빨강)
            fig_bar = px.bar(df_h, x='prdt_name', y='profit_rt', 
                             color='profit_rt', color_continuous_scale='RdYlGn',
                             range_color=[-2, 2], # 손절/익절 범위 강조
                             labels={'prdt_name': '종목', 'profit_rt': '수익률(%)'})
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

            # 🍕 포트폴리오 비중 차트
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("🍕 자산 배분")
                fig_pie = px.pie(df_h, values='evlu_amt', names='prdt_name', hole=0.5)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                st.subheader("📝 상세 보유 현황")
                st.dataframe(df_h[['prdt_name', 'pchs_avg_pric', 'now_pric', 'profit_rt']], use_container_width=True)

        else:
            st.warning("현재 보유 중인 종목이 없습니다. 봇이 사냥을 시작하면 차트가 활성화됩니다.")

# ==========================================
# [로그] 매매 히스토리
# ==========================================
elif menu == "📜 매매 히스토리":
    st.header("Trade History Log")
    if os.path.exists('quant_trade_log.csv'):
        df_log = pd.read_csv('quant_trade_log.csv', on_bad_lines='skip')
        st.dataframe(df_log.sort_values(by=['Date', 'Time'], ascending=False), use_container_width=True)
