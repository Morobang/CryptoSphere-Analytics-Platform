# CryptoSphere Analytics Platform

A cryptocurrency analytics platform built to learn and apply data engineering and data science through a real, working system. Not a tutorial project — a system that collects real data, processes it through a proper pipeline, and surfaces insights about how coins behave.

## What this project does

1. **Collects** real-time cryptocurrency data from CoinMarketCap API
2. **Stores** it in a medallion architecture (Bronze → Silver → Gold) across CSV files and SQL Server
3. **Analyzes** coin behavior: volatility, trends, correlations, market regimes
4. **Models** coin behavior: anomaly detection, clustering, trend classification

## Current state

| Component | Status |
|---|---|
| API data collection | Working (notebook 01) |
| Bronze layer (CSV + SQL) | Working |
| Silver layer ETL | Schema + procedures ready, not automated |
| Gold layer ETL | Schema + procedures ready, not automated |
| Data preprocessor | Implemented (`04-ml-models/02-data-preprocessing/`) |
| Model training framework | Implemented (generic, not yet crypto-specific) |
| Model registry + prediction service | Implemented |
| EDA notebooks | Structure only — next to build |
| Pipeline automation | Not started |

## Project structure

```
CryptoSphere-Analytics-Platform/
├── 00-docs/                    # Documentation and learning roadmap
├── 01-data/                    # Data storage
│   ├── raw/                    # Bronze: raw CSV files
│   └── src/                    # Data collection Python modules
├── 02-notebooks/               # Jupyter notebooks by phase
│   ├── 01-data-acquisition/    # Phase 1: API collection (working)
│   ├── 02-data-cleaning/       # Phase 2: Quality checks
│   ├── 03-exploratory-analysis/# Phase 3: EDA (next to build)
│   └── 04-data-transformation/ # Phase 4: Feature engineering
├── 03-sql-processing/          # SQL Server medallion architecture
│   ├── 01-bronze-layer/        # Raw tables + insert procedures
│   ├── 02-silver-layer/        # Clean tables + ETL procedures
│   ├── 03-gold-layer/          # Analytics tables + aggregations
│   └── 04-automation/          # Full pipeline + monitoring
├── 04-ml-models/               # ML pipeline
│   ├── 02-data-preprocessing/  # Feature engineering + scaling
│   ├── 03-model-training/      # Multi-algorithm trainer
│   ├── 04-model-persistence/   # Model registry + versioning
│   └── 05-prediction-pipeline/ # Prediction service
└── 07-automation/              # Pipeline orchestration (planned)
```

## Setup

### Prerequisites
- Python 3.9+
- SQL Server with ODBC Driver 17 (for database layer)
- CoinMarketCap API key (free tier: 333 calls/day)

### Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the root:

```
COINMARKETCAP_API_KEY=your_key_here
SQL_SERVER=localhost
SQL_DATABASE=cryptosphere_analytics
```

### Database setup

Run the schema setup script once before collecting data:

```sql
-- In SSMS, run:
03-sql-processing/00-schema-setup/01-setup_all_layers.sql
```

### Run the collection pipeline

```bash
# Collect current top-10 crypto data (saves to CSV + SQL)
python main.py collect

# Run the full ETL (Bronze → Silver → Gold)
python main.py etl
```

Or use the notebook directly: `02-notebooks/01-data-acquisition/01-api_data_collection.ipynb`

## Data collected

The API returns 36 fields per coin per snapshot. Key columns:

| Field | Description |
|---|---|
| `symbol` | Ticker (BTC, ETH, etc.) |
| `quote_USD_price` | Current USD price |
| `quote_USD_market_cap` | Total market cap |
| `quote_USD_volume_24h` | 24-hour trading volume |
| `quote_USD_percent_change_1h/24h/7d/30d` | Price change over window |
| `quote_USD_market_cap_dominance` | % of total crypto market cap |
| `circulating_supply` | Coins in circulation |
| `last_updated` | Timestamp of the snapshot |

Full field definitions: [00-docs/02-data_dictionary.md](00-docs/02-data_dictionary.md)

## Learning roadmap

See [00-docs/09-complete_learning_roadmap.md](00-docs/09-complete_learning_roadmap.md) for the full phased breakdown of what to build, in what order, and what each phase teaches.

## Tech stack

| Layer | Tool |
|---|---|
| Data source | CoinMarketCap REST API |
| Storage | CSV files + SQL Server |
| ETL | Python + SQL Server stored procedures |
| Data processing | pandas, numpy, scipy |
| Machine learning | scikit-learn, XGBoost, LightGBM |
| Visualization | matplotlib, seaborn, plotly |
| Notebooks | Jupyter |
| Config | python-dotenv, PyYAML |

## Disclaimer

For educational and analysis purposes only. Not financial advice. Crypto price models have high uncertainty — the goal here is learning data engineering and data science, not building a trading system.
