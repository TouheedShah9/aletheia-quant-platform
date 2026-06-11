"""CMI Web Monitor - Detects website changes"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class WebMonitor:
    @staticmethod
    def calculate_change(old_text: str, new_text: str) -> float:
        if not old_text:
            return 0.0
        old_words = set(old_text.lower().split())
        new_words = set(new_text.lower().split())
        if not old_words:
            return 0.0
        intersection = old_words & new_words
        union = old_words | new_words
        similarity = len(intersection) / len(union) if union else 1.0
        return round(1.0 - similarity, 3)

if __name__ == "__main__":
    old = "Welcome to our company. We provide cloud solutions."
    new = "Welcome to our company. We now provide AI and cloud solutions with new pricing."
    change = WebMonitor.calculate_change(old, new)
    print(f"Change magnitude: {change:.2f}")