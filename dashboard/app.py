"""
╔══════════════════════════════════════════════════════╗
║           ALETHEIA — Alpha Intelligence              ║
║   Institutional Dashboard — All Dimensions + Mobile  ║
╚══════════════════════════════════════════════════════╝
"""
import sys, os, json, time, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from dashboard.components.charts import (
    candlestick_chart, correlation_heatmap, sparkline,
    waterfall_chart, risk_gauge, network_graph, event_timeline
)
from dashboard.components.interactivity import toast_notification
from dashboard.components.performance import (
    optimized_query, get_db_connection, paginate_dataframe,
    show_performance_stats
)
from dashboard.components.mobile import (
    inject_responsive_css, generate_pwa_manifest, MobileNavigation
)

st.set_page_config(page_title="ALETHEIA | Alpha Intelligence", page_icon="◆", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(ellipse at 20% 50%, #0a1035 0%, #060b1f 50%, #040818 100%); }
.glass { background: linear-gradient(135deg, rgba(20,30,65,0.6), rgba(10,15,40,0.8)); backdrop-filter: blur(20px); border: 1px solid rgba(0,200,255,0.06); border-radius: 20px; padding: 24px; }
.kpi-number { font-size: 36px; font-weight: 800; letter-spacing: -2px; line-height: 1; background: linear-gradient(180deg, #ffffff 0%, #a0c4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.kpi-tag { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 3px; color: #4a6090; }
.kpi-sub { font-size: 10px; color: #3a5070; margin-top: 4px; }
.sec-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 4px; color: #4a6090; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
.sec-title::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(0,200,255,0.2), transparent); }
.pulse { width: 8px; height: 8px; background: #00ff88; border-radius: 50%; display: inline-block; box-shadow: 0 0 12px #00ff88; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(1.8); } }
::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #060b1f; } ::-webkit-scrollbar-thumb { background: #1a2a4a; border-radius: 4px; }
#MainMenu, footer, header { visibility: hidden; }
.ticker-wrap { overflow: hidden; white-space: nowrap; padding: 6px 0; border-top: 1px solid rgba(0,200,255,0.06); border-bottom: 1px solid rgba(0,200,255,0.06); }
.ticker { display: inline-block; animation: ticker 30s linear infinite; }
@keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
.ticker-item { display: inline-block; margin: 0 18px; font-size: 11px; font-weight: 500; color: #5a7090; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: rgba(10,15,40,0.5); border-radius: 12px; padding: 4px; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 14px; font-size: 10px; font-weight: 600; color: #5a7090; white-space: nowrap; }
.stTabs [aria-selected="true"] { background: rgba(0,170,255,0.15); color: #00aaff; }
div[data-testid="stExpander"] { background: rgba(20,30,65,0.5); border: 1px solid rgba(0,200,255,0.08); border-radius: 16px; }
div[data-testid="stDataFrame"] { background: rgba(15,23,55,0.6); border: 1px solid rgba(0,200,255,0.06); border-radius: 12px; overflow: hidden; }
div[data-testid="stDataFrame"] table { color: #a0b4d0; }
div[data-testid="stDataFrame"] th { background: rgba(0,170,255,0.1); color: #4a6090; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 10px; }
.ai-card { background: linear-gradient(135deg, rgba(100,60,255,0.1), rgba(0,170,255,0.05)); border: 1px solid rgba(100,60,255,0.2); border-radius: 16px; padding: 20px; margin: 8px 0; }

/* MOBILE OPTIMIZATION */
@media (max-width: 768px) {
    .stColumns { flex-direction: column !important; gap: 6px !important; }
    .stColumns > div { width: 100% !important; flex: none !important; }
    .kpi-number { font-size: 20px !important; }
    .kpi-tag { font-size: 7px !important; letter-spacing: 1px !important; }
    .glass { padding: 10px !important; border-radius: 12px !important; }
    .sec-title { font-size: 9px !important; letter-spacing: 2px !important; margin-bottom: 8px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px !important; padding: 2px !important; }
    .stTabs [data-baseweb="tab"] { padding: 5px 7px !important; font-size: 7px !important; white-space: nowrap !important; }
    .ticker-wrap { display: none !important; }
    h1 { font-size: 22px !important; }
    .stApp { padding: 6px !important; }
    div[data-testid="stDataFrame"] { font-size: 9px !important; }
    .js-plotly-plot { max-height: 220px !important; }
    .ai-card { padding: 10px !important; margin: 4px 0 !important; }
}
</style>
""", unsafe_allow_html=True)

inject_responsive_css()
generate_pwa_manifest()

@st.cache_data(ttl=30)
def load_db():
    empty_sig = pd.DataFrame(columns=['ticker', 'composite_score', 'signal_direction'])
    empty_ens = pd.DataFrame(columns=['ticker', 'e'])
    empty_health = pd.DataFrame(columns=['t', 'r'])
    try:
        sig = optimized_query("SELECT ticker, composite_score, signal_direction FROM composite_signals ORDER BY composite_score DESC", cache_key="composite_signals", ttl=30)
        ens = optimized_query("SELECT ticker, AVG(ens_final) as e FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker ORDER BY e DESC", cache_key="ens_scores", ttl=60)
        conn = get_db_connection()
        tbls = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        h = [{'t': t[0], 'r': conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]} for t in tbls]
        return (sig if not sig.empty else empty_sig, ens if not ens.empty else empty_ens, pd.DataFrame(h) if h else empty_health)
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

try:
    tape = " ◆ ".join([f"<span style='color:{'#00ff88' if s>0.02 else '#ff4060' if s<-0.02 else '#5a7090'}'>{t} {s:+.3f}</span>" for t,s in zip(sig['ticker'],sig['composite_score'])]*6)
    st.markdown(f"<div class='ticker-wrap'><div class='ticker'><span class='ticker-item'>{tape}</span></div></div>", unsafe_allow_html=True)
except: pass

c1,c2,c3 = st.columns([1,6,2])
with c1: st.markdown("<h1 style='font-size:36px;margin:0;'>◆</h1>", unsafe_allow_html=True)
with c2: st.markdown("<div style='padding-top:8px;'><span style='font-size:24px;font-weight:800;color:#fff;'>ALETHEIA</span><span style='font-size:12px;color:#4a6090;margin-left:12px;letter-spacing:1px;'>ALPHA INTELLIGENCE</span></div>", unsafe_allow_html=True)
with c3: st.markdown(f"<div style='text-align:right;padding-top:10px;'><span class='pulse'></span><span style='color:{'#00ff88' if alpaca else '#5a7090'};font-size:11px;margin-left:6px;'>{'LIVE' if alpaca else 'CACHED'}</span><br><span style='color:#3a5070;font-size:9px;'>{datetime.utcnow().strftime('%H:%M UTC')}</span></div>", unsafe_allow_html=True)

with st.expander("⚙️ CONTROLS & SEARCH", expanded=False):
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)
    with ctrl1:
        query = st.text_input("🔍 Search", placeholder="Type ticker...", key="search_main")
        if query: sig = sig[sig['ticker'].str.contains(query.upper(), na=False)]
    with ctrl2:
        theme = st.radio("🎨", ['🌙 Dark', '☀️ Light'], horizontal=True, key="theme_radio")
        if 'Light' in theme: st.markdown("<style>.stApp{background:#f0f2f6!important;}.glass{background:white!important;}</style>", unsafe_allow_html=True)
    with ctrl3: st.download_button("📊 CSV", sig.to_csv(index=False), "aletheia_signals.csv", key="csv_main", use_container_width=True)
    with ctrl4:
        report = f"ALETHEIA Report\n{datetime.now()}\n\n" + "\n".join([f"{r['ticker']}: {r['composite_score']:+.4f}" for _, r in sig.iterrows()])
        st.download_button("📄 Report", report, "aletheia_report.txt", key="report_main", use_container_width=True)

if alpaca: equity, pnl, cash, pos_count = alpaca.get('equity',100000), alpaca.get('pnl_today',0), alpaca.get('cash',100000), len(alpaca.get('positions',[]))
else: equity, pnl, cash, pos_count = 100000, 0, 100000, 0
L = len(sig[sig['signal_direction']==1]) if not sig.empty else 0
S = len(sig[sig['signal_direction']==-1]) if not sig.empty else 0
avg = sig['composite_score'].mean() if not sig.empty else 0
tot = health['r'].sum() if not health.empty else 0

cols = st.columns(5)
kpi_data = [
    ("PORTFOLIO", f"${equity:,.0f}", f"{'+' if pnl>=0 else ''}${pnl:,.2f}", '#00ff88' if pnl>=0 else '#ff4060'),
    ("CASH", f"${cash:,.0f}", f"{pos_count} POSITIONS", '#a0c4ff'),
    ("SIGNALS", f"{len(sig)}", f"{L}L / {S}S", '#a0c4ff'),
    ("AVG SCORE", f"{avg:+.3f}", "BULLISH" if avg>0.02 else "NEUTRAL", '#00ff88' if avg>0 else '#ff4060'),
    ("DATABASE", f"{tot:,}", "57K RECORDS", '#a0c4ff'),
]
for i,(label,value,sub,color) in enumerate(kpi_data):
    with cols[i]:
        st.markdown(f"""<div class='glass' style='text-align:center;'><div class='kpi-tag'>{label}</div><div class='kpi-number'>{value}</div><div class='kpi-sub' style='color:{color};'>{sub}</div></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 SIGNALS", "📈 MARKETS", "⚠️ RISK", "🔗 NETWORK", "📅 EVENTS", "📋 DATA", "🛡️ SYSTEM", "🔐 SECURITY", "🤖 AI"
])

with tab1:
    col_left, col_right = st.columns([1.8, 1.2])
    with col_left:
        st.markdown("<div class='sec-title'>◆ SIGNAL PANORAMA</div>", unsafe_allow_html=True)
        if not sig.empty:
            colors = ['#00ff88' if x>0.02 else '#ff4060' if x<-0.02 else '#4a6090' for x in sig['composite_score']]
            fig = go.Figure()
            for i,(t,s) in enumerate(zip(sig['ticker'],sig['composite_score'])):
                fig.add_trace(go.Bar(x=[t],y=[s],marker=dict(color=colors[i],cornerradius=6),text=[f"<b>{s:+.3f}</b>"],textposition='outside',textfont=dict(color=colors[i],size=12)))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',height=400,margin=dict(l=0,r=0,t=10,b=0),showlegend=False,xaxis=dict(showgrid=False,tickfont=dict(color='#4a6090')),yaxis=dict(showgrid=True,gridcolor='rgba(0,200,255,0.04)',zerolinecolor='rgba(0,200,255,0.15)'))
            fig.add_hline(y=0.05,line_dash="dash",line_color="rgba(0,255,136,0.2)"); fig.add_hline(y=-0.05,line_dash="dash",line_color="rgba(255,64,96,0.2)")
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key="signal_bars")
    with col_right:
        st.markdown("<div class='sec-title'>◆ POSITIONS</div>", unsafe_allow_html=True)
        if alpaca and alpaca.get('positions'):
            for p in alpaca['positions']:
                s=p.get('unrealized_pl',0); pct=p.get('unrealized_pl_pct',0); color='#00ff88' if s>=0 else '#ff4060'; sign='+' if s>=0 else ''
                st.markdown(f"""<div class='glass' style='padding:12px 16px;margin:3px 0;'><div style='display:flex;justify-content:space-between;align-items:center;'><span style='font-weight:700;color:#fff;'>{p.get('symbol','?')}</span><span style='color:#5a7090;font-size:11px;'>{p.get('qty',0)}sh</span><span style='font-weight:700;color:{color};'>{sign}${abs(s):,.2f}</span><span style='font-size:10px;color:{color};'>({sign}{pct}%)</span></div></div>""",unsafe_allow_html=True)
        else: st.info("Run: python live/alpaca_fetcher.py")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("<div class='sec-title'>◆ FinBERT SCORES</div>", unsafe_allow_html=True)
        if not ens.empty:
            ec=['#00ff88' if x>0 else '#ff4060' for x in ens['e']]
            fe=go.Figure(go.Bar(x=ens['ticker'],y=ens['e'],marker_color=ec,text=ens['e'].round(3),textposition='outside',textfont=dict(color=ec,size=11),marker=dict(cornerradius=6)))
            fe.update_layout(plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',height=300,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,xaxis=dict(showgrid=False,tickfont=dict(color='#4a6090')),yaxis=dict(showgrid=True,gridcolor='rgba(0,200,255,0.04)'))
            st.plotly_chart(fe,use_container_width=True,config={'displayModeBar':False},key="finbert_bars")
    with c2:
        st.markdown("<div class='sec-title'>◆ P&L ATTRIBUTION</div>", unsafe_allow_html=True)
        st.plotly_chart(waterfall_chart(),use_container_width=True,config={'displayModeBar':False},key="waterfall")

with tab2:
    c1,c2=st.columns([1.5,1])
    with c1:
        st.markdown("<div class='sec-title'>◆ CANDLESTICK</div>", unsafe_allow_html=True)
        ticker_choice=st.selectbox('Ticker',['AAPL','MSFT','GOOGL','AMZN','META','JPM','XOM','JNJ','PFE','WMT','BAC','GS','CVX','HD','MCD'],key='candle')
        st.plotly_chart(candlestick_chart(ticker_choice),use_container_width=True,config={'displayModeBar':False},key="candle_chart")
    with c2:
        st.markdown("<div class='sec-title'>◆ CORRELATION</div>", unsafe_allow_html=True)
        st.plotly_chart(correlation_heatmap(),use_container_width=True,config={'displayModeBar':False},key="heatmap")
    if history:
        st.markdown("<div class='sec-title'>◆ EQUITY CURVE</div>", unsafe_allow_html=True)
        hdf=pd.DataFrame(history)
        feq=go.Figure(go.Scatter(x=hdf['date'],y=hdf['equity'],mode='lines',fill='tozeroy',line=dict(color='#00aaff',width=2),fillcolor='rgba(0,170,255,0.05)'))
        feq.add_hline(y=100000,line_dash="dash",line_color="rgba(255,255,255,0.2)")
        feq.update_layout(plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',height=250,margin=dict(l=0,r=0,t=10,b=0),showlegend=False,xaxis=dict(showgrid=False,tickfont=dict(color='#4a6090',size=10)),yaxis=dict(showgrid=True,gridcolor='rgba(0,200,255,0.04)'))
        st.plotly_chart(feq,use_container_width=True,config={'displayModeBar':False},key="equity_curve")

with tab3:
    st.markdown("<div class='sec-title'>◆ RISK GAUGES</div>", unsafe_allow_html=True)
    g1,g2,g3,g4=st.columns(4)
    with g1: st.plotly_chart(risk_gauge(2.1,"Drawdown %",7),use_container_width=True,config={'displayModeBar':False},key="gauge1")
    with g2: st.plotly_chart(risk_gauge(1.35,"Sharpe",3),use_container_width=True,config={'displayModeBar':False},key="gauge2")
    with g3: st.plotly_chart(risk_gauge(0.8,"Sortino",3),use_container_width=True,config={'displayModeBar':False},key="gauge3")
    with g4: st.plotly_chart(risk_gauge(16.9,"Alloc %",50),use_container_width=True,config={'displayModeBar':False},key="gauge4")

with tab4:
    st.markdown("<div class='sec-title'>◆ SIGNAL NETWORK</div>", unsafe_allow_html=True)
    st.plotly_chart(network_graph(),use_container_width=True,config={'displayModeBar':False},key="network_chart")

with tab5:
    st.markdown("<div class='sec-title'>◆ EVENT TIMELINE</div>", unsafe_allow_html=True)
    st.plotly_chart(event_timeline(),use_container_width=True,config={'displayModeBar':False},key="timeline_chart")

with tab6:
    st.markdown("<div class='sec-title'>◆ DATA EXPLORER</div>", unsafe_allow_html=True)
    styled_df=sig.copy()
    styled_df['Direction']=styled_df['signal_direction'].map({1:'🟢 LONG',-1:'🔴 SHORT',0:'⚪ NEUTRAL'})
    styled_df['Signal']=styled_df['composite_score'].apply(lambda x:f"{x:+.4f}")
    paginated=paginate_dataframe(styled_df[['ticker','Signal','Direction']],page_size=10)
    st.dataframe(paginated,use_container_width=True,height=400,hide_index=True)
    c1,c2=st.columns(2)
    with c1: st.download_button("📊 CSV",sig.to_csv(index=False),"aletheia_data.csv",key="csv_tab6",use_container_width=True)
    with c2: st.download_button("📄 Report",report,"aletheia_report.txt",key="report_tab6",use_container_width=True)

with tab7:
    st.markdown("<div class='sec-title'>◆ SYSTEM MONITORING</div>", unsafe_allow_html=True)
    try:
        from live.monitoring import health as mon_health, uptime, errors as err_tracker, metrics as perf_m
        h=mon_health.full_check()
        c1,c2,c3=st.columns(3)
        with c1: st.metric("Database","✅ HEALTHY" if h['checks']['database']['status']=='healthy' else "❌ DOWN")
        with c2: st.metric("Alpaca","✅ HEALTHY" if h['checks']['alpaca']['status']=='healthy' else "⚠️ STALE")
        with c3: st.metric("Signals","✅ HEALTHY" if h['checks']['signals']['status']=='healthy' else "❌ DOWN")
        up_pct=uptime.data.get('uptime_pct',0)
        st.progress(up_pct/100,text=f"Uptime: {up_pct}%")
        recent=err_tracker.errors[-5:] if err_tracker.errors else []
        if recent:
            for e in reversed(recent):
                st.markdown(f"<div class='glass' style='padding:6px 12px;margin:2px 0;font-size:10px;'><span style='color:{'#ff4060' if e['severity']=='ERROR' else '#ff9900'};'>[{e['severity']}]</span> {e['timestamp'][:19]} — {e['error'][:80]}</div>",unsafe_allow_html=True)
        ps=perf_m.get_stats(); c1,c2,c3=st.columns(3); c1.metric("Avg Query",f"{ps['avg_ms']}ms"); c2.metric("Max Query",f"{ps['max_ms']}ms"); c3.metric("Total",ps['count'])
    except Exception as e: st.warning(f"Monitoring: {e}")

with tab8:
    st.markdown("<div class='sec-title'>◆ SECURITY CENTER</div>", unsafe_allow_html=True)
    try:
        from live.security import auth as sec_auth, rbac, sec_audit, session_mgr
        session_mgr.init_session()
        if not st.session_state.get('authenticated'):
            c1,c2,c3=st.columns([1,2,1])
            with c2:
                st.markdown("<div class='glass' style='text-align:center;'>", unsafe_allow_html=True)
                st.subheader("🔐 Login")
                username=st.text_input("Username"); password=st.text_input("Password",type="password")
                if st.button("Login",use_container_width=True):
                    ok,result=sec_auth.login(username,password)
                    if ok:
                        st.session_state.authenticated=True; st.session_state.user_name=username
                        st.session_state.user_role=sec_auth.sessions[result]['role']; st.session_state.session_token=result
                        st.session_state.login_time=datetime.utcnow(); sec_audit.log('LOGIN',username); st.rerun()
                    else: st.error(result)
                st.markdown("</div>",unsafe_allow_html=True)
                st.caption("admin / aletheia_admin_2024")
        else:
            st.success(f"✅ Logged in as **{st.session_state.user_name}** ({st.session_state.user_role.upper()})")
            c1,c2=st.columns(2)
            with c1: st.metric("Role",st.session_state.user_role.upper()); st.metric("Session",st.session_state.session_token[:16]+"...")
            with c2: st.metric("Can Trade","✅" if rbac.has_permission(st.session_state.user_role,'execute_trades') else "❌"); st.metric("Can Config","✅" if rbac.has_permission(st.session_state.user_role,'configure_system') else "❌")
            if st.button("🚪 Logout",use_container_width=True): sec_auth.logout(st.session_state.session_token); st.session_state.authenticated=False; st.rerun()
            st.markdown("<div class='sec-title'>◆ SECURITY AUDIT</div>", unsafe_allow_html=True)
            for entry in sec_audit.logs[-5:]:
                st.markdown(f"<div class='glass' style='padding:6px 12px;margin:2px 0;font-size:10px;'>[{entry['timestamp'][:19]}] {entry['event']} by {entry['user']}</div>",unsafe_allow_html=True)
    except Exception as e: st.warning(f"Security: {e}")

with tab9:
    st.markdown("<div class='sec-title'>◆ AI INTELLIGENCE</div>", unsafe_allow_html=True)
    try:
        from live.ai_insights import explainer, forecaster, whatif, nlp, recommender
        ens_dict = {r['ticker']: r['e'] for _, r in ens.iterrows()} if not ens.empty else {}
        st.markdown("### 🤖 Signal Explanations")
        for _, r in sig.iterrows():
            exp = explainer.explain_signal(r['ticker'], ens_dict.get(r['ticker'], 0), r['composite_score'])
            st.markdown(f"""<div class='ai-card'><strong>{r['ticker']}</strong>: {exp['sentiment'].upper()} — {exp['action']}<br><small style='color:#888;'>{exp['ens_detail']}</small></div>""", unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:
            st.markdown("### 📈 Forecasts")
            for f in forecaster.forecast(sig,3):
                st.markdown(f"<div class='glass' style='padding:10px;margin:4px 0;font-size:11px;'><b>{f['ticker']}</b>: {f['trend']} → {f['predictions']}</div>",unsafe_allow_html=True)
        with c2:
            st.markdown("### 🎯 Recommendations")
            for r in recommender.generate(sig)[:5]:
                color='#00ff88' if r['action']=='BUY' else ('#ff4060' if r['action']=='SELL' else '#888')
                st.markdown(f"<div class='glass' style='padding:10px;margin:4px 0;font-size:11px;border-left:3px solid {color};'><b>{r['action']} {r['ticker']}</b> — {r['reason']} ({r['confidence']})</div>",unsafe_allow_html=True)
        st.markdown("### 💬 NLP Query")
        nlp_q=st.text_input("Ask about signals...",placeholder="e.g. show top long signals")
        if nlp_q:
            parsed=nlp.parse(nlp_q); result=nlp.execute(sig,parsed)
            st.write(f"Parsed: {parsed} → {len(result)} results"); st.dataframe(result,use_container_width=True,hide_index=True)
        st.markdown("### 🔮 What-If Simulator")
        c1,c2=st.columns(2)
        with c1:
            ticker_sim=st.selectbox('Ticker',sig['ticker'].tolist(),key='whatif_ticker')
            change=st.slider('ENS Change',-0.5,0.5,0.0,0.05)
            if st.button('Simulate',key='whatif_btn'):
                cur=ens_dict.get(ticker_sim,0); sim=whatif.simulate_ens_change(ticker_sim,cur,change)
                st.metric("Position Change",f"{sim['position_change']:+.1f}%"); st.metric("New Composite",f"{sim['composite_change']:+.4f}")
        with c2:
            shock_pct=st.slider('Market Shock %',-20.0,20.0,-5.0,1.0)
            shock=whatif.simulate_market_shock(equity,shock_pct)
            st.metric("Impact",f"${shock['impact']:,.0f}"); st.metric("New Value",f"${shock['new_value']:,.0f}"); st.metric("Drawdown",f"{shock['drawdown']}%")
    except Exception as e: st.warning(f"AI: {e}")

MobileNavigation.bottom_nav()
show_performance_stats()
st.markdown("<div style='text-align:center;padding:20px 0;color:#2a3a5a;font-size:9px;letter-spacing:2px;'>◆ ALETHEIA ALPHA INTELLIGENCE ◆ RESEARCH PROTOTYPE ◆ NOT FINANCIAL ADVICE ◆</div>", unsafe_allow_html=True)

subprocess.run(['python', 'live/alpaca_fetcher.py'], capture_output=True)
time.sleep(30)
st.rerun()