"""Quick Gmail test with timeout"""
import smtplib, os
from dotenv import load_dotenv
load_dotenv()

print("Testing Gmail connection...")
try:
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    server.starttls()
    server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
    print("✅ Gmail login: SUCCESS")
    server.quit()
except Exception as e:
    print(f"❌ Gmail login: FAILED - {e}")