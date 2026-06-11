"""CMI Signal Generator - Combines jobs + web into CMI score"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from loguru import logger
from models.cmi.jobs_analyzer import JobsAnalyzer
from models.cmi.web_monitor import WebMonitor


class CMISignalGenerator:
    def __init__(self):
        self.jobs = JobsAnalyzer()
        self.web = WebMonitor()

    def generate(self, ticker, job_titles, web_old, web_new):
        job_result = self.jobs.analyze(job_titles)
        web_change = self.web.calculate_change(web_old, web_new)
        job_z = max(-1.0, min(1.0, job_result['anomaly_z'] / 10.0))
        cmi_final = round(0.6 * job_z + 0.4 * web_change, 4)
        return {
            'cmi_final': cmi_final,
            'job_anomaly': round(job_z, 4),
            'web_change': web_change
        }

    def batch_generate(self, db_path="aletheia.db"):
        conn = duckdb.connect(db_path)

        samples = [
            {
                'ticker': 'AAPL',
                'jobs': ['Product Manager AR', 'AI Research Scientist',
                         'Regional Manager India', 'Compliance Officer Finance',
                         'Software Engineer Vision Pro'],
                'web_old': 'iPhone. Cloud services.',
                'web_new': 'iPhone. AI features. Vision Pro. Cloud AI.'
            },
            {
                'ticker': 'JPM',
                'jobs': ['Risk Analyst Crypto', 'Compliance Officer Sanctions',
                         'Investment Banker Tech', 'Branch Manager Texas'],
                'web_old': 'Banking. Wealth.',
                'web_new': 'Banking. Wealth. Digital banking. Crypto desk.'
            },
            {
                'ticker': 'MSFT',
                'jobs': ['AI Engineer Copilot', 'Cloud Architect Azure',
                         'Data Center Operations', 'Compliance Manager EU'],
                'web_old': 'Windows. Office.',
                'web_new': 'Windows. Office. Copilot AI. Azure expansion.'
            },
        ]

        for s in samples:
            result = self.generate(s['ticker'], s['jobs'],
                                   s['web_old'], s['web_new'])
            rid = f"cmi_{s['ticker']}_2024"
            conn.execute("""
                INSERT INTO cmi_scores 
                (id, ticker, score_date, cmi_final, job_anomaly_score, web_change_score)
                VALUES (?, ?, '2024-06-15', ?, ?, ?)
            """, [rid, s['ticker'], result['cmi_final'],
                  result['job_anomaly'], result['web_change']])
            logger.info(f"  {s['ticker']}: CMI={result['cmi_final']:+.3f}")

        conn.close()
        logger.info("CMI generation complete")


if __name__ == "__main__":
    CMISignalGenerator().batch_generate()