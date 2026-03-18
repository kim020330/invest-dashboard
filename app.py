import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import anthropic # 🌟 새롭게 추가된 클로드 두뇌 라이브러리!

st.set_page_config(layout="wide", page_title="AI 퀀트 투자 비서 PRO")

st.title("🤖 실전 AI 퀀트 & 펀더멘털 투자 비서")
st.markdown("**복잡한 데이터는 AI가 분석할게요. 쉽고 친절한 해설을 읽고 투자 결정만 내리세요!**")
st.markdown("---")

# 1. 상단: 글로벌 거시 경제 대시보드
st.subheader("🌍 1. 지금 주식 시장의 날씨는? (거시 경제 지표)")
with st.expander("🎓 초보자를 위한 경제 지표 읽는 법 (클릭해서 펼쳐보세요)"):
    st.write("""
    - **S&P 500:** 미국을 대표하는 500개 기업의 평균 성적표입니다. 이 지수가 오르면 전체적인 시장 분위기가 좋다는 뜻이에요.
    - **국채 금리:** 은행 예금 이자가 아주 높아지면 사람들이 주식 대신 예금을 하겠죠? 국채 금리가 오르면 보통 주식 시장(특히 기술주)의 매력도가 떨어집니다.
    - **환율:** 미국 주식을 사려면 달러가 필요합니다. 환율이 너무 높을 때 사면 주식이 올라도 환율이 떨어지면 손해를 볼 수 있으니 주의해야 해요!
    """)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

