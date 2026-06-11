"""CMI Jobs Analyzer - Detects hiring anomalies"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from loguru import logger

class JobsAnalyzer:
    EXPANSION_KEYWORDS = ['regional manager','country manager','market entry',
                          'international expansion','new markets','global growth']
    COMPLIANCE_KEYWORDS = ['sanctions','compliance officer','regulatory affairs',
                           'government relations','legal counsel','risk and compliance']
    PRODUCT_KEYWORDS = ['product manager','new product','research scientist',
                        'emerging technology','AI engineer','data scientist']
    
    @staticmethod
    def analyze(job_titles: list) -> dict:
        if not job_titles:
            return {'expansion':0,'compliance':0,'product':0,'total':0,'anomaly_z':0}
        total = len(job_titles)
        text = ' '.join(job_titles).lower()
        expansion = sum(1 for kw in JobsAnalyzer.EXPANSION_KEYWORDS if kw in text)
        compliance = sum(1 for kw in JobsAnalyzer.COMPLIANCE_KEYWORDS if kw in text)
        product = sum(1 for kw in JobsAnalyzer.PRODUCT_KEYWORDS if kw in text)
        return {
            'expansion': expansion/total if total else 0,
            'compliance': compliance/total if total else 0,
            'product': product/total if total else 0,
            'total': total,
            'anomaly_z': (expansion - 0.1) / 0.05 if total > 5 else 0
        }

if __name__ == "__main__":
    jobs = ['Product Manager AI','Data Scientist','Regional Manager APAC',
            'Compliance Officer','Software Engineer','Product Manager Cloud']
    result = JobsAnalyzer.analyze(jobs)
    print(f"Jobs: {result}")