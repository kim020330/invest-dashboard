import streamlit as st
import pandas as pd
import numpy as np
import os
import mojito
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ══════════════════════════════════════════════════════════════════
# 0. 페이지 설정
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Jiho Quant Terminal",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# 1. CSS — 단 1회 주입, 구조 불변 (React 안전)
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Base ─────────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"] {
    background-color: #0D0D0F !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] {
    background-color: #0A0A0C !important;
    border-right: 1px solid #1E1E2E !important;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }

p, span, label { color: #E8E8F0 !important; }
h1, h2, h3, h4  { color: #FFFFFF !important; font-weight: 600 !important; }
hr               { border-color: #1E1E2E !important; }

/* ── st.metric() → Bloomberg 카드 ────────────────────── */
[data-testid="stMetric"] {
    background-color: #141418 !important;
    border: 1px solid #1E1E2E !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 0 18px rgba(0,143,251,0.18) !important;
    border-color: rgba(0,143,251,0.35) !important;
}
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] p {
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: #6B6B8A !important;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 22px !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
    font-variant-numeric: tabular-nums !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}

/* ── Sidebar 요소 ─────────────────────────────────────── */
.sb-logo  {
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px; font-weight: 700;
    color: #008FFB !important; letter-spacing: 2.5px;
}
.sb-time  {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: #00D4AA !important; margin-top: 4px;
}
.sb-badge {
    display: inline-block;
    background: rgba(0,212,170,0.08);
    border: 1px solid rgba(0,212,170,0.25);
    color: #00D4AA !important;
    font-size: 9px; font-weight: 700;
    padding: 3px 9px; border-radius: 20px;
    letter-spacing: 1.2px; margin-top: 10px;
}
.sb-meta { font-size: 10px; color: #4A4A6A !important; line-height: 1.9; }

/* ── Radio ────────────────────────────────────────────── */
[data-testid="stRadio"] label { color: #A0A0C0 !important; }

/* ── 섹션 헤더 ────────────────────────────────────────── */
.sec-hdr { font-size: 20px; font-weight: 700; color: #FFFFFF !important; letter-spacing: -0.2px; }
.sec-sub { font-size: 12px; color: #6B6B8A !important; letter-spacing: 0.3px; }
.blk-lbl {
    display: block;
    font-size: 11px; font-weight: 700;
    color: #E8E8F0 !important; letter-spacing: 0.8px; text-transform: uppercase;
    padding-bottom: 8px; border-bottom: 1px solid #1E1E2E;
}

/* ── 에이전트 카드 (정적 HTML — 구조 불변) ──────────── */
.agent-card {
    background: #141418; border: 1px solid #1E1E2E;
    border-radius: 12px; padding: 22px 24px;
}
.agent-card.alpha    { border-left: 3px solid #008FFB; }
.agent-card.guardian { border-left: 3px solid #00D4AA; }
.agent-tag   { display: inline-block; font-size: 9px; font-weight: 700; letter-spacing: 1.4px; padding: 3px 9px; border-radius: 4px; margin-bottom: 10px; text-transform: uppercase; }
.tag-blue    { background: rgba(0,143,251,0.12); color: #008FFB !important; }
.tag-green   { background: rgba(0,212,170,0.12); color: #00D4AA !important; }
.agent-title { font-size: 14px; font-weight: 600; color: #FFFFFF !important; margin-bottom: 10px; }
.agent-body  { font-size: 13px; color: #8080A0 !important; line-height: 1.65; }
.agent-body b { color: #E8E8F0 !important; }

/* ── 데이터 테이블 ────────────────────────────────────── */
.dt-wrap { background: #141418; border: 1px solid #1E1E2E; border-radius: 10px; overflow: hidden; margin-top: 8px; }
.dt      { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }
.dt th   { background: #0D0D0F; color: #6B6B8A !important; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.4px; padding: 11px 14px; border-bottom: 1px solid #1E1E2E; text-align: left; }
.dt td   { padding: 10px 14px; border-bottom: 1px solid #16161E; font-size: 12px; color: #E8E8F0 !important; }
.dt tr:last-child td { border-bottom: none; }
.dt tr:hover td      { background: rgba(255,255,255,0.02); }
.mono    { font-family: 'JetBrains Mono', monospace !important; }

/* ── 시그널 뱃지 ──────────────────────────────────────── */
.bdg      { display: inline-block; font-size: 9px; font-weight: 700; letter-spacing: 1px; padding: 3px 9px; border-radius: 4px; text-transform: uppercase; }
.bdg-buy  { background: rgba(0,212,170,0.12); color: #00D4AA !important; }
.bdg-sell { background: rgba(255,69,96,0.12);  color: #FF4560 !important; }
.bdg-hold { background: rgba(107,107,138,0.10); color: #6B6B8A !important; }

/* ── Dataframe ────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1E1E2E !important; border-radius: 8px !important;
}

/* ── 스피너 ───────────────────────────────────────────── */
.stSpinner > div { border-top-color: #008FFB !important; }

/* ── 빈 상태 ──────────────────────────────────────────── */
.empty-state { background: #141418; border: 1px dashed #1E1E2E; border-radius: 12px; padding: 56px 24px; text-align: center; }
.empty-title { font-size: 15px; font-weight: 600; color: #E8E8F0 !important; }
.empty-sub   { font-size: 12px; color: #6B6B8A !important; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 2. 자동 갱신
# ══════════════════════════════════════════════════════════════════
st_autorefresh(interval=10_000, key="auto_refresh")

# ══════════════════════════════════════════════════════════════════
# 3. 차트 테마 헬퍼
# ══════════════════════════════════════════════════════════════════
_COLORS = ["#008FFB","#00D4AA","#FEB019","#FF4560","#775DD0","#00E396","#FF66C3","#A5978B"]

_LAYOUT = dict(
    paper_bgcolor="#141418",
    plot_bgcolor="#141418",
    font=dict(family="Inter, sans-serif", color="#A0A0C0", size=11),
    margin=dict(l=12, r=12, t=40, b=12),
    legend=dict(bgcolor="rgba(20,20,24,0.9)", bordercolor="#1E1E2E",
                borderwidth=1, font=dict(color="#A0A0C0", size=11)),
    colorway=_COLORS,
)
_AXIS = dict(
    gridcolor="#1A1A28", zeroline=False,
    linecolor="#1E1E2E", tickfont=dict(color="#6B6B8A", size=10),
)


def apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        **_LAYOUT,
        title=dict(text=title, font=dict(color="#C8C8D8", size=13, family="Inter"), x=0.01),
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


# ══════════════════════════════════════════════════════════════════
# 4. 브로커 연결
# ══════════════════════════════════════════════════════════════════
KIS_KEY    = st.secrets["KIS_APP_KEY"]
KIS_SECRET = st.secrets["KIS_APP_SECRET"]
ACC_NO     = st.secrets["KIS_ACCOUNT"]


@st.cache_resource
def get_broker():
    try:
        return mojito.KoreaInvestment(
            api_key=KIS_KEY, api_secret=KIS_SECRET,
            acc_no=ACC_NO, exchange="나스닥", mock=True,
        )
    except Exception:
        return None


broker = get_broker()

# ══════════════════════════════════════════════════════════════════
# 5. 사이드바 — HTML을 단 1회 호출로 배치
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # 동적 시간 포함이지만 구조(태그)는 불변 → React 안전
    st.markdown(
        f'<p class="sb-logo">&#9889; JIHO TERMINAL</p>'
        f'<p class="sb-time">LIVE &nbsp; {datetime.now().strftime("%H:%M:%S")}</p>'
        f'<span class="sb-badge">&#9679; MOCK TRADING</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    page = st.radio(
        "NAVIGATION",
        ["📊 포트폴리오 관제", "🤖 AI 전략실", "📜 매매 장부"],
    )
    st.divider()
    st.markdown(
        '<p class="sb-meta">'
        "ENGINE &nbsp;&#183; V23 HYBRID AI<br>"
        "MAX POS &nbsp;&#183; 7<br>"
        "PROFIT &nbsp;&nbsp;&#183; +0.7 %<br>"
        "STOP &nbsp;&nbsp;&nbsp;&nbsp;&#183; &#8722;1.5 %<br>"
        "REFRESH &nbsp;&#183; 10 s"
        "</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — 포트폴리오 관제
# ══════════════════════════════════════════════════════════════════
if page == "📊 포트폴리오 관제":

    # 헤더 — 1회 호출, 구조 불변
    st.markdown(
        '<p class="sec-hdr">PORTFOLIO COMMAND CENTER</p>'
        '<p class="sec-sub">실시간 포트폴리오 관제 &nbsp;&#183;&nbsp; 10초 자동 갱신</p>',
        unsafe_allow_html=True,
    )

    if not broker:
        st.error("브로커 연결 실패 — .streamlit/secrets.toml 을 확인하세요.")
        st.stop()

    try:
        bal      = broker.fetch_present_balance()
        holdings = bal.get("output1", [])
    except Exception as e:
        st.warning(f"잔고 조회 실패: {e}")
        holdings = []

    if holdings:
        df = pd.DataFrame(holdings)
        df["profit"] = df["evlu_pfls_rt"].astype(float)
        df["amt"]    = df["evlu_amt"].astype(float)
        df["cost"]   = df["pchs_avg_pric"].astype(float) * df["ccld_qty_1"].astype(float)

        total_val    = df["amt"].sum()
        total_pnl    = total_val - df["cost"].sum()
        avg_profit   = df["profit"].mean()
        best_idx     = df["profit"].idxmax()
        worst_profit = df["profit"].min()

        # ── KPI 카드 — 완전 네이티브 st.metric() (HTML 없음) ──
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("총 평가 자산",  f"${total_val:,.0f}")
        c2.metric("오늘 P&L",      f"${total_pnl:+,.0f}",       delta=f"{avg_profit:+.2f}%")
        c3.metric("평균 수익률",   f"{avg_profit:+.2f}%",         delta=f"{avg_profit:+.2f}%")
        c4.metric("최고 종목",     df.loc[best_idx, "prdt_name"], delta=f"{df.loc[best_idx,'profit']:+.2f}%")
        c5.metric("최대 낙폭",     f"{worst_profit:.2f}%",         delta=f"{worst_profit:.2f}%")
        c6.metric("포지션",        f"{len(df)} / 7")

        st.divider()

        # ── 차트 행 ───────────────────────────────────────────
        col1, col2 = st.columns([1, 1.35])

        with col1:
            fig_donut = go.Figure(go.Pie(
                labels=df["prdt_name"],
                values=df["amt"],
                hole=0.64,
                textinfo="label+percent",
                textfont=dict(size=10, color="#E8E8F0"),
                marker=dict(
                    colors=_COLORS[:len(df)],
                    line=dict(color="#0D0D0F", width=2),
                ),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_donut.add_annotation(
                text=f"<b>${total_val:,.0f}</b>",
                x=0.5, y=0.56,
                font=dict(size=17, color="#FFFFFF", family="JetBrains Mono"),
                showarrow=False,
            )
            fig_donut.add_annotation(
                text="TOTAL AUM",
                x=0.5, y=0.43,
                font=dict(size=9, color="#6B6B8A", family="Inter"),
                showarrow=False,
            )
            apply_theme(fig_donut, "ASSET ALLOCATION")
            fig_donut.update_layout(showlegend=False, height=310)
            # key= 로 React 노드 고정
            st.plotly_chart(fig_donut, use_container_width=True, key="chart_donut")

        with col2:
            bar_colors = ["#00D4AA" if p >= 0 else "#FF4560" for p in df["profit"]]
            fig_bar = go.Figure(go.Bar(
                x=df["prdt_name"],
                y=df["profit"],
                marker=dict(color=bar_colors, line=dict(width=0), opacity=0.85),
                hovertemplate="<b>%{x}</b><br>수익률: %{y:.2f}%<extra></extra>",
            ))
            fig_bar.add_hline(
                y=0.7,  line=dict(color="#00D4AA", width=1, dash="dot"),
                annotation_text="익절 +0.7%",
                annotation_font=dict(color="#00D4AA", size=10),
                annotation_position="top right",
            )
            fig_bar.add_hline(
                y=-1.5, line=dict(color="#FF4560", width=1, dash="dot"),
                annotation_text="손절 -1.5%",
                annotation_font=dict(color="#FF4560", size=10),
                annotation_position="bottom right",
            )
            fig_bar.add_hline(y=0, line=dict(color="#2A2A3A", width=1))
            apply_theme(fig_bar, "REAL-TIME P&L BY POSITION")
            fig_bar.update_layout(height=310, yaxis_ticksuffix="%")
            st.plotly_chart(fig_bar, use_container_width=True, key="chart_bar_pnl")

        # ── 포지션 상세 — 단일 st.markdown() 1회 호출 ────────
        st.markdown('<span class="blk-lbl">POSITION DETAIL</span>', unsafe_allow_html=True)

        rows_html = []
        for _, row in df.iterrows():
            p  = row["profit"]
            pc = "#00D4AA" if p >= 0 else "#FF4560"
            pi = "▲" if p >= 0 else "▼"
            rows_html.append(
                f"<tr>"
                f"<td style='font-weight:600;color:#FFFFFF!important;'>{row['prdt_name']}</td>"
                f"<td class='mono'>{int(float(row['ccld_qty_1']))}주</td>"
                f"<td class='mono'>${float(row['pchs_avg_pric']):.2f}</td>"
                f"<td class='mono'>${float(row['now_pric']):.2f}</td>"
                f"<td class='mono'>${row['amt']:,.0f}</td>"
                f"<td class='mono' style='color:{pc}!important;font-weight:600;'>{pi} {p:.2f}%</td>"
                f"</tr>"
            )
        st.markdown(
            "<div class='dt-wrap'><table class='dt'>"
            "<thead><tr>"
            "<th>종목명</th><th>수량</th><th>평균단가</th>"
            "<th>현재가</th><th>평가금액</th><th>수익률</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody>"
            "</table></div>",
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            "<div class='empty-state'>"
            "<div style='font-size:36px;margin-bottom:14px;'>🎯</div>"
            "<div class='empty-title'>포지션 없음</div>"
            "<div class='empty-sub'>봇이 매수 시그널을 스캔 중입니다.</div>"
            "</div>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — AI 전략실
# ══════════════════════════════════════════════════════════════════
elif page == "🤖 AI 전략실":

    st.markdown(
        '<p class="sec-hdr">AI STRATEGY LAB</p>'
        '<p class="sec-sub">실시간 기술적 지표 분석 &nbsp;&#183;&nbsp; yfinance 라이브 데이터 (60초 캐시)</p>',
        unsafe_allow_html=True,
    )

    STOCKS = [
        ("NVDA","엔비디아"), ("TSLA","테슬라"),  ("AAPL","애플"),
        ("MSFT","마이크로소프트"), ("AMD","AMD"),  ("AMZN","아마존"),
        ("META","메타"),    ("GOOGL","구글"),   ("TQQQ","나스닥3배"),
        ("SOXL","반도체3배"),
    ]

    # 에이전트 카드 — 완전 정적 HTML, 구조·값 모두 불변 → React 안전
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            "<div class='agent-card alpha'>"
            "<span class='agent-tag tag-blue'>ALPHA ENGINE</span>"
            "<div class='agent-title'>📈 추세 분석가 · 지호-알파</div>"
            "<div class='agent-body'>"
            "<b>현재 전략:</b> 공격적 스캘핑<br><br>"
            "RSI &lt; 40 과매도 구간 우선 진입. 예측 수익률 0.3% 이상 + RSI &lt; 70 동시 충족 시 매수 집행."
            "</div></div>",
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            "<div class='agent-card guardian'>"
            "<span class='agent-tag tag-green'>GUARDIAN ENGINE</span>"
            "<div class='agent-title'>🛡️ 리스크 관리자 · 지호-가디언</div>"
            "<div class='agent-body'>"
            "<b>현재 전략:</b> 자산 방어 우선<br><br>"
            "최대 포지션 7개 상한 유지. -1.5% 도달 즉시 기계적 손절."
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── 시장 데이터 수집 ──────────────────────────────────────
    @st.cache_data(ttl=60)
    def fetch_market_data(tickers: tuple) -> list:
        results = []
        for ticker, name in tickers:
            try:
                raw = yf.download(ticker, period="30d", progress=False, auto_adjust=True)
                if raw.empty or len(raw) < 15:
                    continue
                close  = raw["Close"].squeeze()
                delta  = close.diff()
                gain   = delta.where(delta > 0, 0.0).rolling(14).mean()
                loss   = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
                rs     = gain / loss.replace(0, np.nan)
                rsi    = float((100 - 100 / (1 + rs)).iloc[-1])
                price  = float(close.iloc[-1])
                chg    = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
                vol    = float(close.pct_change().rolling(10).std().iloc[-1] * 100)
                signal = "BUY" if rsi < 30 else ("SELL" if rsi > 70 else "HOLD")
                results.append(dict(
                    ticker=ticker, name=name,
                    price=price, chg=chg, rsi=rsi, vol=vol, signal=signal,
                ))
            except Exception:
                pass
        return results

    with st.spinner("시장 데이터 로딩 중 …"):
        market_data = fetch_market_data(tuple(STOCKS))

    if not market_data:
        st.warning("시장 데이터를 불러오지 못했습니다. 네트워크를 확인하세요.")
        st.stop()

    # ── RSI 게이지 차트 — 각각 고유 key ──────────────────────
    st.markdown('<span class="blk-lbl">RSI LIVE SCANNER</span>', unsafe_allow_html=True)
    gauge_cols = st.columns(5)

    for i, d in enumerate(market_data[:10]):
        rsi = d["rsi"]
        if rsi < 40:
            bar_color, zone = "#FF4560", "과매도"
        elif rsi > 70:
            bar_color, zone = "#00D4AA", "과매수"
        else:
            bar_color, zone = "#008FFB", "중립"

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rsi,
            number=dict(
                font=dict(color="#FFFFFF", size=20, family="JetBrains Mono"),
                valueformat=".1f",
            ),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickvals=[0, 30, 50, 70, 100],
                    tickfont=dict(color="#4A4A6A", size=8),
                    tickwidth=1,
                    tickcolor="#1E1E2E",   # hex — Plotly 호환
                ),
                bar=dict(color=bar_color, thickness=0.55),
                bgcolor="#0D0D0F",
                borderwidth=0,
                steps=[
                    dict(range=[0,  30], color="rgba(255,69,96,0.07)"),
                    dict(range=[30, 70], color="rgba(0,143,251,0.04)"),
                    dict(range=[70,100], color="rgba(0,212,170,0.07)"),
                ],
                threshold=dict(
                    line=dict(color="#FEB019", width=2),
                    thickness=0.75, value=50,
                ),
            ),
            title=dict(
                text=f"<b>{d['ticker']}</b><br>"
                     f"<span style='font-size:9px;color:#6B6B8A'>{zone}</span>",
                font=dict(color="#E8E8F0", size=11, family="Inter"),
            ),
        ))
        fig_g.update_layout(
            paper_bgcolor="#141418",
            height=165,
            margin=dict(l=6, r=6, t=52, b=6),
            font=dict(family="Inter"),
        )
        gauge_cols[i % 5].plotly_chart(
            fig_g, use_container_width=True,
            key=f"chart_gauge_{d['ticker']}",  # 종목별 고유 key
        )

    st.divider()

    # ── 히트맵 ────────────────────────────────────────────────
    st.markdown('<span class="blk-lbl">MULTI-FACTOR SIGNAL HEATMAP</span>', unsafe_allow_html=True)

    rsi_c  = [d["rsi"] - 50 for d in market_data]
    chg_r  = [d["chg"]      for d in market_data]
    vol_r  = [d["vol"]      for d in market_data]
    tkrs   = [d["ticker"]   for d in market_data]

    fig_heat = go.Figure(go.Heatmap(
        z=[rsi_c, chg_r, vol_r],
        x=tkrs,
        y=["RSI (vs 50)", "일간 변동%", "변동성%"],
        colorscale=[[0.0,"#FF4560"],[0.5,"#1A1A2A"],[1.0,"#00D4AA"]],
        zmid=0,
        text=[
            [f"{d['rsi']:.1f}"  for d in market_data],
            [f"{v:+.2f}"        for v in chg_r],
            [f"{v:.2f}"         for v in vol_r],
        ],
        texttemplate="%{text}",
        textfont=dict(size=10, color="#FFFFFF", family="JetBrains Mono"),
        hovertemplate="<b>%{x}</b> · %{y}<br>값: %{z:.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#6B6B8A", size=9),
            bgcolor="#141418", bordercolor="#1E1E2E", borderwidth=1, thickness=12,
        ),
    ))
    apply_theme(fig_heat)
    fig_heat.update_layout(
        height=220,
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)",       # hex 'transparent' 대신 rgba
            tickfont=dict(color="#A0A0C0", size=11),
        ),
    )
    st.plotly_chart(fig_heat, use_container_width=True, key="chart_heatmap")

    st.divider()

    # ── 시그널 테이블 — 단일 st.markdown() 1회 호출 ──────────
    st.markdown('<span class="blk-lbl">LIVE SIGNAL TABLE</span>', unsafe_allow_html=True)

    sig_rows = []
    for d in market_data:
        cc = "#00D4AA" if d["chg"] >= 0 else "#FF4560"
        ci = "▲" if d["chg"] >= 0 else "▼"
        bc = {"BUY":"bdg-buy","SELL":"bdg-sell","HOLD":"bdg-hold"}[d["signal"]]
        sig_rows.append(
            f"<tr>"
            f"<td style='font-weight:700;color:#FFFFFF!important;'>{d['ticker']}</td>"
            f"<td style='color:#8080A0!important;'>{d['name']}</td>"
            f"<td class='mono'>${d['price']:.2f}</td>"
            f"<td class='mono' style='color:{cc}!important;'>{ci} {d['chg']:+.2f}%</td>"
            f"<td class='mono'>{d['rsi']:.1f}</td>"
            f"<td class='mono'>{d['vol']:.2f}%</td>"
            f"<td><span class='bdg {bc}'>{d['signal']}</span></td>"
            f"</tr>"
        )
    st.markdown(
        "<div class='dt-wrap'><table class='dt'>"
        "<thead><tr>"
        "<th>TICKER</th><th>종목</th><th>현재가</th>"
        "<th>일간 변동</th><th>RSI</th><th>변동성</th><th>시그널</th>"
        "</tr></thead>"
        f"<tbody>{''.join(sig_rows)}</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — 매매 장부
# ══════════════════════════════════════════════════════════════════
elif page == "📜 매매 장부":

    st.markdown(
        '<p class="sec-hdr">TRADE JOURNAL</p>'
        '<p class="sec-sub">전체 매매 이력 &nbsp;&#183;&nbsp; 누적 손익 분석</p>',
        unsafe_allow_html=True,
    )

    LOG_FILE = "quant_trade_log.csv"

    if os.path.exists(LOG_FILE):
        try:
            df_log = pd.read_csv(LOG_FILE, on_bad_lines="skip")
        except Exception as e:
            st.error(f"로그 파일 읽기 실패: {e}")
            st.stop()

        total_trades = len(df_log)
        if total_trades > 0 and df_log.shape[1] > 3:
            action_col  = df_log.columns[3]
            buy_trades  = int((df_log[action_col] == "BUY").sum())
            sell_trades = int((df_log[action_col] == "SELL").sum())
        else:
            buy_trades = sell_trades = 0

        # KPI — 네이티브 st.metric()
        kc1, kc2, kc3 = st.columns(3)
        kc1.metric("총 거래 횟수", f"{total_trades} 회")
        kc2.metric("매수 집행",    f"{buy_trades} 회")
        kc3.metric("매도 집행",    f"{sell_trades} 회")

        st.divider()
        st.markdown('<span class="blk-lbl">TRADE HISTORY (최신순)</span>', unsafe_allow_html=True)
        st.dataframe(
            df_log.iloc[::-1].reset_index(drop=True),
            use_container_width=True,
            height=420,
        )

    else:
        st.markdown(
            "<div class='empty-state'>"
            "<div style='font-size:36px;margin-bottom:14px;'>📋</div>"
            "<div class='empty-title'>기록 없음</div>"
            "<div class='empty-sub'>첫 번째 거래가 실행되면 여기에 장부가 생성됩니다.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
