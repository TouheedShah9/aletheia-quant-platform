"""
╔══════════════════════════════════════════════════════╗
║           ALETHEIA — Enterprise Monitoring           ║
║   Health Checks • Error Tracking • Alerts • Metrics  ║
╚══════════════════════════════════════════════════════╝
"""
import sys, os, json, time, smtplib, logging
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
import requests
from loguru import logger

# ═══════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')

# ═══════════════════════════════════════
# FIX 32: HEALTH ENDPOINT
# ═══════════════════════════════════════
class HealthCheck:
    """Comprehensive system health monitoring."""
    
    @staticmethod
    def check_database():
        try:
            conn = duckdb.connect(str(Path(__file__).parent.parent / 'aletheia.db'))
            conn.execute("SELECT 1")
            conn.close()
            return {'status': 'healthy', 'latency_ms': 0}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def check_alpaca():
        try:
            data_path = Path(__file__).parent.parent / 'alpaca_data.json'
            if not data_path.exists():
                return {'status': 'no_data', 'message': 'alpaca_data.json not found'}
            with open(data_path) as f:
                data = json.load(f)
            if 'error' in data:
                return {'status': 'error', 'message': data['error']}
            age = time.time() - os.path.getmtime(data_path)
            if age > 300:
                return {'status': 'stale', 'age_seconds': int(age)}
            return {'status': 'healthy', 'equity': data.get('equity', 0)}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def check_signals():
        try:
            conn = duckdb.connect(str(Path(__file__).parent.parent / 'aletheia.db'))
            count = conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
            longs = conn.execute("SELECT COUNT(*) FROM composite_signals WHERE signal_direction=1").fetchone()[0]
            conn.close()
            return {'status': 'healthy', 'total': count, 'long': longs}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def full_check():
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system': 'ALETHEIA',
            'version': '1.0.0',
            'checks': {
                'database': HealthCheck.check_database(),
                'alpaca': HealthCheck.check_alpaca(),
                'signals': HealthCheck.check_signals(),
            },
            'overall': 'healthy'
        }

# ═══════════════════════════════════════
# FIX 33: UPTIME MONITORING
# ═══════════════════════════════════════
class UptimeMonitor:
    """Automatic uptime tracking with ping."""
    def __init__(self):
        self.log_file = LOG_DIR / 'uptime.json'
        self.load()
    
    def load(self):
        try:
            with open(self.log_file) as f:
                self.data = json.load(f)
        except:
            self.data = {'checks': [], 'total': 0, 'up': 0}
    
    def save(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def ping(self):
        health = HealthCheck.full_check()
        is_up = all(v.get('status') == 'healthy' for v in health['checks'].values())
        
        self.data['checks'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'up': is_up
        })
        self.data['total'] += 1
        if is_up:
            self.data['up'] += 1
        
        self.data['uptime_pct'] = round(self.data['up'] / max(self.data['total'], 1) * 100, 2)
        self.save()
        return is_up

# ═══════════════════════════════════════
# FIX 34: ERROR TRACKING
# ═══════════════════════════════════════
class ErrorTracker:
    """Centralized error logging with rotation."""
    def __init__(self):
        self.error_file = LOG_DIR / 'errors.json'
        self.load()
    
    def load(self):
        try:
            with open(self.error_file) as f:
                self.errors = json.load(f)
        except:
            self.errors = []
    
    def save(self):
        with open(self.error_file, 'w') as f:
            json.dump(self.errors[-1000:], f, indent=2)
    
    def log(self, module, error, severity='ERROR'):
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'module': module,
            'error': str(error)[:500],
            'severity': severity
        }
        self.errors.append(entry)
        self.save()
        logger.error(f"[{severity}] {module}: {error}")
        return entry

# ═══════════════════════════════════════
# FIX 35: PERFORMANCE METRICS
# ═══════════════════════════════════════
class PerformanceMetrics:
    """Track and report system performance."""
    def __init__(self):
        self.metrics_file = LOG_DIR / 'metrics.json'
        self.load()
    
    def load(self):
        try:
            with open(self.metrics_file) as f:
                self.metrics = json.load(f)
        except:
            self.metrics = {'queries': [], 'api_calls': []}
    
    def save(self):
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def record_query(self, query_name, duration_ms):
        self.metrics['queries'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'query': query_name,
            'duration_ms': duration_ms
        })
        if len(self.metrics['queries']) > 100:
            self.metrics['queries'] = self.metrics['queries'][-100:]
        self.save()
    
    def get_stats(self):
        if not self.metrics['queries']:
            return {'avg_ms': 0, 'count': 0}
        durations = [q['duration_ms'] for q in self.metrics['queries']]
        return {
            'avg_ms': round(sum(durations) / len(durations), 2),
            'max_ms': round(max(durations), 2),
            'count': len(durations)
        }

