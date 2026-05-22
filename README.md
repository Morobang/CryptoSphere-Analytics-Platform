# CryptoSphere Analytics Platform

A cryptocurrency analytics platform built from scratch to learn data engineering and data science.

## What this builds

```
CoinMarketCap API
      │
      ▼
  Bronze (raw)  →  Silver (clean)  →  Gold (analytics-ready)
      │
      ▼
  CSV files  +  SQL Server
      │
      ▼
  EDA notebooks  →  ML models
```

## Build order

1. **Get the API key** — coinmarketcap.com/api (free)
2. **Make the first API call** — understand the raw JSON
3. **Store Bronze data** — CSV, append mode, one row per coin per snapshot
4. **Set up SQL Server** — Bronze tables + insert stored procedures
5. **Build Silver ETL** — clean and validate Bronze into Silver
6. **Build Gold ETL** — aggregate Silver into analysis-ready Gold
7. **EDA notebooks** — understand how coins actually behave
8. **Feature engineering** — technical indicators from raw price data
9. **ML models** — anomaly detection, clustering, trend classification

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your API key
```

## Project structure

```
01-data/
  bronze/   ← raw CSV files from API
  silver/   ← cleaned CSV files
  gold/     ← aggregated, analytics-ready CSV files

02-notebooks/
  01-data-acquisition/   ← Step 1: API calls, raw data
  02-eda/                ← Step 2: Understanding coin behavior
  03-ml/                 ← Step 3: Models

03-pipeline/
  collect.py    ← data collection script
  etl.py        ← Bronze → Silver → Gold

04-analysis/
  indicators.py ← technical indicators (RSI, MACD, etc.)

05-sql/
  01-bronze/    ← table schemas + insert procedures
  02-silver/    ← cleaning ETL
  03-gold/      ← aggregation ETL
```
