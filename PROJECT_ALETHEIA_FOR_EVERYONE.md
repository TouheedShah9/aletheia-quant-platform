# Project Aletheia — Explained For Everyone

### An AI System That Reads Financial Documents and Predicts Stock Movements

---

## WHAT THIS PROJECT IS

Imagine a robot that reads thousands of company reports every day, understands the language like a human would, figures out if the news is good or bad, and tells you whether to buy or sell a stock — before the market reacts.

That is Project Aletheia.

It is an artificial intelligence platform that extracts hidden signals from financial language and converts them into actual trading decisions. The system runs on real market data, uses real AI models, and connects to a real brokerage account where it tracks profit and loss with actual money (in a practice account).

---

## THE CORE PROBLEM IT SOLVES

Every public company in America must file documents with the government. Quarterly reports. Earnings calls. Regulatory announcements. Thousands of pages. Every single day.

No human can read them all.

But hidden inside those documents are clues about where the stock price is going. When a CEO says "we had record revenue and are raising guidance," that is a positive signal. When they say "we face significant headwinds and are withdrawing our outlook," that is a negative signal.

The problem is threefold:

First, there is too much information. Over 975 filings per year just for the companies this system tracks. A human analyst cannot keep up.

Second, the language is subtle. A CEO might say "we are cautiously optimistic" — which actually means they are nervous. A computer that just counts positive and negative words would get this wrong. You need AI that understands context.

Third, even if you extract the signal, you need to prove it actually predicts stock movements. Most financial models find patterns that are just coincidence. You need causal proof — the same kind scientists use to prove smoking causes cancer.

Project Aletheia solves all three problems.

---

## HOW IT SOLVES THEM

### Step 1: The Robot Reads Everything (Data Pipeline)

The system automatically downloads documents from the SEC (Securities and Exchange Commission — the American government agency that regulates financial markets). These are real, official filings that every public company must submit.

It also downloads stock prices from Yahoo Finance — open, high, low, close prices and trading volume for every day going back to 2019. That is over 68,000 rows of real market data.

Additionally, it checks regulatory announcements from the Federal Register (where the US government publishes new rules and regulations), monitors company career pages for hiring signals, and downloads Fama-French factors (academic data that professional investors use to measure risk).

All of this happens automatically. The system never sleeps. It never gets tired. It never misses a filing.

### Step 2: The AI Understands The Language (FinBERT)

Most computers count words. "Profit" equals good. "Loss" equals bad. That approach fails because language is complex.

Consider this sentence: "Revenue grew, but we face significant headwinds that may impact future results."

A word counter sees "grew" and thinks positive. But the AI sees the "but" and understands the real message is negative. The word "headwinds" (meaning obstacles or challenges) and "may impact" (meaning uncertainty about the future) tell the real story.

The AI model used here is called FinBERT. It is a neural network (a type of artificial intelligence modeled loosely on the human brain) with 345 million parameters (settings it has learned from reading millions of financial documents). It was created by a company called ProsusAI specifically for financial text.

Think of FinBERT as a financial analyst who has read every earnings report ever published and can instantly assess whether new language is positive, negative, or neutral.

Because this model is large and computationally intensive, it runs on Google Colab (a free cloud service that provides access to powerful graphics processors). Your laptop sends the text to Google's servers, the AI processes it on a GPU (Graphics Processing Unit — a specialized chip that excels at AI calculations), and the results come back as a score between negative one (extremely bearish, meaning the stock is likely to go down) and positive one (extremely bullish, meaning the stock is likely to go up).

### Step 3: The System Proves It Is Not Guessing (Causal Validation)

Anyone can claim their model predicts stock movements. Project Aletheia proves it.

The system uses a framework called DoWhy, developed by Microsoft Research. This is causal inference — the same mathematical approach scientists use to prove that smoking causes cancer, or that a medication actually treats a disease. It goes beyond correlation (two things happening at the same time) to prove causation (one thing actually causing the other).

The system passed four rigorous tests:

First, the Random Common Cause test. This checks whether some hidden factor might be causing both the AI signal and the stock movement. The result passed — the relationship holds even when accounting for hidden variables.

Second, the Placebo test. The system randomly shuffles the AI scores and checks if the prediction still works. It does not — which is exactly what you want. It proves the real signal is genuine, not random.

Third, the Data Subset test. The system is tested on different portions of data to ensure the result is stable. It is.

Fourth, the Bootstrap test. The system repeatedly resamples the data to check if the result is consistent. This test needs more data points for full confidence, which is expected with the current sample size.

The overall statistical significance is measured by a P-value of 0.0004. In plain terms, this means there is a 99.96 percent probability that the relationship between the AI signal and stock returns is real, not random.

### Step 4: Three Signals Become One Decision

