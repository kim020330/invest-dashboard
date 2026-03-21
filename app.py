import streamlit as st
import pandas as pd
import numpy as np
import os
import mojito
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ══════════════════════════════════════════════════════════════════
# 0. 페이지 설정 (가장 먼저 호출)
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Jiho Quant Terminal",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# 1. 글로벌 다크 테마 CSS
# ══════════════════════════════════════════════════════════════════
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Base ──────────────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
section[data-testid="stSidebar"] > div:first-child {
    background-color: #0D0D0F !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #0A0A0C !important;
    border-right: 1px solid #1E1E2E !important;
}
[data-testid="stHeader"]  { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }

/* ── 기본 텍스트 ───────────────────────────────────────────── */
p, span, div, label, li, td, th { color: #E8E8F0 !important; }
h1, h2, h3, h4, h5            { color: #FFFFFF  !important; font-weight: 600 !important; }
hr                             { border-color: #1E1E2E !important; }

/* ── Streamlit 기본 위젯 다크화 ────────────────────────────── */
[data-testid="stRadio"] > label            { color: #6B6B8A !important; font-size: 11px !important; font-weight: 600 !important; letter-spacing: 1.2px !important; text-transform: uppercase !important; }
[data-testid="stRadio"] div[role="radiogroup"] label { color: #A0A0C0 !important; font-size: 13px !important; text-transform: none !important; letter-spacing: 0 !important; }
[data-testid="stRadio"] div[role="radiogroup"] label:hover { color: #E8E8F0 !important; }
[data-testid="stInfo"]  { background: rgba(0,143,251,0.08) !important; border: 1px solid rgba(0,143,251,0.2) !important; border-radius: 8px !important; color: #A0A0C0 !important; }
[data-testid="stAlert"] { border-radius: 8px !important; }
.stSpinner > div        { border-top-color: #008FFB !important; }

/* ── Dataframe 다크화 ──────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1E1E2E !important;
    border-radius: 8px !important;
    overflow: hidden;
}
[data-testid="stDataFrame"] * { color: #E8E8F0 !important; background-color: #141418 !important; }

/* ══ KPI 카드 ════════════════════════════════════════════════ */
@keyframes glow-green {
    0%, 100% { box-shadow: 0 0 6px  rgba(0, 212, 170, 0.25); border-color: rgba(0, 212, 170, 0.30); }
    50%       { box-shadow: 0 0 18px rgba(0, 212, 170, 0.55); border-color: rgba(0, 212, 170, 0.60); }
}
@keyframes glow-red {
    0%, 100% { box-shadow: 0 0 6px  rgba(255, 69, 96, 0.25); border-color: rgba(255, 69, 96, 0.30); }
    50%       { box-shadow: 0 0 18px rgba(255, 69, 96, 0.55); border-color: rgba(255, 69, 96, 0.60); }
}
@keyframes glow-blue {
    0%, 100% { box-shadow: 0 0 5px  rgba(0, 143, 251, 0.20); border-color: #1E1E2E; }
    50%       { box-shadow: 0 0 14px rgba(0, 143, 251, 0.40); border-color: rgba(0, 143, 251, 0.40); }
}

.kpi-card {
    background: #141418;
    border: 1px solid #1E1E2E;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 8px;
    transition: transform 0.15s ease;
}
.kpi-card:hover      { transform: translateY(-2px); }
.kpi-card.positive   { animation: glow-green 2.8s ease-in-out infinite; }
.kpi-card.negative   { animation: glow-red   2.8s ease-in-out infinite; }
.kpi-card.neutral    { animation: glow-blue  3.5s ease-in-out infinite; }

.kpi-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.6px;
    color: #6B6B8A !important;
    margin-bottom: 10px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 24px;
    font-weight: 600;
    color: #FFFFFF !important;
    font-variant-numeric: tabular-nums;
    line-height: 1.15;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-delta        { font-family: 'JetBrains Mono', monospace !important; font-size: 12px; font-weight: 500; margin-top: 7px; }
.kpi-delta.up     { color: #00D4AA !important; }
.kpi-delta.down   { color: #FF4560 !important; }
.kpi-delta.flat   { color: #6B6B8A !important; }

/* ══ 에이전트 카드 ═══════════════════════════════════════════ */
.agent-card {
    background: #141418;
    border: 1px solid #1E1E2E;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 16px;
}
.agent-card.alpha    { border-left: 3px solid #008FFB; }
.agent-card.guardian { border-left: 3px solid #00D4AA; }

.agent-tag          { display: inline-block; font-size: 9px; font-weight: 700; letter-spacing: 1.4px; padding: 3px 9px; border-radius: 4px; margin-bottom: 10px; text-transform: uppercase; }
.tag-blue           { background: rgba(0,143,251,0.12); color: #008FFB !important; }
.tag-green          { background: rgba(0,212,170,0.12); color: #00D4AA !important; }
.agent-title        { font-size: 14px; font-weight: 600; color: #FFFFFF !important; margin-bottom: 10px; }
.agent-body         { font-size: 13px; color: #8080A0 !important; line-height: 1.65; }
.agent-body b       { color: #E8E8F0 !important; }

/* ══ 섹션 헤더 ═══════════════════════════════════════════════ */
.section-header { font-size: 20px; font-weight: 700; color: #FFFFFF !important; letter-spacing: -0.2px; margin-bottom: 2px; }
.section-sub    { font-size: 12px; color: #6B6B8A !important; margin-bottom: 18px; letter-spacing: 0.3px; }

/* ══ 사이드바 ════════════════════════════════════════════════ */
.sb-logo  { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 700; color: #008FFB !important; letter-spacing: 2.5px; }
.sb-time  { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00D4AA !important; margin-top: 4px; }
.sb-badge { display: inline-block; background: rgba(0,212,170,0.08); border: 1px solid rgba(0,212,170,0.25); color: #00D4AA !important; font-size: 9px; font-weight: 700; padding: 3px 9px; border-radius: 20px; letter-spacing: 1.2px; margin-top: 10px; }
.sb-meta  { font-size: 10px; color: #4A4A6A !important; line-height: 1.9; letter-spacing: 0.5px; }

/* ══ 시그널 테이블 ═══════════════════════════════════════════ */
.sig-table              { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }
.sig-table th           { background: #0D0D0F; color: #6B6B8A !important; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.4px; padding: 11px 14px; border-bottom: 1px solid #1E1E2E; text-align: left; }
.sig-table td           { padding: 10px 14px; border-bottom: 1px solid #16161E; font-size: 12px; }
.sig-table tr:last-child td { border-bottom: none; }
.sig-table tr:hover td  { background: rgba(255,255,255,0.025); }
.sig-table .mono        { font-family: 'JetBrains Mono', monospace !important; }

.badge { display: inline-block; font-size: 9px; font-weight: 700; letter-spacing: 1px; padding: 3px 9px; border-radius: 4px; text-transform: uppercase; }
.badge-buy  { background: rgba(0,212,170,0.12); color: #00D4AA !important; }
.badge-sell { background: rgba(255,69,96,0.12);  color: #FF4560 !important; }
.badge-hold { background: rgba(107,107,138,0.10); color: #6B6B8A !important; }

/* ══ 포지션 테이블 ═══════════════════════════════════════════ */
.pos-table-wrap { background: #141418; border: 1px solid #1E1E2E; border-radius: 10px; overflow: hidden; margin-top: 8px; }

/* ══ 빈 상태 UI ══════════════════════════════════════════════ */
.empty-state { background: #141418; border: 1px dashed #1E1E2E; border-radius: 12px; padding: 56px 24px; text-align: center; }
.empty-icon  { font-size: 36px; margin-bottom: 14px; }
.empty-title { font-size: 15px; font-weight: 600; color: #E8E8F0 !important; }
.empty-sub   { font-size: 12px; color: #6B6B8A !important; margin-top: 6px; }

/* ══ 구분선 라벨 ═════════════════════════════════════════════ */
.block-label { font-size: 11px; font-weight: 700; color: #E8E8F0 !important; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #1E1E2E; }
</style>
"""

# ══════════════════════════════════════════════════════════════════
# 2. 차트 공통 테마
# ══════════════════════════════════════════════════════════════════
_COLORS = ['#008FFB', '#00D4AA', '#FEB019', '#FF4560', '#775DD0', '#00E396', '#FF66C3', '#A5978B']

CHART_BASE = dict(
    paper_bgcolor='#141418',
    plot_bgcolor='#141418',
    font=dict(family='Inter, sans-serif', color='#A0A0C0', size=11),
    margin=dict(l=12, r=12, t=40, b=12),
    legend=dict(
        bgcolor='rgba(20,20,24,0.9)',
        bordercolor='#1E1E2E',
        borderwidth=1,
        font=dict(color='#A0A0C0', size=11),
    ),
    colorway=_COLORS,
)

_AXIS = dict(
    gridcolor='#1A1A28',
    zeroline=False,
    linecolor='#1E1E2E',
    tickfont=dict(color='#6B6B8A', size=10),
)


def apply_theme(fig: go.Figure, title: str = '') -> go.Figure:
    """모든 Plotly 차트에 다크 테마를 일괄 적용한다."""
    fig.update_layout(
        **CHART_BASE,
        title=dict(text=title, font=dict(color='#C8C8D8', size=13, family='Inter'), x=0.01),
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


# ══════════════════════════════════════════════════════════════════
# 3. KPI 카드 헬퍼
# ══════════════════════════════════════════════════════════════════
def kpi_card(label: str, value: str, delta: float | None = None) -> str:
    """글로우 애니메이션 KPI 카드 HTML을 반환한다."""
    if delta is None:
        card_cls, delta_html = 'neutral', ''
    elif delta > 0:
        card_cls    = 'positive'
        delta_html  = f'<div class="kpi-delta up">▲ {delta:+.2f}%</div>'
    elif delta < 0:
        card_cls    = 'negative'
        delta_html  = f'<div class="kpi-delta down">▼ {delta:.2f}%</div>'
    else:
        card_cls    = 'neutral'
        delta_html  = f'<div class="kpi-delta flat">― {delta:.2f}%</div>'

    return (
        f'<div class="kpi-card {card_cls}">'
        f'  <div class="kpi-label">{label}</div>'
        f'  <div class="kpi-value">{value}</div>'
        f'  {delta_html}'
        f'</div>'
    )


# ══════════════════════════════════════════════════════════════════
# 4. CSS 주입 + 자동 갱신
# ══════════════════════════════════════════════════════════════════
st.markdown(DARK_CSS, unsafe_allow_html=True)
st_autorefresh(interval=10_000, key='auto_refresh')

# ══════════════════════════════════════════════════════════════════
# 5. 브로커 연결
# ══════════════════════════════════════════════════════════════════
KIS_KEY    = st.secrets["KIS_APP_KEY"]
KIS_SECRET = st.secrets["KIS_APP_SECRET"]
ACC_NO     = st.secrets["KIS_ACCOUNT"]


@st.cache_resource
def get_broker():
    try:
        return mojito.KoreaInvestment(
            api_key=KIS_KEY, api_secret=KIS_SECRET,
            acc_no=ACC_NO, exchange='나스닥', mock=True,
        )
    except Exception:
        return None


broker = get_broker()

# ══════════════════════════════════════════════════════════════════
# 6. 사이드바
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sb-logo">⚡ JIHO TERMINAL</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sb-time">LIVE &nbsp; {datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sb-badge">● MOCK TRADING</div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)

    page = st.radio(
        'NAVIGATION',
        ['📊 포트폴리오 관제', '🤖 AI 전략실', '📜 매매 장부'],
    )

    st.divider()
    st.markdown(
        '<div class="sb-meta">'
        'ENGINE &nbsp;· V23 HYBRID AI<br>'
        'MAX POS &nbsp;· 7<br>'
        'PROFIT &nbsp;&nbsp;· +0.7 %<br>'
        'STOP &nbsp;&nbsp;&nbsp;&nbsp;· −1.5 %<br>'
        'REFRESH &nbsp;· 10 s'
        '</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — 포트폴리오 관제
# ══════════════════════════════════════════════════════════════════
if page == '📊 포트폴리오 관제':
    st.markdown('<div class="section-header">PORTFOLIO COMMAND CENTER</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">실시간 포트폴리오 관제 · 10초 자동 갱신</div>', unsafe_allow_html=True)

    if not broker:
        st.error('브로커 연결 실패 — .streamlit/secrets.toml 을 확인하세요.')
        st.stop()

    try:
        bal      = broker.fetch_present_balance()
        holdings = bal.get('output1', [])
    except Exception as e:
        st.warning(f'잔고 조회 실패: {e}')
        holdings = []

    if holdings:
        df = pd.DataFrame(holdings)
        df['profit'] = df['evlu_pfls_rt'].astype(float)
        df['amt']    = df['evlu_amt'].astype(float)
        df['cost']   = df['pchs_avg_pric'].astype(float) * df['ccld_qty_1'].astype(float)

        total_val    = df['amt'].sum()
        total_cost   = df['cost'].sum()
        total_pnl    = total_val - total_cost
        avg_profit   = df['profit'].mean()
        best_idx     = df['profit'].idxmax()
        worst_profit = df['profit'].min()

        # ── KPI 카드 6개 ──────────────────────────────────────
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.markdown(kpi_card('총 평가 자산',   f'${total_val:,.0f}'),                    unsafe_allow_html=True)
        c2.markdown(kpi_card('오늘 P&L',       f'${total_pnl:+,.0f}', delta=avg_profit), unsafe_allow_html=True)
        c3.markdown(kpi_card('평균 수익률',    f'{avg_profit:+.2f}%',  delta=avg_profit), unsafe_allow_html=True)
        c4.markdown(kpi_card('최고 종목',      df.loc[best_idx, 'prdt_name'],             delta=df.loc[best_idx, 'profit']), unsafe_allow_html=True)
        c5.markdown(kpi_card('최대 낙폭',      f'{worst_profit:.2f}%', delta=worst_profit), unsafe_allow_html=True)
        c6.markdown(kpi_card('포지션',         f'{len(df)} / 7'),                         unsafe_allow_html=True)

        st.divider()

        # ── 차트 행 ───────────────────────────────────────────
        col1, col2 = st.columns([1, 1.35])

        with col1:
            # 반도넛 — 중앙에 총 AUM 표시
            fig_donut = go.Figure(go.Pie(
                labels=df['prdt_name'],
                values=df['amt'],
                hole=0.64,
                textinfo='label+percent',
                textfont=dict(size=10, color='#E8E8F0'),
                marker=dict(
                    colors=_COLORS[:len(df)],
                    line=dict(color='#0D0D0F', width=2),
                ),
                hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>',
            ))
            fig_donut.add_annotation(
                text=f'<b>${total_val:,.0f}</b>',
                x=0.5, y=0.56,
                font=dict(size=17, color='#FFFFFF', family='JetBrains Mono'),
                showarrow=False,
            )
            fig_donut.add_annotation(
                text='TOTAL AUM',
                x=0.5, y=0.43,
                font=dict(size=9, color='#6B6B8A', family='Inter'),
                showarrow=False,
            )
            apply_theme(fig_donut, 'ASSET ALLOCATION')
            fig_donut.update_layout(showlegend=False, height=310)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            # 수익률 바 + 익절/손절 기준선
            bar_colors = ['#00D4AA' if p >= 0 else '#FF4560' for p in df['profit']]
            fig_bar = go.Figure(go.Bar(
                x=df['prdt_name'],
                y=df['profit'],
                marker=dict(
                    color=bar_colors,
                    line=dict(width=0),
                    opacity=0.85,
                ),
                hovertemplate='<b>%{x}</b><br>수익률: %{y:.2f}%<extra></extra>',
            ))
            fig_bar.add_hline(
                y=0.7,
                line=dict(color='#00D4AA', width=1, dash='dot'),
                annotation_text='익절 +0.7%',
                annotation_font=dict(color='#00D4AA', size=10),
                annotation_position='top right',
            )
            fig_bar.add_hline(
                y=-1.5,
                line=dict(color='#FF4560', width=1, dash='dot'),
                annotation_text='손절 −1.5%',
                annotation_font=dict(color='#FF4560', size=10),
                annotation_position='bottom right',
            )
            fig_bar.add_hline(y=0, line=dict(color='#2A2A3A', width=1))
            apply_theme(fig_bar, 'REAL-TIME P&L BY POSITION')
            fig_bar.update_layout(height=310, yaxis=dict(ticksuffix='%'))
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── 포지션 상세 테이블 ────────────────────────────────
        st.markdown('<div class="block-label">POSITION DETAIL</div>', unsafe_allow_html=True)
        rows_html = ''
        for _, row in df.iterrows():
            p       = row['profit']
            p_color = '#00D4AA' if p >= 0 else '#FF4560'
            p_icon  = '▲' if p >= 0 else '▼'
            rows_html += (
                f'<tr>'
                f'  <td style="font-weight:600;color:#FFFFFF!important;">{row["prdt_name"]}</td>'
                f'  <td class="mono">{int(float(row["ccld_qty_1"]))} 주</td>'
                f'  <td class="mono">${float(row["pchs_avg_pric"]):.2f}</td>'
                f'  <td class="mono">${float(row["now_pric"]):.2f}</td>'
                f'  <td class="mono">${row["amt"]:,.0f}</td>'
                f'  <td class="mono" style="color:{p_color}!important;font-weight:600;">{p_icon} {p:.2f}%</td>'
                f'</tr>'
            )
        st.markdown(
            f'<div class="pos-table-wrap"><table class="sig-table">'
            f'<thead><tr>'
            f'<th>종목명</th><th>수량</th><th>평균단가</th><th>현재가</th><th>평가금액</th><th>수익률</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            '<div class="empty-state">'
            '  <div class="empty-icon">🎯</div>'
            '  <div class="empty-title">포지션 없음</div>'
            '  <div class="empty-sub">봇이 매수 시그널을 스캔 중입니다. 곧 데이터가 나타납니다.</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — AI 전략실
# ══════════════════════════════════════════════════════════════════
elif page == '🤖 AI 전략실':
    st.markdown('<div class="section-header">AI STRATEGY LAB</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">실시간 기술적 지표 분석 · yfinance 라이브 데이터 (60초 캐시)</div>', unsafe_allow_html=True)

    STOCKS = [
        ('NVDA', '엔비디아'), ('TSLA', '테슬라'),  ('AAPL', '애플'),
        ('MSFT', '마이크로소프트'), ('AMD', 'AMD'),   ('AMZN', '아마존'),
        ('META', '메타'),    ('GOOGL', '구글'),   ('TQQQ', '나스닥3배'),
        ('SOXL', '반도체3배'),
    ]

    # ── 에이전트 상태 카드 ─────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            '<div class="agent-card alpha">'
            '  <span class="agent-tag tag-blue">ALPHA ENGINE</span>'
            '  <div class="agent-title">📈 추세 분석가 · 지호-알파</div>'
            '  <div class="agent-body">'
            '    <b>현재 전략:</b> 공격적 스캘핑<br><br>'
            '    RSI &lt; 40 과매도 구간 우선 진입. 예측 수익률 0.3% 이상 + RSI &lt; 70 동시 충족 시 매수 집행.'
            '    나스닥 3배 레버리지 ETF 모멘텀 집중 감시 중.'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            '<div class="agent-card guardian">'
            '  <span class="agent-tag tag-green">GUARDIAN ENGINE</span>'
            '  <div class="agent-title">🛡️ 리스크 관리자 · 지호-가디언</div>'
            '  <div class="agent-body">'
            '    <b>현재 전략:</b> 자산 방어 우선<br><br>'
            '    최대 포지션 7개 상한 유지. −1.5% 도달 즉시 기계적 손절.'
            '    VIX 급등 감지 시 신규 진입 일시 중단 프로토콜 대기 중.'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── 실시간 시장 데이터 수집 ────────────────────────────────
    @st.cache_data(ttl=60)
    def fetch_market_data(tickers: tuple) -> list[dict]:
        results = []
        for ticker, name in tickers:
            try:
                raw = yf.download(ticker, period='30d', progress=False, auto_adjust=True)
                if raw.empty or len(raw) < 15:
                    continue

                close = raw['Close'].squeeze()
                delta = close.diff()
                gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
                loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
                rs    = gain / loss.replace(0, np.nan)
                rsi   = float((100 - 100 / (1 + rs)).iloc[-1])
                price = float(close.iloc[-1])
                chg   = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
                vol   = float(close.pct_change().rolling(10).std().iloc[-1] * 100)

                if rsi < 30:
                    signal = 'BUY'
                elif rsi > 70:
                    signal = 'SELL'
                else:
                    signal = 'HOLD'

                results.append(dict(
                    ticker=ticker, name=name,
                    price=price, chg=chg,
                    rsi=rsi, vol=vol, signal=signal,
                ))
            except Exception:
                pass
        return results

    with st.spinner('시장 데이터 로딩 중 …'):
        market_data = fetch_market_data(tuple(STOCKS))

    if not market_data:
        st.warning('시장 데이터를 불러오지 못했습니다. 네트워크를 확인하세요.')
        st.stop()

    # ── RSI 게이지 차트 (2행 × 5열) ───────────────────────────
    st.markdown('<div class="block-label">RSI LIVE SCANNER</div>', unsafe_allow_html=True)
    gauge_cols = st.columns(5)

    for i, d in enumerate(market_data[:10]):
        rsi = d['rsi']
        if rsi < 40:
            bar_color, zone_label = '#FF4560', '과매도'
        elif rsi > 70:
            bar_color, zone_label = '#00D4AA', '과매수'
        else:
            bar_color, zone_label = '#008FFB', '중립'

        fig_g = go.Figure(go.Indicator(
            mode='gauge+number',
            value=rsi,
            number=dict(
                font=dict(color='#FFFFFF', size=20, family='JetBrains Mono'),
                valueformat='.1f',
            ),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickvals=[0, 30, 50, 70, 100],
                    ticktext=['0', '30', '50', '70', '100'],
                    tickfont=dict(color='#4A4A6A', size=8),
                    tickwidth=0,
                    tickcolor='transparent',
                ),
                bar=dict(color=bar_color, thickness=0.55),
                bgcolor='#0D0D0F',
                borderwidth=0,
                steps=[
                    dict(range=[0,  30], color='rgba(255,69,96,0.07)'),
                    dict(range=[30, 70], color='rgba(0,143,251,0.04)'),
                    dict(range=[70,100], color='rgba(0,212,170,0.07)'),
                ],
                threshold=dict(
                    line=dict(color='#FEB019', width=2),
                    thickness=0.75,
                    value=50,
                ),
            ),
            title=dict(
                text=f"<b>{d['ticker']}</b><br>"
                     f"<span style='font-size:9px;color:#6B6B8A'>{zone_label}</span>",
                font=dict(color='#E8E8F0', size=11, family='Inter'),
            ),
        ))
        fig_g.update_layout(
            paper_bgcolor='#141418',
            height=165,
            margin=dict(l=6, r=6, t=52, b=6),
            font=dict(family='Inter'),
        )
        gauge_cols[i % 5].plotly_chart(fig_g, use_container_width=True)

    st.divider()

    # ── 멀티팩터 시그널 히트맵 ────────────────────────────────
    st.markdown('<div class="block-label">MULTI-FACTOR SIGNAL HEATMAP</div>', unsafe_allow_html=True)

    tickers_list = [d['ticker'] for d in market_data]
    rsi_row = [d['rsi'] for d in market_data]
    chg_row = [d['chg'] for d in market_data]
    vol_row = [d['vol'] for d in market_data]

    # RSI는 50 기준 중립화하여 히트맵 색상이 의미 있게 표시
    rsi_centered = [v - 50 for v in rsi_row]

    fig_heat = go.Figure(go.Heatmap(
        z=[rsi_centered, chg_row, vol_row],
        x=tickers_list,
        y=['RSI (vs 50)', '일간 변동%', '변동성%'],
        colorscale=[
            [0.0, '#FF4560'],
            [0.5, '#1A1A2A'],
            [1.0, '#00D4AA'],
        ],
        zmid=0,
        text=[
            [f'{v:.1f}' for v in rsi_row],
            [f'{v:+.2f}' for v in chg_row],
            [f'{v:.2f}' for v in vol_row],
        ],
        texttemplate='%{text}',
        textfont=dict(size=10, color='#FFFFFF', family='JetBrains Mono'),
        hovertemplate='<b>%{x}</b> · %{y}<br>값: %{z:.2f}<extra></extra>',
        showscale=True,
        colorbar=dict(
            tickfont=dict(color='#6B6B8A', size=9),
            bgcolor='#141418',
            bordercolor='#1E1E2E',
            borderwidth=1,
            thickness=12,
        ),
    ))
    apply_theme(fig_heat)
    fig_heat.update_layout(
        height=220,
        yaxis=dict(tickfont=dict(color='#A0A0C0', size=11), gridcolor='transparent'),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # ── 실시간 시그널 테이블 ──────────────────────────────────
    st.markdown('<div class="block-label">LIVE SIGNAL TABLE</div>', unsafe_allow_html=True)
    rows_sig = ''
    for d in market_data:
        chg_color = '#00D4AA' if d['chg'] >= 0 else '#FF4560'
        chg_icon  = '▲' if d['chg'] >= 0 else '▼'
        sig_map   = {'BUY': 'badge-buy', 'SELL': 'badge-sell', 'HOLD': 'badge-hold'}
        rows_sig += (
            f'<tr>'
            f'  <td style="font-weight:700;color:#FFFFFF!important;">{d["ticker"]}</td>'
            f'  <td style="color:#8080A0!important;">{d["name"]}</td>'
            f'  <td class="mono">${d["price"]:.2f}</td>'
            f'  <td class="mono" style="color:{chg_color}!important;">{chg_icon} {d["chg"]:+.2f}%</td>'
            f'  <td class="mono">{d["rsi"]:.1f}</td>'
            f'  <td class="mono">{d["vol"]:.2f}%</td>'
            f'  <td><span class="badge {sig_map[d["signal"]]}">{d["signal"]}</span></td>'
            f'</tr>'
        )
    st.markdown(
        f'<div class="pos-table-wrap"><table class="sig-table">'
        f'<thead><tr>'
        f'<th>TICKER</th><th>종목</th><th>현재가</th><th>일간 변동</th><th>RSI</th><th>변동성</th><th>시그널</th>'
        f'</tr></thead>'
        f'<tbody>{rows_sig}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — 매매 장부
# ══════════════════════════════════════════════════════════════════
elif page == '📜 매매 장부':
    st.markdown('<div class="section-header">TRADE JOURNAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">전체 매매 이력 · 누적 손익 분석</div>', unsafe_allow_html=True)

    LOG_FILE = 'quant_trade_log.csv'

    if os.path.exists(LOG_FILE):
        try:
            df_log = pd.read_csv(LOG_FILE, on_bad_lines='skip')
        except Exception as e:
            st.error(f'로그 파일 읽기 실패: {e}')
            st.stop()

        total_trades = len(df_log)
        # 4번째 컬럼(index 3)이 매수/매도 구분 컬럼이라고 가정
        if total_trades > 0 and df_log.shape[1] > 3:
            action_col   = df_log.columns[3]
            buy_trades   = int((df_log[action_col] == 'BUY').sum())
            sell_trades  = int((df_log[action_col] == 'SELL').sum())
        else:
            buy_trades = sell_trades = 0

        # ── KPI 카드 3개 ──────────────────────────────────────
        kc1, kc2, kc3 = st.columns(3)
        kc1.markdown(kpi_card('총 거래 횟수', f'{total_trades} 회'), unsafe_allow_html=True)
        kc2.markdown(kpi_card('매수 집행',    f'{buy_trades} 회'),   unsafe_allow_html=True)
        kc3.markdown(kpi_card('매도 집행',    f'{sell_trades} 회'),  unsafe_allow_html=True)

        st.divider()

        # ── 매매 장부 테이블 (최신순) ─────────────────────────
        st.markdown('<div class="block-label">TRADE HISTORY (최신순)</div>', unsafe_allow_html=True)
        st.dataframe(
            df_log.iloc[::-1].reset_index(drop=True),
            use_container_width=True,
            height=420,
        )
    else:
        st.markdown(
            '<div class="empty-state">'
            '  <div class="empty-icon">📋</div>'
            '  <div class="empty-title">기록 없음</div>'
            '  <div class="empty-sub">첫 번째 거래가 실행되면 여기에 장부가 생성됩니다.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