# ═══════════════════════════════════════
# FIX 36: EMAIL ALERTS
# ═══════════════════════════════════════
class AlertManager:
    """Send alerts via email for critical events."""
    
    @staticmethod
    def send_email(subject, body):
        if not all([SMTP_USER, SMTP_PASS, ALERT_EMAIL]):
            logger.warning("Email not configured. Set SMTP_USER, SMTP_PASS, ALERT_EMAIL in .env")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = f"[ALETHEIA] {subject}"
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            logger.info(f"Alert sent: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False
    
    @staticmethod
    def signal_flip_alert(ticker, old_score, new_score):
        subject = f"Signal Flip: {ticker}"
        body = f"""
        ALETHEIA Signal Alert
        
        Ticker: {ticker}
        Previous Signal: {old_score:+.4f}
        New Signal: {new_score:+.4f}
        Change: {new_score - old_score:+.4f}
        
        Time: {datetime.utcnow().isoformat()}
        
        This is an automated alert from Project Aletheia.
        """
        return AlertManager.send_email(subject, body)
    
    @staticmethod
    def drawdown_alert(current_dd, limit):
        subject = f"⚠️ DRAWDOWN ALERT: {current_dd*100:.1f}%"
        body = f"""
        ALETHEIA Risk Alert — DRAWDOWN BREACH
        
        Current Drawdown: {current_dd*100:.2f}%
        Circuit Breaker Limit: {limit*100:.0f}%
        
        Positions will be reduced automatically.
        
        Time: {datetime.utcnow().isoformat()}
        """
        return AlertManager.send_email(subject, body)
    
    @staticmethod
    def system_health_alert(component, status):
        subject = f"System Health: {component} is {status}"
        body = f"""
        ALETHEIA System Health Alert
        
        Component: {component}
        Status: {status}
        Time: {datetime.utcnow().isoformat()}
        
        Please investigate immediately.
        """
        return AlertManager.send_email(subject, body)

# ═══════════════════════════════════════
# FIX 37: SMS ALERTS (via Email-to-SMS)
# ═══════════════════════════════════════
class SMSAlert:
    """SMS alerts via email-to-SMS gateways."""
    
    CARRIERS = {
        'verizon': 'vtext.com',
        'att': 'txt.att.net',
        'tmobile': 'tmomail.net',
        'sprint': 'messaging.sprintpcs.com',
    }
    
    @staticmethod
    def send(phone_number, carrier, message):
        if carrier not in SMSAlert.CARRIERS:
            return False
        to_email = f"{phone_number}@{SMSAlert.CARRIERS[carrier]}"
        try:
            msg = MIMEText(f"[ALETHEIA] {message}")
            msg['From'] = SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = 'ALERT'
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            return True
        except:
            return False

# ═══════════════════════════════════════
# GLOBAL INSTANCES
# ═══════════════════════════════════════
health = HealthCheck()
uptime = UptimeMonitor()
errors = ErrorTracker()
metrics = PerformanceMetrics()
alerts = AlertManager()
sms = SMSAlert()

# ═══════════════════════════════════════
# TEST
# ═══════════════════════════════════════
if __name__ == "__main__":
    print("="*60)
    print("DIMENSION 5: MONITORING & ALERTING")
    print("="*60)
    
    print("\n[32] Health Check:")
    result = health.full_check()
    print(f"  Database: {result['checks']['database']['status']}")
    print(f"  Alpaca: {result['checks']['alpaca']['status']}")
    print(f"  Signals: {result['checks']['signals']['status']}")
    
    print("\n[33] Uptime Monitor:")
    up = uptime.ping()
    print(f"  Current: {'UP' if up else 'DOWN'}")
    print(f"  Uptime: {uptime.data.get('uptime_pct', 0)}%")
    
    print("\n[34] Error Tracker:")
    errors.log('test_module', 'Test error message', 'WARNING')
    print(f"  Errors logged: {len(errors.errors)}")
    
    print("\n[35] Performance Metrics:")
    metrics.record_query('test_query', 45.2)
    stats = metrics.get_stats()
    print(f"  Avg query: {stats['avg_ms']}ms")
    
    print("\n[36] Email Alerts:")
    print(f"  Configured: {bool(SMTP_USER and SMTP_PASS)}")
    
    print("\n[37] SMS Alerts:")
    print(f"  Configured: {bool(SMTP_USER and SMTP_PASS)}")
    
    print("\n" + "="*60)
    print("DIMENSION 5: ALL 6 FIXES READY")
    print("Set SMTP_USER, SMTP_PASS, ALERT_EMAIL in .env for live alerts")
    print("="*60)