"""
╔══════════════════════════════════════════════════════════════╗
║           ALETHEIA — World-Class Alpha Intelligence        ║
║   Premium Dashboard • Real Data • Live Trading • AI-Powered║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dashboard.components.charts import (
    candlestick_chart, correlation_heatmap, waterfall_chart,
    risk_gauge, network_graph, event_timeline
)
from dashboard.components.performance import (
    optimized_query, get_db_connection, paginate_dataframe, show_performance_stats
)
from dashboard.components.mobile import inject_responsive_css, generate_pwa_manifest

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG — Premium Setup
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ALETHEIA | Alpha Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════
# WORLD-CLASS DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── FONTS ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }

/* ── THEME: OBSIDIAN LUXURY ── */
:root {
    --bg-deep: #06080d;
    --bg-primary: #0a0f1a;
    --bg-card: rgba(15, 23, 42, 0.7);
    --border-subtle: rgba(0, 180, 255, 0.06);
    --border-glow: rgba(0, 180, 255, 0.2);
    --text-primary: #e8edf5;
    --text-secondary: #6b7d99;
    --text-muted: #3d4f66;
    --accent-blue: #00a8ff;
    --accent-green: #00e676;
    --accent-red: #ff3d5c;
    --accent-gold: #ffb74d;
    --accent-purple: #7c4dff;
    --glass-blur: blur(24px);
}

.stApp {
    background: linear-gradient(160deg, #06080d 0%, #0a0f1a 30%, #0d1525 60%, #0a0f1a 100%);
    background-attachment: fixed;
}

/* ── AMBIENT GLOW ── */
.stApp::before {
    content: '';
    position: fixed;
    top: -200px;
    right: -200px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(0,168,255,0.03) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ── GLASS CARDS ── */
.glass {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,168,255,0.3), transparent);
}
.glass:hover {
    border-color: var(--border-glow);
    box-shadow: 0 8px 40px rgba(0,0,0,0.4), 0 0 80px rgba(0,168,255,0.04);
    transform: translateY(-2px);
}

/* ── KPI NUMBERS WITH ANIMATION ── */
.kpi-number {
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1;
    background: linear-gradient(180deg, #ffffff 0%, #a0c8f0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s ease-in-out infinite;
}
@keyframes shimmer {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.85; }
}
.kpi-number.positive { background: linear-gradient(180deg, #00e676 0%, #00c853 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.kpi-number.negative { background: linear-gradient(180deg, #ff3d5c 0%, #d50000 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.kpi-tag {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: var(--text-secondary);
}
.kpi-sub {
    font-size: 10px;
    color: var(--text-muted);
    margin-top: 4px;
}

/* ── SECTION HEADERS ── */
.sec-title {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 4px;
    color: var(--text-secondary);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sec-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,168,255,0.15), transparent);
}

/* ── PULSE DOT ── */
.pulse {
    width: 8px; height: 8px;
    background: var(--accent-green);
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 12px var(--accent-green);
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(1.8); }
}

/* ── LIVE GLOW ON P&L ── */
.pnl-positive {
    animation: glow-green 2s ease-in-out infinite;
}
.pnl-negative {
    animation: glow-red 2s ease-in-out infinite;
}
@keyframes glow-green {
    0%, 100% { text-shadow: 0 0 8px rgba(0,230,118,0.3); }
    50% { text-shadow: 0 0 20px rgba(0,230,118,0.6); }
}
@keyframes glow-red {
    0%, 100% { text-shadow: 0 0 8px rgba(255,61,92,0.3); }
    50% { text-shadow: 0 0 20px rgba(255,61,92,0.6); }
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(10,15,26,0.6);
    border-radius: 14px;
    padding: 4px;
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 10px;
    font-weight: 600;
    color: var(--text-secondary);
    white-space: nowrap;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,168,255,0.12);
    color: var(--accent-blue);
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: #1a2540; border-radius: 4px; }

/* ── TICKER TAPE ── */
.ticker-wrap {
    overflow: hidden; white-space: nowrap;
    padding: 6px 0;
    border-top: 1px solid var(--border-subtle);
    border-bottom: 1px solid var(--border-subtle);
    background: rgba(0,0,0,0.3);
}
.ticker { display: inline-block; animation: ticker 25s linear infinite; }
@keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
.ticker-item { display: inline-block; margin: 0 20px; font-size: 10px; font-weight: 500; }

/* ── POSITION CARDS ── */
.position-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 14px 18px;
    margin: 4px 0;
    transition: all 0.2s;
    border-left: 3px solid transparent;
}
.position-card:hover { border-color: var(--border-glow); }
.position-card.profit { border-left-color: var(--accent-green); }
.position-card.loss { border-left-color: var(--accent-red); }

/* ── AI CARD ── */
.ai-card {
    background: linear-gradient(135deg, rgba(124,77,255,0.08), rgba(0,168,255,0.04));
    border: 1px solid rgba(124,77,255,0.15);
    border-radius: 16px;
    padding: 18px;
    margin: 6px 0;
}

/* ── KEYBOARD SHORTCUT HINT ── */
.kbd {
    display: inline-block;
    padding: 2px 8px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    font-size: 9px;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 2px;
}

/* ── HIDE STREAMLIT BRANDING ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

inject_responsive_css()
generate_pwa_manifest()

# ═══════════════════════════════════════════════════════════
# DATA LOADERS — Real-time with caching
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=20)
def load_db():
    empty_sig = pd.DataFrame(columns=['ticker', 'composite_score', 'signal_direction'])
    empty_ens = pd.DataFrame(columns=['ticker', 'e'])
    empty_health = pd.DataFrame(columns=['t', 'r'])
    try:
        sig = optimized_query(
            "SELECT ticker, composite_score, signal_direction FROM composite_signals ORDER BY composite_score DESC",
            cache_key="composite_signals", ttl=20
        )
        ens = optimized_query(
            "SELECT ticker, AVG(tcs_score) as e FROM ens_scores WHERE id LIKE 'finbert_%' GROUP BY ticker ORDER BY e DESC",
            cache_key="ens_scores", ttl=40
        )
        conn = get_db_connection()
        tbls = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        h = [{'t': t[0], 'r': conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]} for t in tbls]
        return (sig if not sig.empty else empty_sig, 
                ens if not ens.empty else empty_ens, 
                pd.DataFrame(h) if h else empty_health)
    except: return empty_sig, empty_ens, empty_health

def load_alpaca():
    try:
        path = Path(__file__).parent.parent / 'alpaca_data.json'
        if not path.exists(): return None
        with open(path) as f: d = json.load(f)
        return d if 'error' not in d else None
    except: return None

def load_history():
    try:
        path = Path(__file__).parent.parent / 'alpaca_history.json'
        if not path.exists(): return None
        with open(path) as f: d = json.load(f)
        return d if d and len(d)>0 else None
    except: return None

sig, ens, health = load_db()
alpaca = load_alpaca()
history = load_history()

# ═══════════════════════════════════════════════════════════
# TICKER TAPE — Live scrolling prices
# ═══════════════════════════════════════════════════════════
try:
    tape_items = []
    for _, r in sig.iterrows():
        s = r['composite_score']
        color = '#00e676' if s > 0.05 else ('#ff3d5c' if s < -0.05 else '#6b7d99')
        tape_items.append(f"<span style='color:{color}'>{r['ticker']} {s:+.3f}</span>")
    tape_html = " ◆ ".join(tape_items * 5)
    st.markdown(f"""<div class='ticker-wrap'><div class='ticker'><span class='ticker-item'>{tape_html}</span></div></div>""", unsafe_allow_html=True)
except: pass

# ═══════════════════════════════════════════════════════════
# HEADER — Premium
# ═══════════════════════════════════════════════════════════
c1, c2, c3 = st.columns([1, 6, 2])
with c1: 
    st.markdown("<h1 style='font-size:34px;margin:0;filter:drop-shadow(0 0 20px rgba(0,168,255,0.3));'>◆</h1>", unsafe_allow_html=True)
with c2: 
    st.markdown("""<div style='padding-top:8px;'>
        <span style='font-size:22px;font-weight:800;letter-spacing:-1px;color:#e8edf5;'>ALETHEIA</span>
        <span style='font-size:11px;font-weight:500;color:#6b7d99;margin-left:12px;letter-spacing:2px;'>ALPHA INTELLIGENCE</span>
    </div>""", unsafe_allow_html=True)
with c3:
    live_text = "● LIVE" if alpaca else "○ CACHED"
    live_color = "#00e676" if alpaca else "#6b7d99"
    now_utc = datetime.utcnow()
    ny_time = now_utc - timedelta(hours=4)
    is_market_open = 9 <= ny_time.hour < 16 and ny_time.weekday() < 5
    market_status = "🟢 MARKET OPEN" if is_market_open else "🔴 MARKET CLOSED"
    st.markdown(f"""<div style='text-align:right;padding-top:8px;'>
        <span class='pulse'></span>
        <span style='color:{live_color};font-size:10px;margin-left:4px;'>{live_text}</span><br>
        <span style='color:#3d4f66;font-size:8px;'>{market_status}</span><br>
        <span style='color:#3d4f66;font-size:8px;'>{datetime.utcnow().strftime('%H:%M')} UTC</span>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# KPI ROW — Animated premium cards
