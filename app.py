import streamlit as st
from anthropic import Anthropic
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 Apple Style CSS
st.set_page_config(page_title="Jiho's Elite Terminal", layout="wide", page_icon="🍏")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F5F5F7; color: #1D1D1F; }
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 20px; padding: 20px !important; box-shadow: 0 8px 30px rgba(0,0,0,0.04); border: 1px solid #E5E5E7; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #0071E3; color: white; border: none; padding: 10px; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E5E5E7; padding: 5px; border-radius: 15px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; background-color: transparent; color: #86868B; padding: 8px 20px; }
    .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #1D1D1F !important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    section[data-testid="stSidebar"] { background-color: #F5F5F7; border-right: 1px solid #E5E5E7; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 영구 저장 (CSV) 관련 함수
PORTFOLIO_FILE = "jiho_portfolio.csv"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    return pd.DataFrame(columns=["Date", "Ticker", "Name", "Quantity", "Buy_Price"])

def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

# 세션 상태 초기화
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = load_portfolio()

class JihoEliteEngine:
    def __init__(self):
        self.client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        self.model = "claude-sonnet-4-6"
        self.workspace_dir = "Dividend_Securities_Workspace"

    # [기능 3] 적정 주가 가치 평가 (Valuation Model)
    def calculate_fair_value(self, ticker, info):
        curr_price = info.get('currentPrice', 0)
        eps = info.get('trailingEps', 0)
        pe_ratio = info.get('trailingPE', 0)
        forward_pe = info.get('forwardPE', 0)
        div_yield = info.get('dividendYield', 0) * 100
        
        prompt = f"""
        기업: {ticker}
        현재가: ${curr_price}
        EPS: {eps}
        현재 P/E: {pe_ratio}
        Forward P/E: {forward_pe}
        배당수익률: {div_yield}%
        
        위 재무 데이터를 바탕으로 이 주식의 '적정 주가(Fair Value)'를 추정하고, 현재가 대비 저평가인지 고평가인지 분석해줘.
        분석은 (1) 수익성 기반 가치, (2) 배당 수익률 기반 가치, (3) 최종 결론 순서로 작성해줘.
        """
        resp = self.client.messages.create(model=self.model, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text

    def get_basic_data(self, ticker):
        stock = yf.Ticker(ticker)
        return stock.info, stock.history(period="1y")

# 3. UI 로직
engine = JihoEliteEngine()

with st.sidebar:
    st.title("🏛️ Jiho Elite")
    page = st.radio("Menu", ["Intelligence & Valuation", "Portfolio Analytics", "Global Briefing"])
    st.divider()
    st.write(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

# 페이지 1: 지능형 분석 및 가치 평가
if page == "Intelligence & Valuation":
    st.header("Stock Valuation Intelligence")
    col_in1, col_in2 = st.columns(2)
    with col_in1: t_ticker = st.text_input("Ticker Symbol", "AAPL")
    with col_in2: t_qty = st.number_input("Purchase Quantity (Optional)", min_value=0, value=10)
    
    if st.button("Run Professional Analysis"):
        with st.spinner("가치 평가 모델 가동 중..."):
            info, hist = engine.get_basic_data(t_ticker)
            valuation_report = engine.calculate_fair_value(t_ticker, info)
            
            # 상단 핵심 지표 카드
            c1, c2, c3 = st.columns(3)
            c1.metric("Current Price", f"${info.get('currentPrice')}")
            c2.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
            c3.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
            
            # 포트폴리오 추가 기능
            if st.button(f"Add {t_ticker} to Portfolio"):
                new_data = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Ticker": t_ticker,
                    "Name": info.get('shortName'),
                    "Quantity": t_qty,
                    "Buy_Price": info.get('currentPrice')
                }
                st.session_state.portfolio_df = pd.concat([st.session_state.portfolio_df, pd.DataFrame([new_data])], ignore_index=True)
                save_portfolio(st.session_state.portfolio_df)
                st.toast("포트폴리오가 안전하게 CSV에 저장되었습니다!")

            tab1, tab2 = st.tabs(["📊 Value Report", "📈 Market Performance"])
            with tab1:
                st.markdown(f"### 🎯 AI Intrinsic Value Analysis\n{valuation_report}")
            with tab2:
                fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#0071E3', width=2))])
                fig.update_layout(template="plotly_white", height=400)
                st.plotly_chart(fig, use_container_width=True)

# 페이지 2: 포트폴리오 분석 및 시각화
elif page == "Portfolio Analytics":
    st.header("Asset Allocation & Holdings")
    df = st.session_state.portfolio_df
    
    if not df.empty:
        # [기능 2] 비중 시각화 (Pie Chart)
        df['Total_Value'] = df['Quantity'] * df['Buy_Price']
        
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            st.markdown("#### Portfolio Weight")
            fig_pie = px.pie(df, values='Total_Value', names='Ticker', hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_p2:
            st.markdown("#### Holding Details")
            st.dataframe(df[['Ticker', 'Quantity', 'Buy_Price', 'Total_Value']], use_container_width=True)
            if st.button("Reset Portfolio"):
                st.session_state.portfolio_df = pd.DataFrame(columns=["Date", "Ticker", "Name", "Quantity", "Buy_Price"])
                save_portfolio(st.session_state.portfolio_df)
                st.rerun()
    else:
        st.info("포트폴리오가 비어 있습니다. 'Valuation' 메뉴에서 종목을 추가하세요.")

# 페이지 3: 글로벌 브리핑
elif page == "Global Briefing":
    st.header("Daily Market Pulse")
    st.write("실시간 글로벌 배당주 뉴스 및 거시경제 브리핑이 제공되는 공간입니다.")
    # (앞선 뉴스레터 로직을 여기에 동일하게 배치 가능)
