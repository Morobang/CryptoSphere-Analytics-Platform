# Learning Roadmap

Three phases. Each one builds on the last. Each one teaches you something you can explain in an interview or apply in a job.

---

## Phase 1: Data Engineering Foundation

**Goal:** A pipeline that reliably collects data, stores it correctly, and moves it through Bronze → Silver → Gold without you touching it manually.

**You already have:** API collection working in the notebook, Bronze layer SQL schema and stored procedures, 40 rows of real data.

**What to build next:**

### 1.1 — Automate the collection script

The notebook works. Now extract that logic into `01-data/src/data_collection_manager.py` so it can be called from `main.py` and scheduled.

Key concepts:
- Separating exploration code (notebook) from production code (module)
- Idempotency: running the same collection twice shouldn't corrupt data
- Structured logging instead of print statements

Deliverable: `python main.py collect` works from the terminal.

### 1.2 — Run the Silver ETL

The Silver layer schema and stored procedures already exist at `03-sql-processing/02-silver-layer/`. Read them, understand what they do, then call them.

Key concepts:
- What "clean" data means: correct types, no nulls in critical fields, deduplication
- ETL vs ELT: the Silver procedure does transformation inside SQL (ELT)
- Data lineage: every silver record traces back to a bronze batch_id

Deliverable: `python main.py etl` executes Bronze → Silver → Gold.

### 1.3 — Schedule collection

Use `APScheduler` or Windows Task Scheduler to run collection every 4 hours. The goal: 2 weeks of data accumulating without manual runs.

Key concepts:
- Cron expressions
- What happens when a scheduled job fails silently
- Logging to a file so you can audit past runs

Deliverable: Collection runs on schedule, log file grows, data grows.

### 1.4 — Data quality checks

Before Silver ETL runs, validate that the Bronze data is sane. If something is wrong, log it and skip that batch rather than propagating bad data.

Key concepts:
- Schema validation (do all expected columns exist?)
- Range checks (price > 0, market_cap > 0)
- Freshness checks (is the timestamp recent?)
- Failing loudly vs failing silently

Deliverable: `05-data-validation/01-schema_validation/data_quality_validator.py` implemented and called in the ETL.

**Phase 1 complete when:**
- 2+ weeks of data in Bronze and Silver
- ETL runs end-to-end without manual SQL
- A log file shows every run's outcome

---

## Phase 2: Coin Behavior Analysis

**Goal:** Understand what the data is actually saying. Before you model anything, you need to know the data's shape, patterns, and quirks.

**Prerequisites:** At least 2 weeks of Silver/Gold data. You cannot do meaningful time series EDA on 40 rows.

**Work in:** `02-notebooks/03-exploratory-analysis/`

### 2.1 — Market overview and trend detection

`01-market_trend_analysis.ipynb`

Questions to answer:
- What does BTC price look like over the collection window?
- Which coins have been trending up/down/sideways?
- How do the percentage changes (1h, 24h, 7d) distribute? Are they normal?
- What is market cap dominance doing over time?

Key concepts:
- Rolling means and standard deviations (pandas `rolling()`)
- Trend vs noise: how to tell signal from randomness in short windows
- Market cap dominance as a sentiment proxy

### 2.2 — Volatility and risk profiling

`03-statistical_profiling.ipynb`

Questions to answer:
- Which coins are most/least volatile?
- Does volatility cluster? (GARCH intuition — volatile periods follow volatile periods)
- What's the relationship between volume and price movement?
- How does a coin's volatility compare to its market cap rank?

Key concepts:
- Realized volatility: rolling standard deviation of log returns
- Log returns vs percentage returns and why log returns are preferred
- Annualizing volatility
- Volume-price divergence as a signal

### 2.3 — Correlation analysis

`02-correlation_analysis.ipynb`

Questions to answer:
- How correlated are altcoins with BTC?
- Are there coins that move independently? When?
- Does correlation change in high-volatility vs low-volatility regimes?
- What's the correlation matrix look like across all 10 coins?

Key concepts:
- Pearson vs Spearman correlation and when each applies
- Rolling correlation windows (correlation is not static)
- Why high correlation between assets matters for diversification (and for feature engineering)

### 2.4 — Technical indicators

`04-visualization_dashboard.ipynb` + add to `02-data-transformation/03-derived_metrics.ipynb`

Build these indicators as computed columns in Gold or as a Python module:

| Indicator | What it measures | Window |
|---|---|---|
| SMA / EMA | Trend direction | 7, 14, 30 snapshots |
| RSI (0-100) | Overbought / oversold momentum | 14 |
| Bollinger Bands | Volatility envelope around price | 20, 2 std dev |
| MACD | Momentum: fast EMA minus slow EMA | 12/26/9 |
| ATR | Average true range — raw volatility | 14 |
| OBV | On-balance volume — volume confirms price | running total |