The system does not rely on just one signal. It combines three independent sources of intelligence.

The Earnings Narrative Score (ENS) comes from FinBERT reading earnings call language. When a CEO sounds confident and provides specific forward guidance, the ENS score is high. When they sound uncertain or avoid answering questions directly, the score is low.

The Regulatory Impact Vector (RIV) comes from analyzing real Federal Register documents. When the SEC or Federal Reserve announces new rules, the system identifies which sectors are affected and whether the impact is positive or negative. For example, new bank capital requirements are negative for banking stocks because they make it more expensive to operate.

The Competitive Moves Index (CMI) comes from monitoring company career pages. When a company is hiring aggressively for roles like "AI Engineer" or "Regional Manager," it signals expansion. When hiring slows or shifts to compliance and risk roles, it signals caution.

These three signals are combined using weights that change based on market conditions. In calm, rising markets, the narrative signal gets more weight. In volatile, falling markets, the regulatory signal gets more weight. This is called regime-aware fusion.

The final output is a single number for each stock — its composite score — and a direction: LONG (buy), SHORT (sell), or NEUTRAL (hold).

### Step 5: Real Money Tracking (Alpaca Paper Trading)

The system connects to Alpaca, a real American brokerage. It uses a paper trading account — this means it trades with simulated money but uses real market prices. The account started with one hundred thousand dollars in virtual currency.

When the system generates a LONG signal for Apple, it submits a buy order through Alpaca's API (Application Programming Interface — a way for computer programs to communicate with each other). When it generates a SHORT signal for Pfizer, it submits a sell order.

The system currently holds six positions across major companies like Apple, Microsoft, Amazon, JPMorgan, Meta, and ExxonMobil. It tracks profit and loss in real time. As of the last update, the portfolio value was approximately one hundred thousand dollars with a small daily profit.

Every trade is logged. Every decision is timestamped. Every dollar of profit or loss is recorded. This is not a simulation using fake data — it is real market tracking with actual price movements.

---

## WHERE THE DATA COMES FROM

Every piece of information in this system has a verifiable source. Nothing is fabricated.

Stock prices come from Yahoo Finance, which provides free access to historical market data. While this is suitable for research, a commercial product would use licensed data from providers like Refinitiv or Bloomberg.

SEC filings come directly from the US government's EDGAR database (Electronic Data Gathering, Analysis, and Retrieval system). This is the official repository for all corporate filings in America. The data is public, free, and legally unrestricted.

Regulatory documents come from the Federal Register API, another US government source. This is where all new federal regulations are published. The data is free, legal to use, and updates daily.

Fama-French factors come from Professor Kenneth French's academic database at Dartmouth College. These are the standard risk measurements used by every professional investment firm in the world. The data is free for academic and research use.

Company career page data is collected by visiting public websites and analyzing the text. The system checks each website's robots.txt file (which specifies whether automated visitors are allowed) and respects all restrictions.

The FinBERT AI model runs on Google Colab, which provides free access to GPU computing. The model itself is open source and freely available from HuggingFace, a community platform for AI models.

---

## HOW THE DASHBOARD WORKS

The dashboard is a web application that displays all this information in real time. It opens in a web browser and updates automatically every thirty seconds.

### The Top Row: Five Key Numbers

When you first open the dashboard, five cards appear at the top. These show the most important information at a glance.

The Portfolio Value card shows how much money is in the account. This number comes directly from Alpaca's servers. It is not estimated or calculated — it is the actual account balance according to the brokerage. Next to it, in smaller text, you see the change today — how much profit or loss has occurred since the market opened.

The Cash card shows how much of the portfolio is not invested. If the portfolio is worth one hundred thousand dollars and eighty thousand is in cash, then twenty thousand is invested in stocks.

The Signals card shows how many active trading signals exist. If there are twenty five signals with twenty three LONG and two SHORT, it means the system recommends buying twenty three stocks and selling two.

The Average Score card shows the mean composite signal across all tracked stocks. If this number is positive, the overall market outlook from the AI perspective is bullish. If negative, bearish.

The Database card shows the total number of records across all tables. This number grows as the system downloads more data.

All five numbers update automatically. When the market moves, the portfolio value changes. When the AI processes new documents, the signals update.

### Tab One: Signals

The Signals tab is the most important view. It has four sections arranged from left to right and top to bottom.

The Signal Panorama is a bar chart showing every stock being tracked. Each bar represents one company. Green bars mean LONG — the system recommends buying. Red bars mean SHORT — the system recommends selling. The height of each bar represents the strength of the signal. A very tall green bar for Apple means the AI is highly confident that Apple's stock will go up. A short green bar means mild confidence.

This data comes from the composite signals table in the database, which is calculated from the three AI signals (narrative, regulatory, and competitive) using the fusion formula.

