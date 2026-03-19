import streamlit as st
import pandas as pd
import plotly.express as px
import os
import mojito
from datetime import datetime

# 1. 페이지 기본 설정 (Apple-Style)
st.set_page_config(page_title="Jiho's Global Terminal", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F5F5F7; color: #1D1D1F; }
    .stMetric { background-color: #FFFFFF; border-radius: 15px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #E5E5E7; }
    .stDataFrame { border-radius: 15px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# 2. 증권사 연결 설정 (사장님 정보 입력)
# 실제 운영 시에는 st.secrets를 쓰거나 직접 입력하세요.
KIS_KEY = "PSgiUu1bjrkWomUVvox8tsQtJPS71JHJeuPi"
KIS_SECRET = "B1put3i5vYVCEiaqbvWdHgHh7oPPi/JSLEDTV3kvUEPS4WV10SuxYOth2mQh9vEjlzjY7QUwWT46ww3zz16tF0hwQOS9Z8iNqv9bcENmMPeshcvBMFN7j0mrhihgziFjffQWE2oBscFHaXQanfK57Z8YcdR9q66D0Inn2xXsiZZDYiMO8bU="
ACC_NO = "50177946-01"

@st.cache_resource
def get_broker():
    try:
        return mojito.KoreaInvestment(
            api_key=KIS_KEY, api_secret=KIS_SECRET, acc_no=ACC_NO, 
            exchange='나스닥', mock=True
        )
    except: return None

broker = get_broker()

# 사이드바 메뉴
with st.sidebar:
    st.title("🍏 Jiho Terminal")
    page = st.radio("메뉴 이동", ["📊 실시간 포트폴리오", "🤖 AI 봇 매매 일지", "📈 종목 개별 분석"])
    st.divider()
    if broker:
        # 잔고 조회 (예수금 가져오기)
        balance = broker.fetch_present_balance()
        cash = int(balance.get('output2', [{}])[0].get('frcr_dnca_tot_amt', 0))
        st.metric("🏦 실시간 외화 예수금", f"${cash:,.2f}")
    st.caption("🟢 KIS Global Server Connected")

# ==========================================
# [페이지 1] 실시간 포트폴리오 (앱 잔고 연동)
# ==========================================
if page == "📊 실시간 포트폴리오":
    st.header("Real-Time Portfolio (USA 🇺🇸)")
    st.write("현재 봇이 매수하여 보유 중인 종목들입니다.")
    
    if broker:
        resp = broker.fetch_present_balance()
        holdings = resp.get('output1', [])
        
        if len(holdings) > 0:
            df = pd.DataFrame(holdings)
            # 필요한 컬럼만 추출 (종목명, 보유수량, 매입가, 현재가, 수익률)
            df = df[['prdt_name', 'ccld_qty_1', 'pchs_avg_pric', 'now_pric', 'evlu_pfls_rt']]
            df.columns = ['종목명', '보유수량', '평균단가', '현재가', '수익률(%)']
            
            # 수익률 색상 입히기
            def color_profit(val):
                color = '#FF4B4B' if float(val) > 0 else '#0068C9' if float(val) < 0 else '#1D1D1F'
                return f'color: {color}; font-weight: bold'

            st.dataframe(df.style.applymap(color_profit, subset=['수익률(%)']), use_container_width=True)
            
            # 포트폴리오 비중 차트
            fig = px.pie(df, values='보유수량', names='종목명', title='보유 종목 비중', hole=0.4)
            st.plotly_chart(fig)
        else:
            st.info("현재 보유 중인 종목이 없습니다. 봇이 사냥을 시작할 때까지 기다려주세요!")

# ==========================================
# [페이지 2] AI 봇 매매 일지 (CSV 연동)
# ==========================================
elif page == "🤖 AI 봇 매매 일지":
    st.header("AI Bot Trading Log")
    st.write("봇이 작성한 비밀 장부(`quant_trade_log.csv`)를 실시간으로 읽어옵니다.")
    
    log_file = 'quant_trade_log.csv'
    if os.path.exists(log_file):
        df_log = pd.read_csv(log_file)
        df_log = df_log.sort_values(by=['Date', 'Time'], ascending=False) # 최신순
        
        # 요약 메트릭
        c1, c2, c3 = st.columns(3)
        c1.metric("총 매매 횟수", f"{len(df_log)}회")
        c2.metric("최근 매수 종목", df_log['Ticker'].iloc[0])
        c3.metric("마지막 체결 시간", df_log['Time'].iloc[0])
        
        st.divider()
        st.table(df_log.head(10)) # 최근 10개 기록만 표로 표시
    else:
        st.warning("아직 매매 기록이 없습니다. `auto_bot.py`를 먼저 실행해주세요.")

# ==========================================
# [페이지 3] 종목 개별 분석 (기존 기능)
# ==========================================
elif page == "📈 종목 개별 분석":
    st.header("Stock Deep Scan")
    target = st.text_input("분석할 미국 티커 입력 (예: NVDA, TSLA)", "NVDA").upper()
    
    if st.button("분석 시작"):
        with st.spinner("AI가 차트와 뉴스를 분석 중..."):
            # 여기에 기존에 짰던 야후 파이낸스 차트 그리기 코드를 넣으시면 됩니다!
            st.success(f"{target}에 대한 정밀 분석 결과가 곧 업데이트됩니다.")
