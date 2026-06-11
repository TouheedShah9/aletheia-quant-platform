"""Project Aletheia - Central Configuration"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

UNIVERSE = {
    'USA': ['AAPL','MSFT','GOOGL','AMZN','META','JPM','BAC','GS','JNJ','PFE','XOM','CVX','HD','WMT','MCD'],
    'UK': ['SHEL.L','AZN.L','HSBA.L','ULVR.L','BP.L','GSK.L','RIO.L','DGE.L','BARC.L','LLOY.L'],
    'EU': ['SAP.DE','SIE.DE','ALV.DE','TTE.PA','ASML.AS','OR.PA','SAN.MC','BNP.PA'],
    'PAKISTAN': ['HBL','UBL','OGDC','PPL','ENGRO','LUCK','MCB','NBP','PSO','HUBC']
}

ALL_TICKERS = [{'ticker':t,'market':m} for m,ts in UNIVERSE.items() for t in ts]

DATA_START, DATA_END = '2019-01-01', '2024-12-31'
TRAIN_END, VAL_END, TEST_START = '2021-12-31', '2022-12-31', '2023-01-01'

# Risk Limits
EMBARGO_DAYS = 2
MAX_POSITION = 0.05
MAX_SECTOR_EXPOSURE = 0.25
MAX_MARKET_EXPOSURE = 1.0
DRAWDOWN_BREAKER = 0.07
POSITION_REDUCTION_ON_BREACH = 0.50

# Transaction Costs
COST_LARGE = 0.001
COST_MID = 0.002

# Market Regime
VIX_FEAR = 30
VIX_GREED = 20

# Model Names
FINBERT = 'ProsusAI/finbert'
BART = 'facebook/bart-large-mnli'
SENT_TF = 'all-MiniLM-L6-v2'

# Signal Weights
REGIME_WEIGHTS = {
    'risk_on': {'ens':0.5,'riv':0.25,'cmi':0.25},
    'risk_off': {'ens':0.3,'riv':0.5,'cmi':0.2},
    'transition': {'ens':0.4,'riv':0.35,'cmi':0.25}
}

ENS_DIM = {'tcs':0.35,'fgc':0.25,'tad':0.25,'lhi':0.15}
ENS_SEC = {'prepared':0.35,'qa':0.65}

# API Keys
FRED_KEY = os.getenv('FRED_API_KEY','')
EMAIL = os.getenv('YOUR_EMAIL','research@projectaletheia.dev')
SEC_UA = f'ProjectAletheia {EMAIL}'

# Rate Limits
RATE_EDGAR = 0.15
RATE_WAYBACK = 2.0
MAX_LOCAL_ROWS = 10000
BATCH_SIZE = 16
DRIVE = '/content/drive/MyDrive/aletheia_data/'
BENCH = {'USA':'^GSPC','UK':'^FTSE','EU':'^STOXX50E','PAKISTAN':'^KSE'}

DISCLAIMER = """
LEGAL: Project Aletheia is a research prototype. All signals are 
experimental. Not investment advice. Not validated for live trading.
"""