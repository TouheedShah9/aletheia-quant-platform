"""
ENS Preprocessor - Clean and normalize transcript text
Runs on laptop. No ML dependencies.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger


class ENSPreprocessor:
    """Cleans earnings call transcripts before scoring."""
    
    # Boilerplate to remove
    SAFE_HARBOR_PATTERNS = [
        r'This (call|presentation|conference call) (contains|may contain|includes) forward-looking statements',
        r'Forward-looking statements involve risks and uncertainties',
        r'I would now like to turn the (call|conference) over to',
        r'Please note that today\'s call is being recorded',
        r'All (lines|participants) (are|will be) in (a )?listen-only mode',
        r'I will now turn the call over to',
        r'Thank you for standing by',
        r'Welcome to the .* earnings (call|conference call)',
        r'At this time, I would like to welcome everyone to',
        r'Certain statements made on this call',
        r'Actual results may differ materially',
        r'Please refer to our SEC filings',
    ]
    
    # Text normalization patterns
    FILLER_WORDS = [
        r'\b(um|uh|er|ah|hmm|like, you know|I mean)\b'
    ]
    
    @staticmethod
    def clean(text: str) -> str:
        """Clean transcript text for scoring."""
        if not text:
            return ""
        
        original_len = len(text.split())
        
        # Remove safe harbor boilerplate
        for pattern in ENSPreprocessor.SAFE_HARBOR_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove filler words
        for pattern in ENSPreprocessor.FILLER_WORDS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove empty lines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s.,!?;:\'\"()-]', '', text)
        
        cleaned_len = len(text.split())
        if cleaned_len < original_len:
            logger.debug(f"Preprocessor: {original_len} -> {cleaned_len} words "
                        f"({original_len - cleaned_len} removed)")
        
        return text.strip()
    
    @staticmethod
    def extract_financial_metrics(text: str) -> dict:
        """Extract key financial numbers mentioned in transcript."""
        metrics = {}
        
        # Revenue patterns
        rev_match = re.search(r'revenue\s*(?:of|was|were|reached)?\s*\$?(\d+\.?\d*)\s*(billion|million|B|M)?', text, re.IGNORECASE)
        if rev_match:
            metrics['revenue_mentioned'] = float(rev_match.group(1))
            metrics['revenue_unit'] = rev_match.group(2) or 'unknown'
        
        # EPS patterns
        eps_match = re.search(r'earnings per share\s*(?:of|was|were)?\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if eps_match:
            metrics['eps_mentioned'] = float(eps_match.group(1))
        
        # Growth patterns
        growth_match = re.search(r'(?:grew|increased|growth\s*(?:of|was)?)\s*(\d+\.?\d*)\s*(?:%|percent)', text, re.IGNORECASE)
        if growth_match:
            metrics['growth_mentioned'] = float(growth_match.group(1))
        
        return metrics


def test_preprocessor():
    """Quick test."""
    sample = """This call contains forward-looking statements. 
    Actual results may differ materially.
    Um, I mean, our revenue was $89.5 billion, up 5 percent.
    Thank you for standing by."""
    
    cleaned = ENSPreprocessor.clean(sample)
    metrics = ENSPreprocessor.extract_financial_metrics(cleaned)
    
    print("Original:", sample[:80])
    print("Cleaned:", cleaned[:80])
    print("Metrics:", metrics)
    
    # Assertions
    assert 'forward-looking' not in cleaned.lower(), "Safe harbor not removed"
    assert 'um' not in cleaned.lower(), "Filler words not removed"
    assert metrics.get('revenue_mentioned') == 89.5, "Revenue not extracted"
    
    print("\nAll preprocessor tests passed.")


if __name__ == "__main__":
    test_preprocessor()