# ═══════════════════════════════════════════════════════════
if alpaca:
    equity = alpaca.get('equity', 100000)
    pnl = alpaca.get('pnl_today', 0)
    cash = alpaca.get('cash', 100000)
    pos_count = len(alpaca.get('positions', []))
else:
    equity, pnl, cash, pos_count = 100000, 0, 100000, 0

L = len(sig[sig['signal_direction']==1]) if not sig.empty else 0
S = len(sig[sig['signal_direction']==-1]) if not sig.empty else 0
avg = sig['composite_score'].mean() if not sig.empty else 0
tot = health['r'].sum() if not health.empty else 0

pnl_sign = '+' if pnl >= 0 else ''
pnl_class = 'positive' if pnl >= 0 else 'negative'
pnl_glow = 'pnl-positive' if pnl >= 0 else 'pnl-negative'

cols = st.columns(5)
kpi_data = [
    ("PORTFOLIO", f"${equity:,.0f}", f"{pnl_sign}${pnl:,.2f} TODAY", '#00e676' if pnl>=0 else '#ff3d5c', pnl_class),
    ("CASH", f"${cash:,.0f}", f"{pos_count} POSITIONS", '#6b7d99', ''),
    ("SIGNALS", f"{len(sig)}", f"{L}L / {S}S", '#6b7d99', ''),
    ("AVG SCORE", f"{avg:+.3f}", "BULLISH" if avg>0.02 else "NEUTRAL", '#00e676' if avg>0 else '#ff3d5c', ''),
    ("DATABASE", f"{tot:,}", "LIVE", '#6b7d99', ''),
]
for i, (label, value, sub, color, extra_class) in enumerate(kpi_data):
    with cols[i]:
        value_class = f'kpi-number {extra_class}' if extra_class else 'kpi-number'
        st.markdown(f"""<div class='glass' style='text-align:center;'>
            <div class='kpi-tag'>{label}</div>
            <div class='{value_class}' style='color:{color};'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)
        
# ═══════════════════════════════════════════════════════════
# ALL 9 TABS — World-Class Design
# ═══════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 SIGNALS", "📈 MARKETS", "⚠️ RISK", "🔗 NETWORK", "📅 EVENTS", 
    "📋 DATA", "🛡️ SYSTEM", "🔐 SECURITY", "🤖 AI"
])

# ═══════════════ TAB 1: SIGNALS ═══════════════
with tab1:
    col_left, col_right = st.columns([1.8, 1.2])
    
    with col_left:
        st.markdown("<div class='sec-title'>◆ SIGNAL PANORAMA</div>", unsafe_allow_html=True)
        if not sig.empty:
            colors = ['#00e676' if x > 0.02 else '#ff3d5c' if x < -0.02 else '#6b7d99' for x in sig['composite_score']]
            fig = go.Figure()
            for i, (t, s) in enumerate(zip(sig['ticker'], sig['composite_score'])):
                fig.add_trace(go.Bar(
                    x=[t], y=[s],
                    marker=dict(color=colors[i], cornerradius=8, line=dict(width=0)),
                    text=[f"<b>{s:+.3f}</b>"],
                    textposition='outside',
                    textfont=dict(color=colors[i], size=12, family='Inter'),
                    hovertemplate=f"<b>{t}</b><br>Signal: {s:+.4f}<extra></extra>"
                ))
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                height=420, margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                xaxis=dict(showgrid=False, tickfont=dict(color='#6b7d99', size=12, family='Inter')),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,168,255,0.04)', zeroline=True,
                          zerolinecolor='rgba(0,168,255,0.15)', tickfont=dict(color='#6b7d99')),
                transition=dict(duration=500, easing='cubic-in-out')
            )
            fig.add_hline(y=0.05, line_dash="dash", line_color="rgba(0,230,118,0.2)", line_width=1,
                         annotation_text="LONG", annotation_position="top right",
                         annotation_font=dict(color='#00e676', size=9))
            fig.add_hline(y=-0.05, line_dash="dash", line_color="rgba(255,61,92,0.2)", line_width=1,
                         annotation_text="SHORT", annotation_position="bottom right",
                         annotation_font=dict(color='#ff3d5c', size=9))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key="signal_bars")
    
    with col_right:
        st.markdown("<div class='sec-title'>◆ LIVE POSITIONS</div>", unsafe_allow_html=True)
        if alpaca and alpaca.get('positions'):
            for p in alpaca['positions']:
                pl = p.get('unrealized_pl', 0)
                pct = p.get('unrealized_pl_pct', 0)
                is_profit = pl >= 0
                card_class = 'profit' if is_profit else 'loss'
                emoji = '🟢' if is_profit else '🔴'
                sign = '+' if is_profit else ''
                glow = 'pnl-positive' if is_profit else 'pnl-negative'
                st.markdown(f"""<div class='position-card {card_class}'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <span style='font-weight:700;font-size:15px;color:#e8edf5;'>{p.get('symbol','?')}</span>
                        <span style='color:#6b7d99;font-size:11px;'>{p.get('qty',0)} sh</span>
                        <span class='{glow}' style='font-weight:700;font-size:14px;color:{'#00e676' if is_profit else '#ff3d5c'};'>
                            {sign}${abs(pl):,.2f}
                        </span>
                        <span style='font-size:10px;color:{'#00e676' if is_profit else '#ff3d5c'};'>({sign}{pct}%)</span>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Run: python live/alpaca_fetcher.py")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='sec-title'>◆ FinBERT SCORES</div>", unsafe_allow_html=True)
        if not ens.empty:
            ec = ['#00e676' if x > 0 else '#ff3d5c' for x in ens['e']]
            fe = go.Figure(go.Bar(
                x=ens['ticker'], y=ens['e'], marker_color=ec,
                text=ens['e'].round(3), textposition='outside',
                textfont=dict(color=ec, size=11), marker=dict(cornerradius=6)
            ))
            fe.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                height=300, margin=dict(l=0,r=0,t=0,b=0), showlegend=False,
                xaxis=dict(showgrid=False, tickfont=dict(color='#6b7d99')),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,168,255,0.04)'),
                transition=dict(duration=400)
            )
            st.plotly_chart(fe, use_container_width=True, config={'displayModeBar': False}, key="finbert_bars")
    with c2:
        st.markdown("<div class='sec-title'>◆ P&L ATTRIBUTION</div>", unsafe_allow_html=True)
        st.plotly_chart(waterfall_chart(), use_container_width=True, config={'displayModeBar': False}, key="waterfall")

