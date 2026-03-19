import streamlit as st
import pandas as pd
import os
import mojito
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Jiho's Command Center", layout="wide")
st_autorefresh(interval=10000, key="f5") # 10초마다 자동 갱신

# [설정]
KIS_KEY = "PSgiUu1bjrkWomUVvox8tsQtJPS71JHJeuPi"
KIS_SECRET = "B1put3i5vYVCEiaqbvWdHgHh7oPPi/JSLEDTV3kvUEPS4WV10SuxYOth2mQh9vEjlzjY7QUwWT46ww3zz16tF0hwQOS9Z8iNqv9bcENmMPeshcvBMFN7j0mrhihgziFjffQWE2oBscFHaXQanfK57Z8YcdR9q66D0Inn2xXsiZZDYiMO8bU="
ACC_NO = "50177946-01"

@st.cache_resource
def get_broker():
    return mojito.KoreaInvestment(api_key=KIS_KEY, api_secret=KIS_SECRET, acc_no=ACC_NO, exchange='나스닥', mock=True)

broker = get_broker()

st.title("🏛️ Jiho AI Quant Terminal V22")

if broker:
    bal = broker.fetch_present_balance()
    holdings = bal.get('output1', [])
    
    if holdings:
        df = pd.DataFrame(holdings)
        df['profit'] = df['evlu_pfls_rt'].astype(float)
        df['amt'] = df['evlu_amt'].astype(float)
        
        # 상단 Metric
        c1, c2, c3 = st.columns(3)
        c1.metric("총 자산", f"${df['amt'].sum():,.2f}")
        c2.metric("평균 수익률", f"{df['profit'].mean():.2f}%")
        c3.metric("보유 종목", f"{len(df)} / 7")

        # 실시간 차트
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🍕 포트폴리오 비중")
            st.plotly_chart(px.pie(df, values='amt', names='prdt_name', hole=0.4), use_container_width=True)
        with col2:
            st.subheader("📊 실시간 수익률")
            st.plotly_chart(px.bar(df, x='prdt_name', y='profit', color='profit', color_continuous_scale='RdYlGn'), use_container_width=True)
    else:
        st.info("현재 사냥 중인 종목이 없습니다.")

st.divider()
st.subheader("📜 최근 매매 기록")
if os.path.exists('quant_trade_log.csv'):
    st.dataframe(pd.read_csv('quant_trade_log.csv', on_bad_lines='skip').iloc[::-1], use_container_width=True)
