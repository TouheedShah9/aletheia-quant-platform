"""Market Regime Detector - VIX + trend based"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

def detect(vix=20, above_ma=True):
    if vix > config.VIX_FEAR:
        return 'risk_off'
    elif vix < config.VIX_GREED and above_ma:
        return 'risk_on'
    return 'transition'

if __name__ == "__main__":
    print(f"VIX=15, above MA: {detect(15, True)}")
    print(f"VIX=35, below MA: {detect(35, False)}")
    print(f"VIX=25: {detect(25)}")