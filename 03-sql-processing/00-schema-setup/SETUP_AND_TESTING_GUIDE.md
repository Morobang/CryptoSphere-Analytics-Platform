# 🚀 CryptoSphere Medallion Architecture - Setup & Testing Guide

## 📋 **COMPLETE SETUP INSTRUCTIONS**

### Step 1: Run the Master Setup Script

```sql
-- Connect to SQL Server (DESKTOP-939GPCA)
-- Run the complete setup script
USE master;
GO

-- Execute the master setup (creates all tables, schemas, and procedures)
:r "C:\Users\Morobang\Documents\GitHub\CryptoSphere-Analytics-Platform\03-sql-processing\00-MEDALLION-ARCHITECTURE\01-setup_all_layers.sql"
```

### Step 2: Create All Layer Procedures

```sql
-- Switch to the database
USE cryptosphere_analytics;
GO

-- Bronze layer procedures
:r "C:\Users\Morobang\Documents\GitHub\CryptoSphere-Analytics-Platform\03-sql-processing\01-BRONZE-LAYER\02-bronze_procedures.sql"

-- Silver layer ETL procedures
:r "C:\Users\Morobang\Documents\GitHub\CryptoSphere-Analytics-Platform\03-sql-processing\02-SILVER-LAYER\02-silver_etl_procedures.sql"

-- Gold layer ETL procedures
:r "C:\Users\Morobang\Documents\GitHub\CryptoSphere-Analytics-Platform\03-sql-processing\03-GOLD-LAYER\02-gold_etl_procedures.sql"

-- Automation and monitoring
:r "C:\Users\Morobang\Documents\GitHub\CryptoSphere-Analytics-Platform\03-sql-processing\04-AUTOMATION\01-complete_etl_pipeline.sql"
:r "C:\Users\Morobang\Documents\GitHub\CryptoSphere-Analytics-Platform\03-sql-processing\04-AUTOMATION\02-data_quality_monitoring.sql"
```

---

## 🧪 **TESTING THE COMPLETE PIPELINE**

### Test 1: Bronze Layer Data Insertion (From Your Notebook)

```python
# In your Jupyter notebook (02-notebooks/01-data_acquisition.ipynb)
# Use the new Bronze layer procedures

# Simple insertion (8 fields)
cursor.execute("""
    EXEC bronze.sp_insert_crypto_simple 
        @crypto_id = ?, 
        @name = ?, 
        @symbol = ?, 
        @price_usd = ?, 
        @market_cap_usd = ?, 
        @volume_24h_usd = ?, 
        @percent_change_24h = ?, 
        @cmc_rank = ?
""", (1, 'Bitcoin', 'BTC', 45000.00, 850000000000.00, 25000000000.00, 2.5, 1))

# Complete insertion (22 fields) - recommended
cursor.execute("""
    EXEC bronze.sp_insert_crypto_complete 
        @crypto_id = ?, @name = ?, @symbol = ?, @slug = ?, @cmc_rank = ?,
        @circulating_supply = ?, @total_supply = ?, @max_supply = ?,
        @price_usd = ?, @volume_24h_usd = ?, @market_cap_usd = ?,
        @percent_change_1h = ?, @percent_change_24h = ?, @percent_change_7d = ?,
        @percent_change_30d = ?, @percent_change_60d = ?, @percent_change_90d = ?,
        @volume_change_24h = ?, @market_cap_dominance = ?, 
        @fully_diluted_market_cap = ?, @tvl = ?, @raw_json_data = ?
""", (
    crypto_data['id'], crypto_data['name'], crypto_data['symbol'], 
    crypto_data.get('slug'), crypto_data.get('cmc_rank'),
    # ... all 22 fields from your DataFrame
))
```

### Test 2: Verify Bronze Layer Data

```sql
-- Check Bronze layer data
EXEC bronze.sp_get_latest_data @limit = 10;

-- Run Bronze data quality check
EXEC bronze.sp_data_quality_check;

-- Check API logs
SELECT TOP 10 * FROM bronze.api_request_log ORDER BY request_timestamp DESC;
```

### Test 3: Run Silver Layer ETL

```sql
-- Process Bronze → Silver
EXEC silver.sp_process_bronze_to_silver @batch_size = 1000, @min_quality_score = 0.60;

-- Create daily snapshots
EXEC silver.sp_create_daily_snapshots;

-- Check Silver layer results
SELECT TOP 10 
    symbol, name, price_usd, data_quality_score, processed_timestamp
FROM silver.crypto_clean_data 
ORDER BY processed_timestamp DESC;

-- View Silver data quality dashboard
EXEC silver.sp_data_quality_dashboard;
```

### Test 4: Run Gold Layer ETL

