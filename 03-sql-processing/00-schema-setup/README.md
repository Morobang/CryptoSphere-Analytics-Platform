# 🏆 CryptoSphere Medallion Architecture - SQL Server Implementation

## 🎯 **Architecture Overview**

This is a **proper medallion architecture** implementation for cryptocurrency analytics using **SQL Server (DESKTOP-939GPCA)**.

### 📊 **Data Flow: API → Bronze → Silver → Gold**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CoinMarketCap │    │     BRONZE      │    │     SILVER      │    │      GOLD       │
│       API       │───▶│   (Raw Data)    │───▶│  (Clean Data)   │───▶│  (Analytics)    │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │                        │
                              ▼                        ▼                        ▼
                       • Raw JSON Storage      • Data Validation      • KPIs & Metrics
                       • Minimal Processing    • Type Conversion       • Technical Analysis
                       • Full History          • Quality Scoring       • ML Features
                       • Error Logging         • Deduplication         • Business Reports
```

## 🥉 **BRONZE LAYER** - Raw Data Storage

**Purpose**: Store raw, unprocessed data exactly as received from APIs

### Key Principles:
- ✅ **Store Everything**: Never lose raw data
- ✅ **Minimal Processing**: Just basic parsing
- ✅ **Full History**: Keep all versions
- ✅ **Error Tolerance**: Accept imperfect data

### Tables:
- `bronze.crypto_raw_data` - Raw cryptocurrency data from API
- `bronze.api_request_log` - API call tracking and monitoring

## 🥈 **SILVER LAYER** - Clean & Validated Data

**Purpose**: Cleaned, validated, standardized data ready for business use

### Key Principles:
- ✅ **Data Quality**: Validate and score all data
- ✅ **Type Conversion**: Proper data types
- ✅ **Deduplication**: Remove duplicates
- ✅ **Business Rules**: Apply validation rules

### Tables:
- `silver.crypto_clean_data` - Validated cryptocurrency data
- `silver.data_quality_metrics` - Quality tracking per record
- `silver.crypto_daily_snapshots` - Daily aggregated data

## 🥇 **GOLD LAYER** - Analytics & Business Intelligence

**Purpose**: Business-ready data marts for analytics, ML, and reporting

### Key Principles:
- ✅ **Business Focus**: Designed for specific use cases
- ✅ **Performance**: Optimized for queries
- ✅ **Aggregations**: Pre-calculated metrics
- ✅ **ML Ready**: Feature engineering complete

### Data Marts:
- `gold.market_overview_daily` - Daily market summaries
- `gold.crypto_performance_metrics` - Technical indicators
- `gold.trading_signals` - ML-generated signals
- `gold.ml_features` - Machine learning features

## 🔄 **ETL PROCEDURES**

### Bronze → Silver ETL
- Data validation and cleaning
- Type conversions and standardization
- Quality scoring and flagging
- Duplicate detection and removal

### Silver → Gold ETL
- Business logic application
- Aggregations and calculations
- Technical indicator generation
- ML feature engineering

## 📁 **File Organization**

```
03-sql-processing/
├── 00-MEDALLION-ARCHITECTURE/
│   ├── README.md                    # This architecture guide
│   └── 01-setup_all_layers.sql     # Complete setup script
├── 01-BRONZE-LAYER/
│   ├── 01-create_bronze_schema.sql  # Schema and tables
│   ├── 02-bronze_procedures.sql     # Data insertion procedures
│   └── 03-bronze_views.sql          # Monitoring views
├── 02-SILVER-LAYER/
│   ├── 01-create_silver_schema.sql  # Schema and tables
│   ├── 02-silver_etl_procedures.sql # Bronze→Silver ETL
│   └── 03-silver_views.sql          # Business views
├── 03-GOLD-LAYER/
│   ├── 01-create_gold_schema.sql    # Schema and data marts
│   ├── 02-gold_etl_procedures.sql   # Silver→Gold ETL
│   └── 03-gold_views.sql            # Analytics views
└── 04-AUTOMATION/
    ├── 01-complete_etl_pipeline.sql # Full pipeline automation
    └── 02-monitoring_alerts.sql     # Data quality monitoring
```

## 🚀 **Quick Setup**

### 1. Run Complete Setup
```sql
-- Execute the master setup script
USE master;
EXEC xp_cmdshell 'sqlcmd -S DESKTOP-939GPCA -E -i "00-MEDALLION-ARCHITECTURE\01-setup_all_layers.sql"';
```

### 2. Test Data Flow
```sql
-- Insert test data into Bronze
EXEC bronze.sp_insert_crypto_simple 1, 'Bitcoin', 'BTC', 50000.00;

-- Run Bronze → Silver ETL
EXEC silver.sp_process_bronze_to_silver;

-- Run Silver → Gold ETL
EXEC gold.sp_process_silver_to_gold;

-- Check results
SELECT * FROM gold.market_overview_daily WHERE symbol = 'BTC';
```

## 📊 **Usage Examples**

### Insert Data (Bronze Layer)
```sql
-- Simple insert from Python
EXEC bronze.sp_insert_crypto_simple 
    @crypto_id = 1,
    @name = 'Bitcoin',
    @symbol = 'BTC',
    @price_usd = 45000.00,
    @market_cap_usd = 850000000000.00;
```

### Process Data (Silver Layer)
```sql
-- Clean and validate data
EXEC silver.sp_process_bronze_to_silver;

-- Check data quality
SELECT * FROM silver.v_data_quality_dashboard;
```

### Analytics (Gold Layer)
```sql
-- Get market overview
SELECT * FROM gold.v_market_overview_latest;

-- Get trading signals
SELECT * FROM gold.trading_signals 
WHERE confidence_score > 0.7 
AND signal_date >= DATEADD(day, -7, GETDATE());
```

## 🛡️ **Data Quality Framework**

### Quality Scoring (0.0 - 1.0)
- **Price Validity**: Non-null, positive values
- **Market Cap Consistency**: Reasonable relative to price
- **Volume Analysis**: Non-negative, realistic values
- **Change Percentages**: Within expected ranges (-100% to +1000%)

### Quality Thresholds
- **Gold Standard**: Score ≥ 0.95
- **Good Quality**: Score ≥ 0.80
- **Acceptable**: Score ≥ 0.60
- **Poor Quality**: Score < 0.60 (flagged for review)

## 📈 **Business Benefits**

### For Data Engineers
- ✅ Clear separation of concerns
- ✅ Easy debugging and maintenance
- ✅ Scalable architecture
- ✅ Automated quality monitoring

### For Data Scientists
- ✅ Clean, validated data in Silver layer
- ✅ ML-ready features in Gold layer
- ✅ Historical data preservation
- ✅ Data lineage tracking

### For Business Users
- ✅ Real-time market insights
- ✅ Technical analysis indicators
- ✅ Trading signal generation
- ✅ Risk management metrics

---

**This medallion architecture ensures data quality, enables efficient analytics, and supports machine learning workflows while maintaining full data lineage and audit capabilities.**