# ═══════════════ TAB 2: MARKETS ═══════════════
with tab2:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("<div class='sec-title'>◆ CANDLESTICK CHART</div>", unsafe_allow_html=True)
        tickers_list = sorted(sig['ticker'].tolist()) if not sig.empty else ['AAPL','MSFT','GOOGL']
        ticker_choice = st.selectbox('Select Ticker', tickers_list, key='candle_select')
        st.plotly_chart(candlestick_chart(ticker_choice), use_container_width=True, config={'displayModeBar': False}, key="candle_chart")
    with c2:
        st.markdown("<div class='sec-title'>◆ CORRELATION MATRIX</div>", unsafe_allow_html=True)
        st.plotly_chart(correlation_heatmap(), use_container_width=True, config={'displayModeBar': False}, key="heatmap")
    
    if history:
        st.markdown("<div class='sec-title'>◆ EQUITY CURVE</div>", unsafe_allow_html=True)
        hdf = pd.DataFrame(history)
        hdf = hdf[hdf['equity'] > 0]
        if len(hdf) > 1:
            feq = go.Figure()
            feq.add_trace(go.Scatter(
                x=hdf['date'], y=hdf['equity'], mode='lines', fill='tozeroy',
                line=dict(color='#00a8ff', width=2.5), fillcolor='rgba(0,168,255,0.05)',
                name='Portfolio'
            ))
            feq.add_hline(y=100000, line_dash="dash", line_color="rgba(255,255,255,0.15)",
                         annotation_text="Initial Capital", annotation_position="bottom right",
                         annotation_font=dict(color='#6b7d99', size=9))
            feq.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                height=280, margin=dict(l=0,r=0,t=10,b=0), showlegend=False,
                xaxis=dict(showgrid=False, tickfont=dict(color='#6b7d99', size=10)),
                yaxis=dict(showgrid=True, gridcolor='rgba(0,168,255,0.04)', tickfont=dict(color='#6b7d99')),
                transition=dict(duration=400)
            )
            st.plotly_chart(feq, use_container_width=True, config={'displayModeBar': False}, key="equity_curve")