```sql
-- Run complete Gold layer ETL
EXEC gold.sp_run_complete_gold_etl;

-- Check individual Gold components
SELECT * FROM gold.market_overview_daily WHERE report_date = CAST(GETDATE() AS DATE);

SELECT TOP 10 * FROM gold.crypto_performance_metrics 
WHERE analysis_date = CAST(GETDATE() AS DATE);

SELECT TOP 10 * FROM gold.trading_signals 
WHERE CAST(signal_date AS DATE) = CAST(GETDATE() AS DATE);

SELECT TOP 10 * FROM gold.ml_features 
WHERE feature_date = CAST(GETDATE() AS DATE);
```

### Test 5: Run Complete Pipeline

```sql
-- Run the complete medallion pipeline
EXEC etl.sp_run_complete_medallion_pipeline 
    @process_date = NULL,  -- Today
    @cleanup_old_data = 0, -- Don't cleanup during testing
    @cleanup_days = 90;
```

### Test 6: Data Quality Monitoring

```sql
-- Run all data quality checks
EXEC dq.sp_run_data_quality_checks;

-- View quality dashboard
EXEC dq.sp_data_quality_dashboard @hours_back = 24;

-- Check for alerts
SELECT TOP 10 * FROM dbo.data_quality_alerts 
WHERE alert_timestamp >= DATEADD(HOUR, -24, GETDATE())
ORDER BY alert_timestamp DESC;
```

### Test 7: Pipeline Health Check

```sql
-- Overall health check
EXEC etl.sp_pipeline_health_check;

-- Check ETL job history
SELECT TOP 20 
    job_name, start_time, end_time, status, 
    records_processed, execution_duration_seconds
FROM dbo.etl_job_log 
ORDER BY start_time DESC;
```

---

## 📊 **EXPECTED RESULTS**

### After Bronze Layer:
- ✅ Raw data stored in `bronze.crypto_raw_data`
- ✅ API calls logged in `bronze.api_request_log`
- ✅ All 22 fields populated (or NULLs where appropriate)

### After Silver Layer:
- ✅ Clean data in `silver.crypto_clean_data` with quality scores
- ✅ Daily snapshots in `silver.crypto_daily_snapshots`
- ✅ Quality metrics in `silver.data_quality_metrics`

### After Gold Layer:
- ✅ Market overview in `gold.market_overview_daily`
- ✅ Technical indicators in `gold.crypto_performance_metrics`
- ✅ Trading signals in `gold.trading_signals`
- ✅ ML features in `gold.ml_features`

---

## 🔧 **TROUBLESHOOTING**

### Common Issues:

1. **"Schema does not exist"**
   - Re-run the master setup script: `01-setup_all_layers.sql`

2. **"Procedure not found"**
   - Run the specific layer procedure files in order

3. **"No data in Silver/Gold layers"**
   - Check if Bronze layer has data first
   - Verify quality score thresholds (min 0.60)

4. **"Data quality checks failing"**
   - Check `dbo.data_quality_alerts` for specific issues
   - Review data in Bronze layer for completeness

5. **"ETL jobs showing errors"**
   - Check `dbo.etl_job_log` for error messages
   - Verify data types and NULL handling

---

## 🎯 **DAILY OPERATION**

### Step 1: Run Your Python Notebook
- Execute `02-notebooks/01-data_acquisition.ipynb`
- Use the new Bronze procedures for data insertion

### Step 2: Run Daily Pipeline
```sql
-- Run daily automated pipeline
EXEC etl.sp_daily_scheduled_pipeline;
```

### Step 3: Monitor Quality
```sql
-- Check daily quality
EXEC dq.sp_data_quality_dashboard;
```

---

## 🏆 **MEDALLION ARCHITECTURE BENEFITS**

### ✅ **Data Quality**
- Comprehensive quality scoring (0.0-1.0)
- Automated validation rules
- Alert system for issues

### ✅ **Scalability**
- Proper indexing strategy
- Batch processing capabilities
- Incremental ETL operations

### ✅ **Business Value**
- Real-time trading signals
- Technical analysis indicators
- ML-ready feature engineering

### ✅ **Monitoring**
- Complete audit trail
- Performance metrics
- Health check dashboards

---

## 🚀 **NEXT STEPS**

1. **Test with Real Data**: Run your notebook with CoinMarketCap API data
2. **Schedule Automation**: Set up SQL Server Agent jobs for daily runs
3. **Add More Symbols**: Expand beyond current cryptocurrency set
4. **ML Integration**: Use Gold layer features for model training
5. **Visualization**: Connect Power BI to Gold layer tables

---

**🎉 Your medallion architecture is now complete and ready for production!**