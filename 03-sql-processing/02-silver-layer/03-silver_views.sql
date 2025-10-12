-- =====================================================
-- SILVER LAYER - BUSINESS VIEWS
-- =====================================================
-- Purpose: Create business-focused views for Silver layer
-- Layer: Silver (Clean Data)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Usage: Business intelligence and data analysis
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- SILVER LAYER BUSINESS VIEWS
-- =====================================================

-- View: High Quality Data Summary
CREATE OR ALTER VIEW silver.v_high_quality_data
AS
SELECT 
    symbol,
    name,
    price_usd,
    market_cap_usd,
    volume_24h_usd,
    percent_change_24h,
    cmc_rank,
    data_quality_score,
    processed_timestamp,
    CASE 
        WHEN data_quality_score >= 0.95 THEN 'EXCELLENT'
        WHEN data_quality_score >= 0.80 THEN 'GOOD'
        WHEN data_quality_score >= 0.60 THEN 'ACCEPTABLE'
        ELSE 'POOR'
    END AS quality_tier
FROM silver.crypto_clean_data
WHERE is_active = 1 AND data_quality_score >= 0.80;
GO

-- View: Data Quality Dashboard
CREATE OR ALTER VIEW silver.v_data_quality_dashboard
AS
SELECT 
    'Silver Layer Quality Dashboard' AS dashboard_section,
    COUNT(*) AS total_clean_records,
    COUNT(DISTINCT symbol) AS unique_symbols,
    AVG(data_quality_score) AS avg_quality_score,
    MIN(data_quality_score) AS min_quality_score,
    MAX(data_quality_score) AS max_quality_score,
    
    -- Quality Distribution
    COUNT(CASE WHEN data_quality_score >= 0.95 THEN 1 END) AS excellent_quality_count,
    COUNT(CASE WHEN data_quality_score >= 0.80 THEN 1 END) AS good_quality_count,
    COUNT(CASE WHEN data_quality_score >= 0.60 THEN 1 END) AS acceptable_quality_count,
    COUNT(CASE WHEN data_quality_score < 0.60 THEN 1 END) AS poor_quality_count,
    
    -- Quality Percentages
    CAST(COUNT(CASE WHEN data_quality_score >= 0.95 THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS excellent_quality_pct,
    CAST(COUNT(CASE WHEN data_quality_score >= 0.80 THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS good_quality_pct,
    
    -- Temporal Information
    MIN(processed_timestamp) AS oldest_record,
    MAX(processed_timestamp) AS newest_record,
    DATEDIFF(MINUTE, MAX(processed_timestamp), GETDATE()) AS minutes_since_last_update
FROM silver.crypto_clean_data
WHERE is_active = 1;
GO

-- View: Market Leaders (Top 50 by Market Cap)
CREATE OR ALTER VIEW silver.v_market_leaders
AS
SELECT TOP 50
    symbol,
    name,
    price_usd,
    market_cap_usd,
    volume_24h_usd,
    percent_change_24h,
    percent_change_7d,
    cmc_rank,
    data_quality_score,
    processed_timestamp,
    
    -- Market Dominance Calculations
    market_cap_usd / SUM(market_cap_usd) OVER() * 100 AS market_dominance_pct,
    
    -- Ranking
    ROW_NUMBER() OVER (ORDER BY market_cap_usd DESC) AS market_cap_rank_calculated,
    ROW_NUMBER() OVER (ORDER BY volume_24h_usd DESC) AS volume_rank
    
FROM silver.crypto_clean_data
WHERE is_active = 1 
    AND market_cap_usd IS NOT NULL 
    AND data_quality_score >= 0.70
ORDER BY market_cap_usd DESC;
GO

-- View: Price Movement Analysis
CREATE OR ALTER VIEW silver.v_price_movement_analysis
AS
SELECT 
    symbol,
    name,
    price_usd,
    percent_change_1h,
    percent_change_24h,
    percent_change_7d,
    percent_change_30d,
    volume_24h_usd,
    market_cap_usd,
    processed_timestamp,
    
    -- Movement Classification
    CASE 
        WHEN percent_change_24h > 20 THEN 'STRONG_UP'
        WHEN percent_change_24h > 5 THEN 'UP'
        WHEN percent_change_24h > -5 THEN 'STABLE'
        WHEN percent_change_24h > -20 THEN 'DOWN'
        ELSE 'STRONG_DOWN'
    END AS movement_24h_category,
    
    -- Volatility Classification
    CASE 
        WHEN ABS(percent_change_24h) > 15 THEN 'HIGH_VOLATILITY'
        WHEN ABS(percent_change_24h) > 5 THEN 'MEDIUM_VOLATILITY'
        ELSE 'LOW_VOLATILITY'
    END AS volatility_category,
    
    -- Volume vs Market Cap Ratio
    CASE 
        WHEN market_cap_usd > 0 THEN volume_24h_usd / market_cap_usd * 100
        ELSE NULL 
    END AS volume_to_market_cap_ratio_pct

FROM silver.crypto_clean_data
WHERE is_active = 1 AND data_quality_score >= 0.70;
GO

-- View: Daily Trading Summary
CREATE OR ALTER VIEW silver.v_daily_trading_summary
AS
SELECT 
    snapshot_date,
    COUNT(*) AS symbols_tracked,
    AVG(closing_price) AS avg_closing_price,
    SUM(total_volume_24h) AS total_daily_volume,
    SUM(market_cap_close) AS total_market_cap,
    AVG(price_change_24h) AS avg_price_change_24h,
    
    -- Market Movers
    MAX(price_change_24h) AS biggest_gainer_pct,
    MIN(price_change_24h) AS biggest_loser_pct,
    
    -- Volume Analysis
    AVG(volume_change_24h) AS avg_volume_change_24h,
    
    -- Quality Metrics
    AVG(quality_score_avg) AS avg_data_quality,
    SUM(records_processed) AS total_records_processed
    
FROM silver.crypto_daily_snapshots
GROUP BY snapshot_date;
GO

-- View: Top Gainers and Losers
CREATE OR ALTER VIEW silver.v_top_movers
AS
WITH ranked_movers AS (
    SELECT 
        symbol,
        name,
        price_usd,
        percent_change_24h,
        volume_24h_usd,
        market_cap_usd,
        data_quality_score,
        processed_timestamp,
        ROW_NUMBER() OVER (ORDER BY percent_change_24h DESC) AS gainer_rank,
        ROW_NUMBER() OVER (ORDER BY percent_change_24h ASC) AS loser_rank
    FROM silver.crypto_clean_data
    WHERE is_active = 1 
        AND percent_change_24h IS NOT NULL
        AND data_quality_score >= 0.70
        AND market_cap_usd > 1000000 -- Only coins with >$1M market cap
)
SELECT 
    'TOP_GAINERS' AS mover_type,
    gainer_rank AS rank,
    symbol,
    name,
    price_usd,
    percent_change_24h,
    volume_24h_usd,
    market_cap_usd,
    data_quality_score
FROM ranked_movers
WHERE gainer_rank <= 10

UNION ALL

SELECT 
    'TOP_LOSERS' AS mover_type,
    loser_rank AS rank,
    symbol,
    name,
    price_usd,
    percent_change_24h,
    volume_24h_usd,
    market_cap_usd,
    data_quality_score
FROM ranked_movers
WHERE loser_rank <= 10;
GO

-- View: Volume Leaders
CREATE OR ALTER VIEW silver.v_volume_leaders
AS
SELECT TOP 25
    symbol,
    name,
    price_usd,
    volume_24h_usd,
    market_cap_usd,
    percent_change_24h,
    volume_change_24h,
    data_quality_score,
    processed_timestamp,
    
    -- Volume Analysis
    CASE 
        WHEN market_cap_usd > 0 THEN volume_24h_usd / market_cap_usd * 100
        ELSE NULL 
    END AS volume_turnover_pct,
    
    ROW_NUMBER() OVER (ORDER BY volume_24h_usd DESC) AS volume_rank

FROM silver.crypto_clean_data
WHERE is_active = 1 
    AND volume_24h_usd IS NOT NULL
    AND data_quality_score >= 0.70
ORDER BY volume_24h_usd DESC;
GO

-- View: Data Processing Statistics
CREATE OR ALTER VIEW silver.v_processing_statistics
AS
SELECT 
    process_name,
    COUNT(*) AS total_runs,
    AVG(records_input) AS avg_records_input,
    AVG(records_output) AS avg_records_output,
    AVG(records_rejected) AS avg_records_rejected,
    AVG(avg_quality_score) AS avg_quality_score_across_runs,
    COUNT(CASE WHEN process_status = 'SUCCESS' THEN 1 END) AS successful_runs,
    COUNT(CASE WHEN process_status = 'FAILED' THEN 1 END) AS failed_runs,
    CAST(COUNT(CASE WHEN process_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS success_rate_pct,
    AVG(execution_duration_seconds) AS avg_execution_duration_seconds,
    MIN(start_timestamp) AS first_run,
    MAX(start_timestamp) AS latest_run
FROM silver.processing_audit_log
GROUP BY process_name;
GO

-- View: Quality Metrics by Symbol
CREATE OR ALTER VIEW silver.v_quality_metrics_by_symbol
AS
SELECT 
    c.symbol,
    c.name,
    COUNT(m.id) AS total_quality_checks,
    AVG(m.metric_value) AS avg_metric_value,
    COUNT(CASE WHEN m.threshold_passed = 1 THEN 1 END) AS passed_checks,
    COUNT(CASE WHEN m.threshold_passed = 0 THEN 1 END) AS failed_checks,
    CAST(COUNT(CASE WHEN m.threshold_passed = 1 THEN 1 END) * 100.0 / COUNT(m.id) AS DECIMAL(5,2)) AS pass_rate_pct,
    MAX(c.data_quality_score) AS latest_quality_score,
    MAX(m.validation_timestamp) AS latest_check_timestamp
FROM silver.crypto_clean_data c
LEFT JOIN silver.data_quality_metrics m ON c.id = m.silver_record_id
WHERE c.is_active = 1
GROUP BY c.symbol, c.name;
GO

-- View: Historical Price Trends
CREATE OR ALTER VIEW silver.v_historical_price_trends
AS
SELECT 
    symbol,
    snapshot_date,
    closing_price,
    price_change_24h,
    total_volume_24h,
    market_cap_close,
    
    -- Moving Averages (simplified)
    AVG(closing_price) OVER (
        PARTITION BY symbol 
        ORDER BY snapshot_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS sma_7d,
    
    AVG(closing_price) OVER (
        PARTITION BY symbol 
        ORDER BY snapshot_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS sma_30d,
    
    -- Price Position vs Historical High/Low
    MAX(closing_price) OVER (
        PARTITION BY symbol 
        ORDER BY snapshot_date 
        ROWS UNBOUNDED PRECEDING
    ) AS historical_high,
    
    MIN(closing_price) OVER (
        PARTITION BY symbol 
        ORDER BY snapshot_date 
        ROWS UNBOUNDED PRECEDING
    ) AS historical_low,
    
    -- Days since historical high
    DATEDIFF(DAY, 
        MAX(CASE WHEN closing_price = MAX(closing_price) OVER (PARTITION BY symbol ORDER BY snapshot_date ROWS UNBOUNDED PRECEDING) THEN snapshot_date END) OVER (PARTITION BY symbol ORDER BY snapshot_date ROWS UNBOUNDED PRECEDING),
        snapshot_date
    ) AS days_since_high

FROM silver.crypto_daily_snapshots
WHERE quality_score_avg >= 0.70;
GO