# ═══════════════ TAB 3: RISK ═══════════════
with tab3:
    st.markdown("<div class='sec-title'>◆ RISK GAUGES</div>", unsafe_allow_html=True)
    try:
        import numpy as np
        if alpaca and alpaca.get('positions'):
            tv = alpaca.get('equity', 100000)
            c = alpaca.get('cash', 0)
            alloc = ((tv - c) / tv * 100) if tv > 0 else 0
            dd = 0; sh = 0; so = 0
            if history and len(history) > 1:
                eq = [h['equity'] for h in history if h['equity'] > 0]
                if len(eq) > 1:
                    peak = max(eq); cur = eq[-1]
                    dd = ((peak - cur) / peak * 100) if peak > 0 else 0
                if len(eq) > 5:
                    rets = np.diff(eq) / eq[:-1]
                    sh = np.sqrt(252) * np.mean(rets) / (np.std(rets) + 1e-10)
                    sh = max(-3, min(3, sh))
                    down = rets[rets < 0]
                    so = np.sqrt(252) * np.mean(rets) / (np.std(down) + 1e-10) if len(down) > 0 else 0
                    so = max(-3, min(3, so))
        else:
            alloc = 0; dd = 0; sh = 0; so = 0
        
        g1, g2, g3, g4 = st.columns(4)
        with g1: st.plotly_chart(risk_gauge(round(dd, 1), "Drawdown %", 7), use_container_width=True, config={'displayModeBar': False}, key="g1")
        with g2: st.plotly_chart(risk_gauge(round(abs(sh), 2), "Sharpe", 3), use_container_width=True, config={'displayModeBar': False}, key="g2")
        with g3: st.plotly_chart(risk_gauge(round(abs(so), 2), "Sortino", 3), use_container_width=True, config={'displayModeBar': False}, key="g3")
        with g4: st.plotly_chart(risk_gauge(round(alloc, 1), "Alloc %", 50), use_container_width=True, config={'displayModeBar': False}, key="g4")
        st.caption(f"Live from Alpaca • {len(history)} data points" if history else "Awaiting data...")
    except Exception as e:
        st.warning(f"Risk: {e}")
        
