import duckdb, hashlib
conn = duckdb.connect('aletheia.db')
conn.execute("DELETE FROM transcripts_metadata WHERE source = 'generated_sample'")
conn.execute("DELETE FROM ens_scores")

POSITIVE = '''Operator: Welcome to {company} quarterly earnings call.
CEO: We delivered exceptional results this quarter. Revenue of ${revenue}B exceeded our guidance by {beat}%. Our strategic investments in {theme} are paying off. We are seeing accelerating momentum across all business segments. Customer adoption is at record levels. Our competitive position has never been stronger.
CFO: Gross margins expanded to {margin}%, up {margin_improve} basis points year over year. Operating income grew {op_income}%. We generated {cash_flow}B in free cash flow. We are raising our full year guidance and announcing a {buyback}B share buyback program.
Q&A
Analyst: Can you talk about the growth trajectory?
CEO: We see sustained growth ahead. Our {theme} investments create a multi-year runway. We are gaining share in every market we serve.'''

NEUTRAL = '''Operator: Welcome to {company} quarterly earnings call.
CEO: This quarter results were in line with our expectations. Revenue of ${revenue}B reflects stable demand across our markets. We continue to execute on our strategic priorities while managing through a mixed macroeconomic environment. Some segments showed strength while others faced headwinds.
CFO: Gross margin was {margin}%, consistent with prior guidance. We maintained disciplined cost management. Operating cash flow was {cash_flow}B. We are maintaining our full year outlook. The macro environment remains uncertain.
Q&A
Analyst: What are the key risks?
CEO: Currency headwinds, inflation pressure, and regional demand variability. But our diversification helps us manage through.'''

NEGATIVE = '''Operator: Welcome to {company} quarterly earnings call.
CEO: This was a challenging quarter. Revenue of ${revenue}B came in below guidance. We faced headwinds from {problem}. Our {weak_segment} business underperformed significantly. We are taking decisive action to restructure.
CFO: Gross margins declined to {margin}% driven by unfavorable mix. We are implementing a {layoff_count} headcount reduction saving approximately ${savings}B annually. We are withdrawing our previous full year guidance.
Q&A
Analyst: How deep are the problems?
CEO: We underestimated the pace of change. Recovery will take 3 to 4 quarters. We are fundamentally restructuring that business.'''

