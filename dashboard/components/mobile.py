import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os, json, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from loguru import logger

SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK', '')

def inject_responsive_css():
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumns { flex-direction: column !important; }
        .stColumns > div { width: 100% !important; }
        .kpi-number { font-size: 24px !important; }
        .glass { padding: 16px !important; }
        .stTabs [data-baseweb="tab"] { font-size: 9px !important; padding: 6px 10px !important; }
    }
    @media print {
        .stApp { background: white !important; }
        .glass { border: 1px solid #ddd !important; box-shadow: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

def generate_pwa_manifest():
    manifest = {
        "name": "Aletheia Alpha Platform",
        "short_name": "Aletheia",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#060b1f",
        "theme_color": "#00aaff",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    manifest_path = Path(__file__).parent.parent / 'static' / 'manifest.json'
    manifest_path.parent.mkdir(exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    return manifest_path

class EmailReportGenerator:
    @staticmethod
    def generate_report(signals_df, alpaca_data=None):
        report = f"""╔══════════════════════════════╗
║  ALETHEIA DAILY ALPHA REPORT ║
║     {datetime.now().strftime('%Y-%m-%d')}                    ║
╚══════════════════════════════╝

PORTFOLIO: """
        if alpaca_data:
            report += f"${alpaca_data.get('equity',0):,.2f} (P&L: ${alpaca_data.get('pnl_today',0):+,.2f})"
        report += "\n\nSIGNALS:\n"
        for _, row in signals_df.iterrows():
            d = 'LONG' if row['signal_direction']==1 else ('SHORT' if row['signal_direction']==-1 else 'NEUTRAL')
            report += f"  {row['ticker']:5s}: {row['composite_score']:+.4f} -> {d}\n"
        report += f"\nGenerated: {datetime.utcnow().isoformat()}\nALETHEIA ALPHA INTELLIGENCE PLATFORM"
        return report
    
    @staticmethod
    def send_email_report(report_text, recipient=None):
        if not SMTP_USER or not SMTP_PASS:
            return False, "Email not configured"
        to = recipient or ALERT_EMAIL
        if not to:
            return False, "No recipient"
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = to
            msg['Subject'] = f"[ALETHEIA] Daily Alpha Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg.attach(MIMEText(report_text, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            logger.info(f"Report sent to {to}")
            return True, f"Sent to {to}"
        except Exception as e:
            return False, str(e)

class SlackIntegration:
    @staticmethod
    def send_signal_update(signals_df):
        if not SLACK_WEBHOOK:
            return False, "Not configured"
        try:
            import requests
            blocks = [{"type": "header", "text": {"type": "plain_text", "text": "Aletheia Alpha Signals"}}]
            for _, row in signals_df.iterrows():
                e = '🟢' if row['composite_score']>0.02 else ('🔴' if row['composite_score']<-0.02 else '⚪')
                d = 'LONG' if row['signal_direction']==1 else ('SHORT' if row['signal_direction']==-1 else 'NEUTRAL')
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"{e} *{row['ticker']}*: {row['composite_score']:+.4f} ({d})"}})
            resp = requests.post(SLACK_WEBHOOK, json={"blocks": blocks})
            return resp.status_code == 200, "Posted"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_alert(message, color='warning'):
        if not SLACK_WEBHOOK:
            return False
        colors = {'warning': '#ff9900', 'danger': '#ff4060', 'good': '#00ff88'}
        try:
            import requests
            payload = {"attachments": [{"color": colors.get(color,'#ff9900'), "text": f"*ALETHEIA ALERT*: {message}"}]}
            requests.post(SLACK_WEBHOOK, json=payload)
            return True
        except:
            return False

class APIServer:
    @staticmethod
    def get_signals_json(signals_df):
        signals_list = []
        for _, row in signals_df.iterrows():
            signals_list.append({
                'ticker': row['ticker'],
                'composite_score': round(float(row['composite_score']), 4),
                'signal_direction': int(row['signal_direction']),
                'direction_text': 'LONG' if row['signal_direction']==1 else ('SHORT' if row['signal_direction']==-1 else 'NEUTRAL')
            })
        return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat(), 'count': len(signals_list), 'signals': signals_list}
    
    @staticmethod
    def save_api_response(data, filename='api_response.json'):
        path = Path(__file__).parent.parent / filename
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return path

class MobileNavigation:
    @staticmethod
    def bottom_nav():
        st.markdown("""
        <style>
        @media (max-width: 768px) {
            .mobile-nav { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(10,15,40,0.95); backdrop-filter: blur(20px); display: flex; justify-content: space-around; padding: 8px 0; border-top: 1px solid rgba(0,200,255,0.1); z-index: 1000; }
            .mobile-nav a { color: #4a6090; text-decoration: none; font-size: 10px; text-align: center; }
            .main-content { padding-bottom: 60px; }
        }
        </style>
        <div class='mobile-nav'>
            <a href='?tab=signals'>📊</a><a href='?tab=markets'>📈</a><a href='?tab=risk'>⚠️</a><a href='?tab=ai'>🤖</a><a href='?tab=more'>⋯</a>
        </div>
        """, unsafe_allow_html=True)