# ═══════════════ TAB 4: NETWORK ═══════════════
with tab4:
    st.markdown("<div class='sec-title'>◆ SIGNAL CORRELATION NETWORK</div>", unsafe_allow_html=True)
    st.plotly_chart(network_graph(), use_container_width=True, config={'displayModeBar': False}, key="network_chart")
    st.caption("Node size = signal strength • Green = bullish • Red = bearish")

# ═══════════════ TAB 5: EVENTS ═══════════════
with tab5:
    st.markdown("<div class='sec-title'>◆ SEC FILING TIMELINE</div>", unsafe_allow_html=True)
    st.plotly_chart(event_timeline(), use_container_width=True, config={'displayModeBar': False}, key="timeline_chart")
    st.caption("Diamond markers = SEC filings • Real EDGAR data")

# ═══════════════ TAB 6: DATA EXPLORER ═══════════════
with tab6:
    st.markdown("<div class='sec-title'>◆ INTERACTIVE DATA EXPLORER</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6b7d99;font-size:10px;margin-bottom:12px;'>Click headers to sort • Type to search • Paginated for speed</p>", unsafe_allow_html=True)
    
    styled_df = sig.copy()
    styled_df['Direction'] = styled_df['signal_direction'].map({1: '🟢 LONG', -1: '🔴 SHORT', 0: '⚪ NEUTRAL'})
    styled_df['Signal'] = styled_df['composite_score'].apply(lambda x: f"{x:+.4f}")
    display_df = styled_df[['ticker', 'Signal', 'Direction']]
    
    paginated = paginate_dataframe(display_df, page_size=12)
    st.dataframe(paginated, use_container_width=True, height=420, hide_index=True)
    
    c1, c2 = st.columns(2)
    with c1: 
        st.download_button("📊 Download CSV", sig.to_csv(index=False), "aletheia_signals.csv", 
                          key="csv_tab6", use_container_width=True)
    with c2:
        report = f"ALETHEIA Alpha Report\n{datetime.now()}\n\n" + "\n".join(
            [f"{r['ticker']}: {r['composite_score']:+.4f}" for _, r in sig.iterrows()]
        )
        st.download_button("📄 Download Report", report, "aletheia_report.txt", 
                          key="report_tab6", use_container_width=True)

