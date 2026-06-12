"""
Professional Interactivity Components — All 9 UX fixes
"""
import streamlit as st
import pandas as pd
import base64
from datetime import datetime, timedelta
from io import BytesIO, StringIO

def drilldown_click(ticker, signals_df):
    """Click any ticker to see full analysis."""
    if ticker:
        st.markdown(f"### ◆ {ticker} — Full Analysis")
        data = signals_df[signals_df['ticker'] == ticker]
        if not data.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Signal Score", f"{data['composite_score'].values[0]:+.4f}")
            direction = data['signal_direction'].values[0]
            col2.metric("Direction", "LONG 🟢" if direction==1 else ("SHORT 🔴" if direction==-1 else "NEUTRAL ⚪"))
            col3.metric("Regime", data.get('market_regime', ['N/A']).values[0] if 'market_regime' in data else 'risk_on')
        return True
    return False

def search_filter(df, key="search"):
    """Global search bar with instant filtering."""
    query = st.text_input("🔍 Search tickers...", key=key, placeholder="Type AAPL, MSFT, JPM...")
    if query:
        return df[df['ticker'].str.contains(query.upper(), na=False)]
    return df

def sortable_table(df, key="sort"):
    """Click column headers to sort."""
    return st.dataframe(
        df.sort_values('composite_score', ascending=False) if 'composite_score' in df.columns else df,
        use_container_width=True, height=300,
        column_config={
            "ticker": "Ticker",
            "composite_score": st.column_config.NumberColumn("Signal", format="%+.4f"),
            "signal_direction": st.column_config.NumberColumn("Direction"),
        },
        hide_index=True
    )

def date_range_filter(key="date"):
    """Custom date range selector."""
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Start", datetime.now() - timedelta(days=30), key=f"{key}_start")
    with col2:
        end = st.date_input("End", datetime.now(), key=f"{key}_end")
    return start, end

def export_csv(df, filename="aletheia_data"):
    """Download data as CSV."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" class="glass" style="display:inline-block;padding:8px 16px;color:#00aaff;text-decoration:none;border-radius:8px;">📥 Download CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

def export_pdf(content="Report content", filename="aletheia_report"):
    """Download report as text file (PDF requires additional library)."""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}.txt" class="glass" style="display:inline-block;padding:8px 16px;color:#00aaff;text-decoration:none;border-radius:8px;">📄 Download Report</a>'
    st.markdown(href, unsafe_allow_html=True)

def dark_light_toggle():
    """Toggle between dark and light mode."""
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    
    theme = st.radio("🎨 Theme", ['🌙 Dark', '☀️ Light'], horizontal=True, label_visibility='collapsed')
    st.session_state.theme = 'dark' if 'Dark' in theme else 'light'
    
    if st.session_state.theme == 'light':
        st.markdown("""
        <style>
        .stApp { background: #f5f7fa !important; }
        .glass { background: white !important; border: 1px solid #e0e0e0 !important; }
        .kpi-number { -webkit-text-fill-color: #1a1a2e !important; }
        .sec-title { color: #666 !important; }
        </style>
        """, unsafe_allow_html=True)
    return st.session_state.theme

def keyboard_shortcuts():
    """Display keyboard shortcuts."""
    with st.expander("⌨️ Keyboard Shortcuts"):
        shortcuts = {
            "Ctrl+K": "Command palette",
            "Ctrl+F": "Search tickers",
            "Ctrl+E": "Export data",
            "Ctrl+D": "Toggle dark mode",
            "Ctrl+R": "Refresh data",
            "1-5": "Switch tabs",
        }
        for key, desc in shortcuts.items():
            st.markdown(f"`{key}` — {desc}")

def toast_notification(message, type="info"):
    """Show toast-style notification."""
    colors = {"info": "#00aaff", "success": "#00ff88", "warning": "#ff9900", "error": "#ff4060"}
    color = colors.get(type, "#00aaff")
    st.markdown(f"""
        <div style='background:{color}22; border-left:4px solid {color}; border-radius:8px; padding:12px 16px; margin:8px 0; animation:slideIn 0.3s ease;'>
            <span style='color:{color}; font-weight:600;'>{'🔔' if type=='info' else '✅' if type=='success' else '⚠️' if type=='warning' else '❌'} {message}</span>
        </div>
        <style>
        @keyframes slideIn {{ from {{ opacity:0; transform:translateY(-10px); }} to {{ opacity:1; transform:translateY(0); }} }}
        </style>
    """, unsafe_allow_html=True)

def loading_skeleton():
    """Show skeleton loading state."""
    st.markdown("""
        <div style='animation:pulse 1.5s infinite;'>
            <div style='height:20px; background:#1a2a4a; border-radius:4px; margin:8px 0; width:60%;'></div>
            <div style='height:20px; background:#1a2a4a; border-radius:4px; margin:8px 0; width:40%;'></div>
            <div style='height:200px; background:#1a2a4a; border-radius:8px; margin:12px 0;'></div>
        </div>
    """, unsafe_allow_html=True)