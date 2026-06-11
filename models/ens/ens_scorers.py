"""
ENS Dimension Scorers - Local (keyword-based) versions
GPU versions for Colab are in colab/ens_batch_processing.ipynb

Four dimensions:
1. TCS: Tone Confidence Score (sentiment proxy)
2. FGC: Forward Guidance Clarity
3. TAD: Topic Avoidance Detection
4. LHI: Linguistic Hedging Index
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
import config


class ToneConfidenceScorer:
    """
    TCS: Measures tone and confidence in prepared remarks.
    Local version uses keyword dictionaries.
    Colab version uses FinBERT.
    """
    
    POSITIVE_WORDS = {
        'strong', 'growth', 'record', 'exceed', 'momentum', 'confident',
        'accelerating', 'expanding', 'leading', 'innovative', 'excellent',
        'outstanding', 'exceptional', 'thrilled', 'pleased', 'proud',
        'all-time high', 'best-in-class', 'market leader', 'robust',
        'significant', 'substantial', 'impressive', 'remarkable'
    }
    
    NEGATIVE_WORDS = {
        'decline', 'weak', 'challenging', 'headwind', 'pressure', 'difficult',
        'disappointing', 'below', 'miss', 'slowdown', 'uncertainty',
        'volatility', 'risk', 'concern', 'cautious', 'softening',
        'deterioration', 'loss', 'restructuring', 'layoff', 'impairment',
        'write-down', 'negative', 'adverse', 'severe'
    }
    
    @staticmethod
    def score(text: str) -> float:
        """Score from -1 (negative) to +1 (positive)."""
        if not text:
            return 0.0
        
        words = text.lower().split()
        total = len(words)
        if total == 0:
            return 0.0
        
        pos_count = sum(1 for w in ToneConfidenceScorer.POSITIVE_WORDS if w in text.lower())
        neg_count = sum(1 for w in ToneConfidenceScorer.NEGATIVE_WORDS if w in text.lower())
        
        # Normalize by sentence count for fairness
        sentences = max(1, len(re.split(r'[.!?]+', text)))
        
        pos_score = pos_count / sentences
        neg_score = neg_count / sentences
        
        raw = (pos_score - neg_score) / max(1, pos_score + neg_score)
        return max(-1.0, min(1.0, raw * 2))  # Scale to [-1, 1]


class ForwardGuidanceScorer:
    """
    FGC: Measures clarity and specificity of forward-looking statements.
    """
    
    FORWARD_TRIGGERS = {
        'expect', 'anticipate', 'guidance', 'outlook', 'forecast',
        'pipeline', 'next quarter', 'fiscal year', 'looking ahead',
        'going forward', 'we project', 'we estimate', 'we see',
        'trajectory', 'runway', 'multi-year', 'long-term'
    }
    
    SPECIFICITY_INDICATORS = {
        'percent', 'dollars', 'billion', 'million', 'basis points',
        'range', 'approximately', 'at least', 'up to', 'between',
        'target', 'plan to', 'on track', 'committed to'
    }
    
    VAGUE_INDICATORS = {
        'may', 'might', 'could', 'possibly', 'potentially',
        'we believe', 'we think', 'uncertain', 'depending on',
        'subject to', 'if', 'assuming', 'hope to'
    }
    
    @staticmethod
    def score(text: str) -> float:
        """Score: specific forward guidance = positive, vague = negative."""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        fwd_count = sum(1 for w in ForwardGuidanceScorer.FORWARD_TRIGGERS if w in text_lower)
        spec_count = sum(1 for w in ForwardGuidanceScorer.SPECIFICITY_INDICATORS if w in text_lower)
        vague_count = sum(1 for w in ForwardGuidanceScorer.VAGUE_INDICATORS if w in text_lower)
        
        if fwd_count == 0:
            return 0.0  # No forward guidance at all = neutral
        
        specificity_ratio = spec_count / max(1, spec_count + vague_count)
        return max(-1.0, min(1.0, (specificity_ratio - 0.3) * 2.5))


class TopicAvoidanceScorer:
    """
    TAD: Detects when executives dodge analyst questions.
    Local version uses keyword overlap.
    """
    
    DODGE_PATTERNS = [
        r'(we|I) (don\'t|do not|can\'t|cannot) (comment|speculate|discuss)',
        r'that\'s (not something|nothing) (we|I) (can|will) (comment on|discuss)',
        r'I would (refer you|point you|direct you) to',
        r'as (we|I) (mentioned|said|discussed) (earlier|previously|before)',
        r'we (don\'t|do not) (break out|disclose|provide)',
        r'it\'s (too early|premature) to',
        r'(we|I) (prefer not to|won\'t) (comment|speculate)',
        r'that\'s (a|very) (good|great|interesting) question',
    ]
    
    @staticmethod
    def score(question_text: str, answer_text: str) -> float:
        """
        Score from 0 (no avoidance) to 1 (complete dodge).
        QA section text is analyzed for dodging patterns.
        """
        if not answer_text or not question_text:
            return 0.0
        
        answer_lower = answer_text.lower()
        
        # Count dodge patterns
        dodge_count = 0
        for pattern in TopicAvoidanceScorer.DODGE_PATTERNS:
            if re.search(pattern, answer_lower):
                dodge_count += 1
        
        # Keyword overlap between question and answer
        q_words = set(question_text.lower().split()) - {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'can', 'could', 'would', 'will', 'do', 'does', 'did', 'about', 'on', 'in', 'at', 'to', 'of', 'for', 'and', 'or', 'but'}
        a_words = set(answer_text.lower().split()) - {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'can', 'could', 'would', 'will', 'do', 'does', 'did', 'about', 'on', 'in', 'at', 'to', 'of', 'for', 'and', 'or', 'but', 'we', 'our', 'i', 'my', 'that', 'this', 'it', 'they', 'their', 'its'}
        
        if len(q_words) == 0:
            overlap_ratio = 0.5
        else:
            overlap = q_words & a_words
            overlap_ratio = len(overlap) / len(q_words)
        
        # High overlap = addressing the question. Low overlap = avoiding.
        avoidance_from_overlap = 1.0 - overlap_ratio
        
        # Combine dodge patterns + overlap
        raw_score = (dodge_count * 0.3) + (avoidance_from_overlap * 0.7)
        return max(0.0, min(1.0, raw_score))


class LinguisticHedgingScorer:
    """
    LHI: Measures hedging and uncertainty language.
    High score = high hedging = negative signal.
    """
    
    HEDGE_WORDS = {
        'uncertain': 3, 'volatility': 3, 'risk': 2, 'cautious': 2,
        'subject to': 3, 'depending on': 3, 'if': 1, 'assuming': 2,
        'approximately': 1, 'roughly': 1, 'about': 1, 'around': 1,
        'maybe': 2, 'perhaps': 2, 'possibly': 2, 'potentially': 1,
        'generally': 1, 'typically': 1, 'normally': 1, 'usually': 1,
        'believe': 2, 'think': 2, 'feel': 2, 'seems': 1,
        'appears': 1, 'suggests': 1, 'indicates': 1, 'likely': 1,
        'probably': 2, 'could': 1, 'might': 1, 'may': 1,
        'expects': 1, 'hopes': 2, 'aims': 1, 'intends': 1,
        'preliminary': 2, 'tentative': 2, 'estimated': 1, 'projected': 1,
        'guidance range': 1, 'wide range': 2, 'various': 1,
    }
    
    # Strong commitment words (reduce hedging score)
    COMMITMENT_WORDS = {
        'will': -1, 'committed': -2, 'guaranteed': -3, 'certain': -2,
        'definitively': -2, 'absolutely': -2, 'clearly': -1, 'confirmed': -2,
        'on track': -2, 'delivering': -1, 'executing': -1, 'achieved': -2,
    }
    
    @staticmethod
    def score(text: str) -> float:
        """
        Score from -1 (strong commitment) to +1 (high hedging).
        Inverted in ENS composer so high score = good.
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        words = text_lower.split()
        total_words = max(1, len(words))
        
        hedge_score = 0
        for phrase, weight in LinguisticHedgingScorer.HEDGE_WORDS.items():
            count = text_lower.count(phrase)
            hedge_score += count * weight
        
        for phrase, weight in LinguisticHedgingScorer.COMMITMENT_WORDS.items():
            count = text_lower.count(phrase)
            hedge_score += count * weight
        
        # Normalize per 100 words
        normalized = hedge_score / (total_words / 100)
        
        # Map to [-1, 1]
        # Typical range: -5 to +15 per 100 words
        return max(-1.0, min(1.0, normalized / 10.0))


