# Project Charter: CryptoSphere Analytics Platform

## Purpose

Build a system that answers: **"How do cryptocurrency coins behave, and can that behavior be learned by a model?"**

This is not a dashboard project or a price predictor built on someone else's tutorial. It's a full data engineering + data science system, built from scratch, where every layer has a reason for existing.

## Problem statement

Raw cryptocurrency market data from APIs is noisy, snapshot-based, and context-free. There's no structure, no historical shape, no signal — just a flat record of prices and percentages at a point in time.

To understand coin behavior you need:
1. A pipeline that collects data reliably over time and stores it in a queryable form
2. A processing layer that computes derived metrics (volatility, momentum, market dominance trends)
3. Analysis that characterizes each coin's behavior pattern (volatile/stable, correlated/independent, trending/ranging)
4. Models that can detect anomalies, cluster coins by behavior, and classify whether a pattern is forming

## Goals

| Goal | What it means concretely |
|---|---|
| Learn data engineering | Build a real ETL pipeline: API → Bronze → Silver → Gold |
| Learn SQL for analytics | Write and understand stored procedures, views, and aggregations |
| Learn time series EDA | Compute rolling stats, detect regimes, identify correlations |
| Learn feature engineering | Turn raw prices into signals: RSI, MACD, Bollinger Bands, OBV |
| Learn ML evaluation | Train, tune, and honestly evaluate models on time-series data |
| Build a portfolio piece | Something that runs, has real data, and demonstrates real skill |

## Scope

### In scope
- Top 10 cryptocurrencies by market cap (BTC, ETH, USDT, BNB, XRP, SOL, USDC, TRX, DOGE, ADA)
- CoinMarketCap API, free tier (333 calls/day)
- SQL Server medallion architecture (Bronze → Silver → Gold)
- CSV file storage as a parallel backup
- Coin behavior analysis: volatility, correlation, market regime detection
- ML tasks: anomaly detection, coin clustering, trend classification
- Visualization via Plotly/matplotlib in notebooks

### Out of scope (for now)
- Live trading or order execution
- Sentiment analysis or news feeds
- Cloud deployment or containerization
- Real-time streaming (< 5 minute updates)
- More than 10 coins

## Success criteria

The project is successful when:
- [ ] A scheduled collection job runs without manual intervention and builds up historical data
- [ ] Bronze → Silver → Gold ETL runs end-to-end without manual SQL execution
- [ ] At least 2 weeks of historical snapshots are stored
- [ ] An EDA notebook characterizes each coin: volatility profile, dominant trends, correlation with BTC
- [ ] At least one ML model is trained, evaluated, and interpretable — not just "accuracy: 0.7"
- [ ] You can explain every component you built: why it's designed that way, what it's doing

## Tech stack decisions

| Decision | Choice | Reason |
|---|---|---|
| Database | SQL Server | Already set up, real enterprise tool, teaches stored procedures |
| API | CoinMarketCap | Free tier, well-documented, enough data to build on |
| Language | Python | pandas + scikit-learn ecosystem is the right tool for this domain |
| Notebooks | Jupyter | Right for exploration; Python scripts for production logic |
| ML | scikit-learn + XGBoost | Interpretable, well-documented, industry standard |
| Visualization | Plotly + matplotlib | Plotly for interactive exploration, matplotlib for static publication |

## Project phases

### Phase 1 — Data Engineering (foundation)
Build the pipeline that feeds everything else. Without reliable, clean, well-structured data, the analysis and ML are worthless.

**Deliverables:** Working collection script, automated Bronze→Silver→Gold ETL, 2+ weeks of data

### Phase 2 — Coin Behavior Analysis
With data flowing, understand it. This is where you learn what the data actually says before trying to model it.

**Deliverables:** EDA notebooks covering volatility, correlation, regime detection, technical indicators

### Phase 3 — Data Science and ML
Apply models to the patterns found in Phase 2. The models should answer questions discovered in EDA, not random ones.

**Deliverables:** Anomaly detector, coin behavior clustering, trend classifier with proper backtesting

## Constraints

- Free API tier: 333 calls/day, ~10 coins per call = collect every 4 hours comfortably
- SQL Server runs locally — not cloud, not containerized yet
- No paid data sources
- Solo project — scope must stay manageable