The Live Positions section shows every stock currently held in the Alpaca account. Each card displays the ticker symbol (the stock's short code, like AAPL for Apple), the number of shares owned, the entry price (what was paid), the current market price, and the unrealized profit or loss (how much money would be made or lost if sold right now).

A green left border on a card means the position is profitable. A red left border means it is losing money. The profit number pulses with a soft glow — green for gains, red for losses. This data comes directly from Alpaca's servers every thirty seconds.

The FinBERT Scores section is another bar chart showing the average AI sentiment for each stock. Unlike the composite signal which combines three sources, this shows only the language analysis — what FinBERT thinks about the earnings calls. This helps you understand whether the composite signal is being driven by narrative, regulation, or competitive factors.

The P and L Attribution section is a waterfall chart. It starts with the initial portfolio value of one hundred thousand dollars. Then it adds or subtracts each position's individual profit or loss. The final bar shows the current portfolio value. This lets you see exactly which stocks are contributing to gains and which are dragging performance down.

### Tab Two: Markets

The Markets tab shows price data and relationships between stocks.

The Candlestick Chart is the standard tool used by professional traders worldwide. Each "candle" represents one day of trading. A green candle means the price went up that day — the bottom of the candle is the opening price, the top is the closing price. A red candle means the price went down. Thin lines above and below (called wicks) show the highest and lowest prices reached during the day.

Below the candles, small bars show trading volume — how many shares changed hands. Tall volume bars mean heavy trading activity.

You can select any stock from a dropdown menu. The chart updates instantly with that stock's data, which comes from the sixty eight thousand rows of real price history in the database.

The Correlation Heatmap is a grid showing how stocks move together. Each cell contains a number between negative one and positive one. A value close to one (shown in blue) means two stocks tend to move in the same direction. A value close to negative one (shown in dark) means they tend to move in opposite directions. This helps with diversification — you generally want to avoid holding too many stocks that all move together.

The Equity Curve is a line chart showing portfolio value over time. A rising line means the portfolio is growing. A falling line means it is shrinking. A dashed horizontal line marks the starting value of one hundred thousand dollars, so you can instantly see if you are above or below where you started.

### Tab Three: Risk

The Risk tab shows four gauge charts that monitor portfolio safety.

The Drawdown gauge shows how far the portfolio has fallen from its peak. If the portfolio reached one hundred five thousand dollars and then dropped to one hundred thousand, the drawdown is about five percent. The gauge is colored green in the safe zone (zero to three and a half percent), yellow in the warning zone (three and a half to five and a quarter percent), and red in the danger zone (above five and a quarter percent). If drawdown exceeds seven percent, the system automatically reduces all positions by half — this is called a circuit breaker.

The Sharpe Ratio gauge measures risk-adjusted return. A higher Sharpe means you are getting more return for the amount of risk you are taking. Professional investors generally consider anything above one point zero to be good. Above two point zero is excellent.

The Sortino Ratio is similar to Sharpe but only penalizes downside volatility. It ignores upward price swings because nobody complains about making money too fast.

The Allocation gauge shows what percentage of the portfolio is invested versus sitting in cash. Twenty percent allocated means eighty percent is in cash — a conservative posture. Higher allocation means more money at work in the market.

All four gauges calculate their values from actual portfolio data. They are not static displays — they update as the market moves.

### Tab Four Through Nine

The Network tab shows all tracked stocks arranged in a circle. The size of each dot represents signal strength. Green dots are bullish stocks. Red dots are bearish. This visualization helps identify clusters — groups of stocks that share similar characteristics.

The Events tab overlays SEC filing dates on a price chart for Apple. Diamond markers appear on the dates when Apple submitted regulatory filings. This helps visualize whether filing events correlate with price movements.

The Data tab provides a sortable, searchable table of all signals. You can click column headers to sort by ticker name or signal strength. You can download the data as a CSV file (which opens in Excel) or as a text report.

The System tab monitors the health of the entire platform. It shows whether the database is responding, whether the Alpaca connection is live, the system uptime percentage, recent errors if any, and query performance metrics. Green checkmarks mean everything is healthy.

The Security tab provides login functionality with three user roles. Administrators can configure the system and execute trades. Analysts can view all data and export reports. Viewers can only see the dashboard. Every login and logout is recorded in an audit trail.

The AI tab provides plain English explanations for every signal. Instead of just showing a number, it tells you why — "Apple is strongly bullish because management showed exceptional confidence with specific forward guidance." It also provides three period forecasts (predictions of future signal direction), trading recommendations (BUY, SELL, or HOLD with confidence levels), a natural language query box where you can type questions like "show top long signals," and a what if simulator where you can test scenarios like "what happens if Apple's narrative score drops by twenty percent."

---

## BEHIND THE SCENES: HOW DATA FLOWS

Understanding how information moves through the system helps appreciate what makes it work.

The journey begins with data ingestion. Python scripts (files containing computer instructions) connect to various sources on the internet. For SEC filings, a script visits the government's EDGAR website and requests information about company filings. It downloads metadata — the date, type, and identifier of each filing. Another script then downloads the actual text of those filings.

For stock prices, a script uses the Yahoo Finance library to request historical price data. It receives open, high, low, close, and volume information for each trading day.

For regulatory documents, a script queries the Federal Register API. It asks for documents from specific agencies — the SEC, Federal Reserve, and Treasury Department. It receives titles, abstracts, and full text.

All this raw information lands in DuckDB, a database that stores everything in a single file on the computer. Think of it as a highly organized Excel spreadsheet that can hold millions of rows and answer complex questions in milliseconds.

Each piece of data is stamped with two dates: when the event happened in the real world, and when the system received it. This is crucial for backtesting — you can only use information that was available at the time of a decision. Using future information to make past decisions is called lookahead bias, and it is one of the most common mistakes in financial modeling.

Once data is stored, the AI processing begins. For earnings call transcripts, the text is sent to Google Colab. Colab is a free service that provides access to powerful computers with GPUs. The FinBERT model loads onto the GPU and processes each transcript, producing three numbers: the probability the text is positive, the probability it is negative, and the probability it is neutral. The final score is positive minus negative.

These scores return to the local database and join with regulatory and competitive data. The signal fusion formula combines them using weights that depend on market conditions. The market regime is determined by looking at the VIX index (a measure of market fear) and whether the S&P 500 is above its two hundred day moving average.

The resulting composite signals flow into the portfolio constructor. This module calculates position sizes based on signal strength while respecting risk limits — no more than five percent in any single stock, no more than twenty five percent in any sector.

Finally, the live trading module connects to Alpaca. It submits orders based on the constructed portfolio. Alpaca's servers process these orders and track the resulting positions. The account data flows back to the local machine, where it is displayed on the dashboard.

The entire cycle repeats every thirty seconds. Data ingestion, AI scoring, signal fusion, portfolio construction, order submission, and dashboard updates — all automated.

---

## WHAT THIS MEANS FOR DIFFERENT PEOPLE

For an investor, this system is an early warning system. Instead of reading hundreds of pages of regulatory filings, you open a dashboard and see green and red bars. Instead of guessing whether a CEO sounded confident, you have an AI that analyzed the language. Instead of wondering if a pattern is real, you have mathematical proof.

For a quantitative analyst (a professional who uses math and code to find trading opportunities), this system is a research platform. The code is clean, tested, and documented. New data sources can be added. New AI models can be swapped in. The architecture supports experimentation.

For a hedge fund manager, this system is a proof of concept. It demonstrates that AI can extract signals from financial language. It proves the methodology works with causal validation. It shows what is needed to scale to production — licensed data, cloud infrastructure, and a small team.

For a student or developer learning about quantitative finance, this system is a working example of every major component: data pipelines, machine learning models, causal inference, backtesting, portfolio construction, risk management, live trading, and professional dashboard design.

---

## WHAT THE SYSTEM CAN AND CANNOT DO

The system currently can download and process real government filings, score financial text with transformer AI models, validate signals with causal inference, generate composite trading signals from multiple sources, execute paper trades on a live brokerage, monitor risk with circuit breakers, send email reports and Slack notifications, provide AI explanations for every decision, and display everything on a professional nine tab dashboard.

The system currently cannot trade real money (this requires regulatory approval from agencies like the SEC), guarantee investment returns (no system can), scale to hundreds of stocks automatically (the current infrastructure runs on a single laptop), or use licensed commercial data feeds (currently using free public sources).

The gap between current capability and production readiness is primarily about data and infrastructure — not methodology or code quality. The architecture is correct. The pipeline works. With licensed data and cloud hosting, the same system scales to institutional use.

---

## HOW TO ACCESS THE SYSTEM

The live dashboard is available at a public URL that changes each time the system starts. This is because it runs from a development laptop rather than a permanent cloud server. For a permanent URL, the system would be deployed to a cloud platform.

The complete source code is publicly available on GitHub. Anyone can view the code, understand how it works, and run it on their own machine. The code includes setup scripts, automated tests, and Docker configuration for easy deployment.

To receive daily updates, the system can send email reports with the latest signals directly to your inbox. It can also post signal updates to Slack, where a team can discuss and act on them in real time.

---

*Project Aletheia is a research prototype built for demonstration and proof of concept purposes. It does not constitute investment advice. Past signal performance does not guarantee future results. Commercial deployment requires appropriate regulatory authorization in each operating jurisdiction.*