def get_macro(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d")
        current = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        change = current - prev
        return current, change, (change/prev)*100
    except:
        return 0, 0, 0

tnx_c, tnx_chg, tnx_pct = get_macro("^TNX") 
usdkrw_c, usdkrw_chg, usdkrw_pct = get_macro("KRW=X")
sp500_c, sp500_chg, sp500_pct = get_macro("^GSPC")

col_m1.metric("S&P 500 (시장 흐름)", f"{sp500_c:,.2f}", f"{sp500_pct:.2f}%")
col_m2.metric("미국 10년물 국채 금리", f"{tnx_c:.3f}%", f"{tnx_pct:.2f}%", delta_color="inverse")
col_m3.metric("원/달러 환율", f"{usdkrw_c:,.2f}원", f"{usdkrw_pct:.2f}%", delta_color="inverse")
col_m4.info("👈 숫자 아래 화살표가 빨간색이면 하락, 초록색이면 상승을 의미해요!")

st.markdown("---")

# 2. 사이드바: 종목 검색 및 클로드 세팅
st.sidebar.header("🔍 심층 분석 종목 검색")
ticker_symbol = st.sidebar.text_input("티커를 입력하세요 (예: AAPL, MSFT, NVDA)", "AAPL").upper()
ticker_data = yf.Ticker(ticker_symbol)

info = ticker_data.info
company_name = info.get('shortName', ticker_symbol)
current_price = info.get('currentPrice', 0)

# 🌟 사이드바에 클로드 API 키 입력칸 추가
st.sidebar.markdown("---")
api_key = st.sidebar.text_input("🔑 클로드 API 키를 입력하세요", type="password")

# --- 💡 AI 투자 매력도 정밀 채점 로직 ---
st.header(f"🏢 2. {company_name} ({ticker_symbol}) 1차 기본 분석 리포트")
st.subheader(f"현재가: ${current_price:,.2f}" if current_price else "현재가: 데이터 없음")

score = 0
max_score = 6
ai_report = []

# [1] 가치 및 회계 분석
per = info.get('trailingPE', 0)
ev_ebitda = info.get('enterpriseToEbitda', 0) 

if per > 0 and ev_ebitda > 0:
    if per < 20 and ev_ebitda < 15:
        score += 2
        ai_report.append("🟢 **[가치 평가 - 저렴함]** 내 투자금을 빨리 회수할 수 있는 '가성비 좋은' 상태입니다. (PER, EV/EBITDA 우수)")
    elif per > 30 or ev_ebitda > 20:
        ai_report.append("🔴 **[가치 평가 - 비쌈]** 현재 회사가 버는 돈에 비해 주가가 꽤 비쌉니다. 인기가 너무 많아 거품이 끼었을 수 있어요.")
    else:
        score += 1
        ai_report.append("🟡 **[가치 평가 - 적절함]** 주가가 비싸지도, 싸지도 않은 시장 평균 수준입니다.")

# [2] 비즈니스 효율성
op_margin = info.get('operatingMargins', 0)
if op_margin > 0.20:
    score += 1
    ai_report.append(f"🟢 **[수익성 - 장사 잘함]** 1만 원어치를 팔면 {op_margin*100:.0f}천 원을 남기는 엄청난 알짜 기업입니다! (영업이익률 우수)")
elif op_margin > 0:
    ai_report.append(f"🟡 **[수익성 - 평범함]** 적자는 아니지만, 이익을 남기는 마진율({op_margin*100:.1f}%)이 평범한 수준입니다.")

# [3] 리스크 분석
df = ticker_data.history(period="1y")
if not df.empty:
    df['Daily Return'] = df['Close'].pct_change()
    annual_volatility = df['Daily Return'].std() * np.sqrt(252) * 100 
    
    if annual_volatility < 25:
        score += 1
        ai_report.append(f"🟢 **[안전성 - 든든함]** 주가가 위아래로 크게 널뛰지 않아서 마음 편하게 투자할 수 있는 종목입니다.")
    elif annual_volatility > 45:
        ai_report.append(f"🔴 **[안전성 - 위험함]** 롤러코스터처럼 주가 변동이 아주 심합니다. 초보자는 투자 금액을 줄이는 게 안전해요!")
    else:
        ai_report.append(f"🟡 **[안전성 - 보통]** 일반적인 수준의 주가 오르내림을 보여줍니다.")

# [4] 기술적 매매 타이밍
    df['20 SMA'] = df['Close'].rolling(window=20).mean()
    df['60 SMA'] = df['Close'].rolling(window=60).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    
    current_rsi = df['RSI'].iloc[-1]
    
    if current_rsi < 35:
        score += 2
        ai_report.append("🟢 **[매매 타이밍 - 바닥]** 최근 사람들이 너무 많이 팔아서 주가가 바닥일 확률이 높습니다. '줍줍'할 기회일 수 있어요! (RSI 과매도)")
    elif current_rsi > 70:
        ai_report.append("🔴 **[매매 타이밍 - 꼭지]** 단기간에 주가가 너무 올랐습니다. 조만간 사람들이 이익을 챙기려고 팔기 시작할 수 있으니 조심하세요. (RSI 과매수)")
    else:
        score += 1
        ai_report.append("🟡 **[매매 타이밍 - 중립]** 현재 특별히 과열되거나 침체되지 않은 안정적인 흐름입니다.")

# --- 1차 판정 UI ---
st.info("📊 **1차 퀀트 투자 의견 (규칙 기반)**")
col_score1, col_score2 = st.columns([1, 2.5])
with col_score1:
    st.metric("투자 매력도 (6점 만점)", f"{score} 점")
    st.progress(score / max_score)
    if score >= 5:
        st.success("🔥 **강력 매수 (지금 당장 관심 가져도 좋아요!)**")
    elif score >= 3:
        st.warning("👀 **분할 매수 (한 번에 다 사지 말고 조금씩 사보세요)**")
    else:
        st.error("🛑 **관망 (지금은 위험하니 지켜보기만 하세요)**")
        
with col_score2:
    for text in ai_report:
        st.write(text)

st.markdown("---")

# =====================================================================
# 🌟 진화된 클로드 수석 비서 심층 분석 영역 (RAG 도입) 🌟
# =====================================================================
st.header(f"🧠 3. 수석 비서 클로드의 '4대 투자 철학' 심층 리포트")

if st.button("✨ 실시간 뉴스 융합 심층 분석 시작하기", type="primary"):
    if not api_key:
        st.warning("👈 왼쪽 사이드바에 클로드 API 키를 먼저 입력해 주세요!")
    else:
        with st.spinner("최근 뉴스를 읽고 마케팅 전략과 비즈니스 해자를 심층 분석 중입니다... 🕵️‍♀️"):
            try:
                # 1. 실시간 뉴스 긁어오기 (최대 5개)
                news_list = ticker_data.news
                news_text = ""
                if news_list:
                    for i, news in enumerate(news_list[:5]):
                        title = news.get('title', '제목 없음')
                        publisher = news.get('publisher', '출처 없음')
                        news_text += f"{i+1}. [{publisher}] {title}\n"
                else:
                    news_text = "최근 주목할 만한 뉴스가 없습니다."

                # 2. 클로드 API 연결
                client = anthropic.Anthropic(api_key=api_key)
                
                # 3. 데이터 통합 및 프롬프트 생성
                prompt_data = f"""
                [분석 대상 기업: {company_name} ({ticker_symbol})]
                
                📊 재무 및 기술적 지표:
                - PER: {per:.2f} / EV/EBITDA: {ev_ebitda:.2f}
                - 영업이익률: {op_margin*100:.2f}%
                - 리스크(변동성): {annual_volatility:.2f}%
                
                📰 최근 핵심 뉴스 헤드라인:
                {news_text}
                
                당신은 아영님의 가상 증권사 수석 투자 비서입니다. 
                위의 재무 데이터와 실시간 뉴스를 종합하여 다음 4대 원칙을 매우 논리적이고 창의적으로 평가해 주세요.
                
                1. 안정적인 현금 흐름 창출 (재무 지표를 바탕으로 한 수익성 평가)
                2. 비즈니스 전략과 해자에 기반한 방어력 (최근 뉴스를 분석하여, 이 기업의 마케팅 파워, 브랜드 충성도, 시장 점유율 방어력이 뛰어난지 정성적으로 평가)
                3. 배당 성장 (복리의 마법)
                4. 철저한 자본 보호 (리스크 관리)
                
                답변은 대표님께 보고하듯 신뢰감 있으면서도 친절한 어조로 작성해 주세요. (가독성 좋은 마크다운 적극 활용)
                """
                
                response = client.messages.create(
                    model=model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt_data}]
                )
                
                st.success("✅ 실시간 뉴스 기반 4대 철학 심층 분석 완료!")
                st.info(response.content[0].text)
                
            except Exception as e:
                st.error(f"분석 중 오류가 발생했어요. API 키나 네트워크를 확인해 주세요!: {e}")