def test_scorers():
    """Test all four scorers."""
    
    # Test TCS
    positive_text = "We had record revenue and exceptional growth. We are very confident about the future."
    negative_text = "This was a challenging quarter with significant headwinds. We are cautious going forward."
    
    tcs_pos = ToneConfidenceScorer.score(positive_text)
    tcs_neg = ToneConfidenceScorer.score(negative_text)
    assert tcs_pos > 0, f"TCS positive failed: {tcs_pos}"
    assert tcs_neg < 0, f"TCS negative failed: {tcs_neg}"
    print(f"TCS: positive={tcs_pos:.2f}, negative={tcs_neg:.2f} ✅")
    
    # Test FGC
    specific = "We expect revenue of $90 billion next quarter, up 5 percent. Our pipeline is strong."
    vague = "We might possibly see some growth maybe next year depending on conditions."
    
    fgc_spec = ForwardGuidanceScorer.score(specific)
    fgc_vague = ForwardGuidanceScorer.score(vague)
    assert fgc_spec > fgc_vague, f"FGC failed: spec={fgc_spec}, vague={fgc_vague}"
    print(f"FGC: specific={fgc_spec:.2f}, vague={fgc_vague:.2f} ✅")
    
    # Test TAD
    question = "What is your revenue guidance for next quarter?"
    direct_answer = "We expect revenue between $88 and $92 billion next quarter."
    dodge_answer = "That's a great question. As we mentioned earlier, we don't provide specific guidance. I would refer you to our SEC filings."
    
    tad_direct = TopicAvoidanceScorer.score(question, direct_answer)
    tad_dodge = TopicAvoidanceScorer.score(question, dodge_answer)
    assert tad_dodge > tad_direct, f"TAD failed: direct={tad_direct}, dodge={tad_dodge}"
    print(f"TAD: direct={tad_direct:.2f}, dodge={tad_dodge:.2f} ✅")
    
    # Test LHI
    confident = "We will deliver strong growth. We are committed to our targets. Revenue growth is confirmed."
    hedging = "We believe we might possibly see some growth. It could be approximately 5 percent. We are cautiously optimistic."
    
    lhi_confident = LinguisticHedgingScorer.score(confident)
    lhi_hedging = LinguisticHedgingScorer.score(hedging)
    assert lhi_hedging > lhi_confident, f"LHI failed: confident={lhi_confident}, hedging={lhi_hedging}"
    print(f"LHI: confident={lhi_confident:.2f}, hedging={lhi_hedging:.2f} ✅")
    
    print("\nAll scorer tests passed.")


if __name__ == "__main__":
    test_scorers()