# ═══════════════ TAB 7: SYSTEM ═══════════════
with tab7:
    st.markdown("<div class='sec-title'>◆ SYSTEM MONITORING</div>", unsafe_allow_html=True)
    try:
        from live.monitoring import health as mon_health, uptime, errors as err_tracker, metrics as perf_m
        h = mon_health.full_check()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            db_status = h['checks']['database']['status'] == 'healthy'
            st.metric("🗄️ Database", "✅ HEALTHY" if db_status else "❌ DOWN")
        with col2:
            al_status = h['checks']['alpaca']['status'] == 'healthy'
            st.metric("💵 Alpaca", "✅ HEALTHY" if al_status else "⚠️ STALE")
        with col3:
            sig_status = h['checks']['signals']['status'] == 'healthy'
            st.metric("📊 Signals", "✅ HEALTHY" if sig_status else "❌ DOWN")
        
        up_pct = uptime.data.get('uptime_pct', 0)
        st.markdown("<div class='sec-title'>◆ UPTIME</div>", unsafe_allow_html=True)
        st.progress(up_pct / 100, text=f"Uptime: {up_pct}% ({uptime.data.get('up',0)}/{uptime.data.get('total',0)} checks)")
        
        st.markdown("<div class='sec-title'>◆ ERROR LOG</div>", unsafe_allow_html=True)
        recent = err_tracker.errors[-5:] if err_tracker.errors else []
        if recent:
            for e in reversed(recent):
                sc = '#ff3d5c' if e['severity'] == 'ERROR' else '#ffb74d'
                st.markdown(f"""<div class='glass' style='padding:8px 14px;margin:2px 0;font-size:10px;'>
                    <span style='color:{sc};'>[{e['severity']}]</span>
                    <span style='color:#6b7d99;'> {e['timestamp'][:19]}</span>
                    <span style='color:#a0b8d0;'> — {e['error'][:100]}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("✨ No errors logged — system running clean")
        
        ps = perf_m.get_stats()
        st.markdown("<div class='sec-title'>◆ PERFORMANCE</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Query", f"{ps['avg_ms']}ms")
        c2.metric("Max Query", f"{ps['max_ms']}ms")
        c3.metric("Total Queries", ps['count'])
        
    except Exception as e:
        st.warning(f"Monitoring: {e}")

# ═══════════════ TAB 8: SECURITY ═══════════════
with tab8:
    st.markdown("<div class='sec-title'>◆ SECURITY CENTER</div>", unsafe_allow_html=True)
    try:
        from live.security import auth as sec_auth, rbac, sec_audit, session_mgr
        session_mgr.init_session()
        
        if not st.session_state.get('authenticated'):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown("<div class='glass' style='text-align:center;padding:30px;'>", unsafe_allow_html=True)
                st.markdown("### 🔐 Authentication")
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                if st.button("🔓 Login", use_container_width=True):
                    ok, result = sec_auth.login(username, password)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.user_name = username
                        st.session_state.user_role = sec_auth.sessions[result]['role']
                        st.session_state.session_token = result
                        st.session_state.login_time = datetime.utcnow()
                        sec_audit.log('LOGIN', username)
                        st.rerun()
                    else:
                        st.error(result)
                st.markdown("</div>", unsafe_allow_html=True)
                st.caption("Default: admin / aletheia_admin_2024")
        else:
            st.success(f"✅ Authenticated as **{st.session_state.user_name}** ({st.session_state.user_role.upper()})")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Role", st.session_state.user_role.upper())
            with c2: st.metric("Session", st.session_state.session_token[:12] + "...")
            with c3: st.metric("Can Trade", "✅" if rbac.has_permission(st.session_state.user_role, 'execute_trades') else "❌")
            with c4: st.metric("Can Config", "✅" if rbac.has_permission(st.session_state.user_role, 'configure_system') else "❌")
            
            if st.button("🚪 Logout", use_container_width=True):
                sec_auth.logout(st.session_state.session_token)
                st.session_state.authenticated = False
                st.rerun()
            
            st.markdown("<div class='sec-title'>◆ AUDIT TRAIL</div>", unsafe_allow_html=True)
            for entry in sec_audit.logs[-8:]:
                st.markdown(f"""<div class='glass' style='padding:6px 14px;margin:2px 0;font-size:10px;'>
                    <span style='color:#6b7d99;'>{entry['timestamp'][:19]}</span>
                    <span style='color:#a0b8d0;'> — {entry['event']} by {entry['user']}</span>
                </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Security: {e}")

# ═══════════════ TAB 9: AI INTELLIGENCE ═══════════════
with tab9:
    st.markdown("<div class='sec-title'>◆ AI-POWERED INSIGHTS</div>", unsafe_allow_html=True)
    try:
        from live.ai_insights import explainer, forecaster, whatif, nlp, recommender
        ens_dict = {r['ticker']: r['e'] for _, r in ens.iterrows()} if not ens.empty else {}
        
        # Signal Explanations
        st.markdown("### 🤖 Real-Time Signal Explanations")
        for _, r in sig.head(5).iterrows():
            exp = explainer.explain_signal(r['ticker'], ens_dict.get(r['ticker'], 0), r['composite_score'])
            st.markdown(f"""<div class='ai-card'>
                <strong style='color:#e8edf5;'>{r['ticker']}</strong>: 
                <span style='color:{'#00e676' if r['composite_score']>0 else '#ff3d5c'};'>{exp['sentiment'].upper()}</span> — {exp['action']}
                <br><small style='color:#6b7d99;'>{exp['ens_detail']}</small>
            </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 3-Period Forecasts")
            for f in forecaster.forecast(sig, 3)[:5]:
                trend_color = '#00e676' if f['trend'] == 'UP' else ('#ff3d5c' if f['trend'] == 'DOWN' else '#6b7d99')
                st.markdown(f"""<div class='glass' style='padding:10px 16px;margin:3px 0;font-size:11px;'>
                    <b style='color:#e8edf5;'>{f['ticker']}</b>
                    <span style='color:{trend_color};'> {f['trend']}</span> → {f['predictions']}
                </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 🎯 Trading Recommendations")
            for r in recommender.generate(sig)[:5]:
                border_color = '#00e676' if r['action'] == 'BUY' else ('#ff3d5c' if r['action'] == 'SELL' else '#6b7d99')
                st.markdown(f"""<div class='glass' style='padding:10px 16px;margin:3px 0;font-size:11px;border-left:3px solid {border_color};'>
                    <b style='color:#e8edf5;'>{r['action']} {r['ticker']}</b>
                    <span style='color:#6b7d99;'> — {r['reason']}</span>
                    <span style='color:{border_color};float:right;'>({r['confidence']})</span>
                </div>""", unsafe_allow_html=True)
        
        # NLP Query
        st.markdown("### 💬 Natural Language Query")
        nlp_q = st.text_input("Ask anything about your signals...", 
                             placeholder="e.g. show top long signals, what are the bearish tickers, filter AAPL")
        if nlp_q:
            parsed = nlp.parse(nlp_q)
            result = nlp.execute(sig, parsed)
            st.success(f"Parsed: {parsed} → Found {len(result)} results")
            st.dataframe(result, use_container_width=True, hide_index=True)
        
        # What-If Simulator
        st.markdown("### 🔮 What-If Scenario Simulator")
        c1, c2 = st.columns(2)
        with c1:
            ticker_sim = st.selectbox('Select Ticker', sig['ticker'].tolist(), key='whatif_ticker_ai')
            change = st.slider('ENS Score Change', -0.5, 0.5, 0.0, 0.05, key='ens_change_ai')
            if st.button('🔮 Run Simulation', key='whatif_btn_ai', use_container_width=True):
                cur = ens_dict.get(ticker_sim, 0)
                sim = whatif.simulate_ens_change(ticker_sim, cur, change)
                st.metric("Position Impact", f"{sim['position_change']:+.1f}%")
                st.metric("New Composite", f"{sim['composite_change']:+.4f}")
                st.info(sim['action'])
        with c2:
            shock_pct = st.slider('Market Shock %', -20.0, 20.0, -5.0, 1.0, key='shock_ai')
            shock = whatif.simulate_market_shock(equity, shock_pct)
            st.metric("Portfolio Impact", f"${shock['impact']:,.0f}")
            st.metric("New Portfolio Value", f"${shock['new_value']:,.0f}")
            st.metric("Drawdown", f"{shock['drawdown']}%")
            
    except Exception as e:
        st.warning(f"AI: {e}")

# ═══════════════════════════════════════════════════════════
# FOOTER — Premium
# ═══════════════════════════════════════════════════════════
show_performance_stats()
st.markdown("""
    <div style='text-align:center;padding:30px 0 10px 0;color:#1a2540;font-size:8px;letter-spacing:3px;'>
        ◆ ALETHEIA ALPHA INTELLIGENCE ◆ RESEARCH PROTOTYPE ◆ NOT FINANCIAL ADVICE ◆
    </div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# AUTO-REFRESH with Alpaca data update
# ═══════════════════════════════════════════════════════════
import subprocess
subprocess.run(['python', 'live/alpaca_fetcher.py'], capture_output=True)
time.sleep(25)
st.rerun()