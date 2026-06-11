"""
ENS Section Parser - Splits transcripts into speaker sections
Pure regex. No ML. Runs on 4GB laptop.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger


# Known speaker patterns across transcript formats
SPEAKER_PATTERNS = [
    # Format: "Tim Cook: Good afternoon..."
    r'(?P<speaker>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}):\s+',
    # Format: "Operator: Welcome to..."
    r'(?P<speaker>Operator):\s+',
    # Format: "QUESTION AND ANSWER SECTION"
    r'^(?P<section>QUESTION(?:\s+AND\s+ANSWER|S\s+AND\s+ANSWERS|S))\s*$',
    # Format: "Q&A" header
    r'^(?P<section>Q\s*&?\s*A)\s*$',
    # Format: "Analyst:" or "Analyst Name:"
    r'(?P<speaker>Analyst(?:\s+[A-Z][a-z]+)?):\s+',
]

# CEO name variations
CEO_NAMES = {
    'AAPL': ['Tim Cook', 'Tim'],
    'MSFT': ['Satya Nadella', 'Satya'],
    'GOOGL': ['Sundar Pichai', 'Sundar'],
    'AMZN': ['Andy Jassy', 'Andy'],
    'META': ['Mark Zuckerberg', 'Mark'],
    'JPM': ['Jamie Dimon', 'Jamie'],
    'BAC': ['Brian Moynihan', 'Brian'],
    'GS': ['David Solomon', 'David'],
    'JNJ': ['Joaquin Duato', 'Joaquin'],
    'PFE': ['Albert Bourla', 'Albert'],
    'XOM': ['Darren Woods', 'Darren'],
    'CVX': ['Mike Wirth', 'Mike'],
    'HD': ['Ted Decker', 'Ted'],
    'WMT': ['Doug McMillon', 'Doug'],
    'MCD': ['Chris Kempczinski', 'Chris'],
}

CFO_NAMES = {
    'AAPL': ['Luca Maestri', 'Luca'],
    'MSFT': ['Amy Hood', 'Amy'],
    'GOOGL': ['Ruth Porat', 'Ruth'],
    'AMZN': ['Brian Olsavsky', 'Brian'],
    'META': ['Susan Li', 'Susan'],
    'JPM': ['Jeremy Barnum', 'Jeremy'],
    'BAC': ['Alastair Borthwick', 'Alastair'],
    'GS': ['Denis Coleman', 'Denis'],
    'JNJ': ['Joe Wolk', 'Joe'],
    'PFE': ['David Denton', 'David'],
    'XOM': ['Kathy Mikells', 'Kathy'],
    'CVX': ['Pierre Breber', 'Pierre'],
    'HD': ['Richard McPhail', 'Richard'],
    'WMT': ['John David Rainey', 'John David'],
    'MCD': ['Ian Borden', 'Ian'],
}


class SectionParser:
    """Parses earnings call transcripts into structured sections."""
    
    def __init__(self, ticker: str = None):
        self.ticker = ticker or ''
        self.ceo_names = CEO_NAMES.get(ticker, [])
        self.cfo_names = CFO_NAMES.get(ticker, [])
    
    def identify_speaker(self, name: str) -> str:
        """Map speaker name to role."""
        name_lower = name.lower().strip()
        for ceo_name in self.ceo_names:
            if ceo_name.lower() in name_lower:
                return 'CEO'
        for cfo_name in self.cfo_names:
            if cfo_name.lower() in name_lower:
                return 'CFO'
        if 'operator' in name_lower:
            return 'OPERATOR'
        if 'analyst' in name_lower:
            return 'ANALYST'
        return 'EXEC'
    
    def parse(self, text: str) -> dict:
        """
        Split transcript into sections.
        
        Returns:
            {
                'prepared_ceo': str,
                'prepared_cfo': str,
                'qa_section': str,
                'has_qa': bool,
                'total_words': int,
                'sections_found': list
            }
        """
        result = {
            'prepared_ceo': '',
            'prepared_cfo': '',
            'qa_section': '',
            'has_qa': False,
            'total_words': len(text.split()),
            'sections_found': [],
            'sentences': []
        }
        
        lines = text.strip().split('\n')
        current_section = 'preamble'
        current_speaker = 'UNKNOWN'
        sections = {'prepared_ceo': [], 'prepared_cfo': [], 'qa': [], 'preamble': []}
        
        # Detect Q&A boundary
        qa_started = False
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for Q&A section header
            if re.search(r'^(Q\s*&?\s*A|QUESTION(?:\s+AND\s+ANSWER|S))', line_stripped, re.IGNORECASE):
                qa_started = True
                result['has_qa'] = True
                continue
            
            # Check for speaker line
            speaker_match = None
            for pattern in SPEAKER_PATTERNS:
                match = re.match(pattern, line_stripped)
                if match:
                    speaker_match = match
                    break
            
            if speaker_match and 'speaker' in speaker_match.groupdict():
                speaker_name = speaker_match.group('speaker')
                role = self.identify_speaker(speaker_name)
                
                # Extract the speech content after the colon
                content = line_stripped[speaker_match.end():].strip()
                
                if qa_started:
                    sections['qa'].append({'speaker': role, 'name': speaker_name, 'text': content})
                elif role == 'CEO':
                    sections['prepared_ceo'].append({'speaker': role, 'name': speaker_name, 'text': content})
                elif role == 'CFO':
                    sections['prepared_cfo'].append({'speaker': role, 'name': speaker_name, 'text': content})
                elif role == 'OPERATOR':
                    sections['preamble'].append({'text': content})
            else:
                # Continuation of previous speaker
                if sections['qa'] and qa_started:
                    sections['qa'][-1]['text'] += ' ' + line_stripped
                elif sections['prepared_cfo']:
                    sections['prepared_cfo'][-1]['text'] += ' ' + line_stripped
                elif sections['prepared_ceo']:
                    sections['prepared_ceo'][-1]['text'] += ' ' + line_stripped
        
        # Combine
        result['prepared_ceo'] = ' '.join([s['text'] for s in sections['prepared_ceo']])
        result['prepared_cfo'] = ' '.join([s['text'] for s in sections['prepared_cfo']])
        result['qa_section'] = ' '.join([s['text'] for s in sections['qa']])
        
        # Fallback: if regex failed, use heuristics
        if not result['prepared_ceo'] and not result['prepared_cfo']:
            logger.warning(f"No CEO/CFO sections found for {self.ticker}, using full text")
            result['prepared_ceo'] = text[:len(text)//2]
            result['prepared_cfo'] = text[len(text)//2:]
        
        # If no QA section detected by header, check for analyst mentions
        if not result['has_qa']:
            if 'Analyst:' in text or 'analyst' in text.lower():
                result['has_qa'] = True
        
        # Prepare sentence list for scoring
        all_text = ' '.join([result['prepared_ceo'], result['prepared_cfo'], result['qa_section']])
        result['sentences'] = [s.strip() for s in re.split(r'[.!?]+', all_text) if len(s.strip().split()) > 3]
        
        result['sections_found'] = []
        if result['prepared_ceo']:
            result['sections_found'].append('CEO_PREPARED')
        if result['prepared_cfo']:
            result['sections_found'].append('CFO_PREPARED')
        if result['qa_section']:
            result['sections_found'].append('QA')
        
        logger.info(f"Parsed {self.ticker}: {len(result['sentences'])} sentences, "
                   f"sections={result['sections_found']}, QA={result['has_qa']}")
        
        return result


def test_parser():
    """Quick test with sample transcript."""
    sample = """Operator: Welcome to the earnings call.
    
Tim Cook: This was a great quarter. Revenue exceeded expectations.
We are seeing strong demand across all products.

Luca Maestri: Gross margin was 45 percent. Operating income grew 10 percent.
    
Q&A
    
Analyst: What about China?
Tim: China remains a key market for us."""
    
    parser = SectionParser('AAPL')
    result = parser.parse(sample)
    
    assert len(result['prepared_ceo']) > 0, "CEO section missing"
    assert len(result['prepared_cfo']) > 0, "CFO section missing"
    assert result['has_qa'], "QA not detected"
    assert len(result['sentences']) > 0, "No sentences extracted"
    
    print("All parser tests passed.")
    print(f"CEO section: {result['prepared_ceo'][:80]}...")
    print(f"CFO section: {result['prepared_cfo'][:80]}...")
    print(f"QA section: {result['qa_section'][:80]}...")
    print(f"Sentences: {len(result['sentences'])}")


if __name__ == "__main__":
    test_parser()