Key concepts:
- Why indicators are derived from price but aren't the same as price
- Look-ahead bias: indicators must only use data available at the time of the signal
- The difference between a feature and a label in a time series context

### 2.5 — Market regime detection

Questions to answer:
- Can you label each time window as "bull / bear / sideways" for a given coin?
- Does the overall market have regimes that all coins follow?
- What features best distinguish regimes?

Key concepts:
- Unsupervised regime detection with HMM or k-means on rolling features
- How regime labels will become training targets for Phase 3 models

**Phase 2 complete when:**
- You can describe each of the 10 coins' behavior in one paragraph backed by charts
- You have a set of computed features (indicators + rolling stats) stored in Gold
- You have a hypothesis for at least one ML task worth doing in Phase 3

---

## Phase 3: Data Science and Machine Learning

**Goal:** Train models that answer specific questions discovered in Phase 2. Not "predict price" (too hard, too unreliable) — questions like "is this price movement anomalous?" or "which behavioral group does this coin belong to?"

**Work in:** `04-ml-models/` notebooks and scripts

### 3.1 — Anomaly detection

**Question:** Is the current price behavior unusual given this coin's history?

Method: Isolation Forest or Z-score on rolling feature vectors (price change + volume + RSI). Flag samples that are far from the normal distribution.

Key concepts:
- Unsupervised vs supervised — no labels needed here
- What "anomaly" means in time series vs tabular data
- False positive rate: anomaly detectors are only useful if they don't fire constantly

Deliverable: A function `is_anomalous(snapshot, coin_history) -> bool` with a confidence score.

### 3.2 — Coin behavior clustering

**Question:** Do the 10 coins cluster into behavioral groups? What characterizes each group?

Method: K-means or hierarchical clustering on feature vectors: [realized volatility, BTC correlation, average volume trend, RSI distribution, 30d return].

Key concepts:
- Feature scaling before clustering (k-means is distance-based)
- Choosing k: elbow method + silhouette score
- Interpreting clusters: what makes cluster A different from cluster B?
- How cluster membership changes over time (rolling window clustering)

Deliverable: Cluster assignments for each coin with a characterization of each cluster.

### 3.3 — Trend direction classification

**Question:** Given the last N snapshots for a coin, is it more likely trending up, down, or sideways in the next period?

Method: Random Forest or XGBoost on a feature window → predict direction class. Evaluate with a proper walk-forward validation, not a random train/test split.

Key concepts:
- Walk-forward validation: why random splits leak future data in time series
- Class imbalance: markets might be sideways 60% of the time
- Feature importance: which indicators matter most?
- Calibration: predicted probability of "up" should mean it goes up that % of the time

Deliverable: A trained classifier, evaluated with a confusion matrix and walk-forward accuracy, with a feature importance plot.

### 3.4 — Model evaluation and honest reporting

**Question:** Are my models actually learning something, or just memorizing?

This is a full notebook dedicated to:
- Comparing each model against a naive baseline (e.g., "always predict up")
- Computing Sharpe-equivalent metric: if you acted on every signal, would returns be better than random?
- Documenting failure modes: when does the model fail? Is there a pattern?

Key concepts:
- The difference between in-sample and out-of-sample performance
- Why accuracy alone is misleading on imbalanced datasets
- Overfitting in time series: why cross-val folds must be temporal

**Phase 3 complete when:**
- At least two models trained and evaluated with walk-forward validation
- Each model has a clear write-up: what it predicts, what features it uses, where it fails
- You can compare models honestly against a naive baseline

---

## Skills inventory

After completing all three phases, you'll have hands-on experience with:

**Data Engineering**
- REST API integration and rate limiting
- Medallion architecture (Bronze/Silver/Gold)
- SQL Server stored procedures and ETL design
- Data quality validation
- Pipeline scheduling and observability

**Data Analysis**
- Time series EDA (rolling stats, regime detection)
- Technical indicators and financial feature engineering
- Correlation analysis
- Pandas and NumPy at production depth

**Data Science / ML**
- Unsupervised learning: clustering, anomaly detection
- Supervised classification with time series data
- Walk-forward validation and avoiding data leakage
- Model evaluation beyond accuracy: calibration, baseline comparison, feature importance
- Scikit-learn, XGBoost, LightGBM pipelines

---

## Reference: key tools

| Task | Library | Docs |
|---|---|---|
| Data manipulation | pandas | pandas.pydata.org |
| Numerical operations | numpy | numpy.org |
| ML models | scikit-learn | scikit-learn.org |
| Gradient boosting | xgboost, lightgbm | xgboost.readthedocs.io |
| Visualization | plotly, matplotlib | plotly.com/python |
| Scheduling | APScheduler | apscheduler.readthedocs.io |
| SQL Server | pyodbc | github.com/mkleehammer/pyodbc |
| Config/secrets | python-dotenv | pypi.org/project/python-dotenv |