st.markdown("---")
# =====================================================================

# 3. 탭 구성
tab1, tab2, tab3 = st.tabs(["📉 쉬운 주가 차트", "📋 초보자용 재무 요약", "📰 실시간 뉴스"])

with tab1:
    if not df.empty:
        st.write("**최근 1년 주가 추세**")
        st.write("💡 파란 선(실제 주가)이 어떻게 움직이는지 눈으로 확인해 보세요.")
        st.line_chart(df['Close'])

with tab2:
    st.write("💡 **초보자 체크리스트:** 숫자가 마이너스(-)만 아니면 일단 합격! 'Total Revenue(매출)'가 꾸준히 커지는지 확인하세요.")
    financials = ticker_data.financials
    if not financials.empty:
        target_rows = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
        available_rows = [row for row in target_rows if row in financials.index]
        if available_rows:
            st.dataframe(financials.loc[available_rows], use_container_width=True)
        else:
            st.dataframe(financials)

with tab3:
    st.write("💡 회사에 안 좋은 사건이나 엄청난 호재가 있는지 기사 제목만 가볍게 훑어보세요.")
    news_list = ticker_data.news
    if news_list:
        for news in news_list[:5]:
            title = news.get('title', '제목 없음')
            link = news.get('link', '#')
            st.markdown(f"- **[{title}]({link})**")