COMPANIES = {
    'AAPL':{'company':'Apple','revenue':89.5,'beat':3,'theme':'AI','margin':45.2,'margin_improve':70,'op_income':5,'cash_flow':21.6,'buyback':27,'problem':'China slowdown','weak_segment':'iPhone','layoff_count':'5%','savings':2.0},
    'MSFT':{'company':'Microsoft','revenue':56.5,'beat':5,'theme':'cloud AI','margin':71.0,'margin_improve':120,'op_income':25,'cash_flow':19.7,'buyback':9.1,'problem':'enterprise slowdown','weak_segment':'Office','layoff_count':'10,000','savings':1.2},
    'GOOGL':{'company':'Alphabet','revenue':76.7,'beat':2,'theme':'GenAI','margin':57.0,'margin_improve':50,'op_income':15,'cash_flow':22.6,'buyback':15,'problem':'ad volatility','weak_segment':'YouTube','layoff_count':'12,000','savings':2.0},
    'AMZN':{'company':'Amazon','revenue':143.1,'beat':4,'theme':'AWS','margin':47.6,'margin_improve':200,'op_income':400,'cash_flow':21.4,'buyback':0,'problem':'retail pressure','weak_segment':'International','layoff_count':'9,000','savings':1.8},
    'META':{'company':'Meta','revenue':34.1,'beat':7,'theme':'AI ads','margin':81.8,'margin_improve':250,'op_income':40,'cash_flow':13.6,'buyback':20,'problem':'privacy regs','weak_segment':'Reality Labs','layoff_count':'21,000','savings':3.0},
    'JPM':{'company':'JPMorgan','revenue':39.9,'beat':6,'theme':'IB','margin':55.0,'margin_improve':80,'op_income':22,'cash_flow':15.2,'buyback':6,'problem':'credit losses','weak_segment':'Consumer','layoff_count':'2,000','savings':0.8},
    'BAC':{'company':'BofA','revenue':25.2,'beat':3,'theme':'digital','margin':52.0,'margin_improve':40,'op_income':10,'cash_flow':8.5,'buyback':3.5,'problem':'NIM','weak_segment':'Mortgage','layoff_count':'3,000','savings':0.6},
    'GS':{'company':'Goldman','revenue':11.8,'beat':2,'theme':'AM','margin':60.0,'margin_improve':30,'op_income':8,'cash_flow':4.2,'buyback':2.5,'problem':'deal decline','weak_segment':'IB','layoff_count':'3,500','savings':1.0},
    'JNJ':{'company':'J&J','revenue':21.4,'beat':2,'theme':'pharma','margin':69.0,'margin_improve':20,'op_income':6,'cash_flow':7.8,'buyback':5,'problem':'patent cliff','weak_segment':'Consumer','layoff_count':'1,500','savings':0.5},
    'PFE':{'company':'Pfizer','revenue':13.2,'beat':-15,'theme':'oncology','margin':55.0,'margin_improve':-300,'op_income':-40,'cash_flow':3.1,'buyback':0,'problem':'COVID cliff','weak_segment':'COVID','layoff_count':'5,000','savings':2.5},
    'XOM':{'company':'Exxon','revenue':90.8,'beat':5,'theme':'low carbon','margin':38.0,'margin_improve':100,'op_income':15,'cash_flow':16.0,'buyback':17.5,'problem':'oil vol','weak_segment':'Chemicals','layoff_count':'1,200','savings':1.5},
    'CVX':{'company':'Chevron','revenue':54.1,'beat':3,'theme':'Permian','margin':35.0,'margin_improve':60,'op_income':12,'cash_flow':9.8,'buyback':11.5,'problem':'refining','weak_segment':'Downstream','layoff_count':'800','savings':0.4},
    'HD':{'company':'Home Depot','revenue':37.7,'beat':-2,'theme':'supply chain','margin':33.8,'margin_improve':-50,'op_income':-4,'cash_flow':6.0,'buyback':2.0,'problem':'housing','weak_segment':'Big ticket','layoff_count':'1,000','savings':0.3},
    'WMT':{'company':'Walmart','revenue':160.8,'beat':4,'theme':'e-comm','margin':24.0,'margin_improve':40,'op_income':8,'cash_flow':14.0,'buyback':5.5,'problem':'shrink','weak_segment':'Intl','layoff_count':'2,500','savings':0.7},
    'MCD':{'company':'McDonalds','revenue':6.7,'beat':3,'theme':'digital','margin':57.0,'margin_improve':80,'op_income':12,'cash_flow':2.5,'buyback':1.5,'problem':'traffic','weak_segment':'US','layoff_count':'500','savings':0.2},
}

count = 0
for ticker, info in COMPANIES.items():
    for sentiment, template in [('positive',POSITIVE),('neutral',NEUTRAL),('negative',NEGATIVE)]:
        text = template.format(**info)
        wc = len(text.split())
        checksum = hashlib.sha256(text.encode()).hexdigest()
        tid = f'gen_{ticker}_{sentiment}'
        
        conn.execute('''INSERT OR REPLACE INTO transcripts_metadata
            (id, ticker, company_name, market, event_date, ingestion_timestamp, source, word_count, has_qa_section, checksum, full_text)
            VALUES (?,?,?,'USA','2024-01-15',CURRENT_TIMESTAMP,'generated_sample',?,TRUE,?,?)''',
            [tid, ticker, ticker, wc, checksum, text])
        count += 1

conn.close()
print(f'Stored {count} transcripts with full text')