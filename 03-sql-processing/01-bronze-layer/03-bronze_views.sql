-- =====================================================
-- BRONZE LAYER - MONITORING VIEWS
-- =====================================================
-- Purpose: Create monitoring and analysis views for Bronze layer
-- Layer: Bronze (Raw Data Storage)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Usage: Data quality monitoring and operational insights
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- BRONZE LAYER MONITORING VIEWS
-- =====================================================

-- View: Latest Data Summary
CREATE OR ALTER VIEW bronze.v_latest_data_summary
AS
SELECT 
    symbol,
    name,
    COUNT(*) AS total_records,
    MIN(collection_timestamp) AS first_record,
    MAX(collection_timestamp) AS latest_record,
    DATEDIFF(HOUR, MIN(collection_timestamp), MAX(collection_timestamp)) AS data_span_hours,
    AVG(price_usd) AS avg_price_usd,
    MIN(price_usd) AS min_price_usd,
    MAX(price_usd) AS max_price_usd,
    COUNT(CASE WHEN price_usd IS NULL THEN 1 END) AS missing_price_count,
    COUNT(CASE WHEN market_cap_usd IS NULL THEN 1 END) AS missing_market_cap_count,
    COUNT(CASE WHEN volume_24h_usd IS NULL THEN 1 END) AS missing_volume_count
FROM bronze.crypto_raw_data
GROUP BY symbol, name;
GO

-- View: Data Quality Dashboard
CREATE OR ALTER VIEW bronze.v_data_quality_dashboard
AS
SELECT 
    'Bronze Layer Quality Metrics' AS dashboard_section,
    COUNT(*) AS total_records,
    COUNT(DISTINCT symbol) AS unique_symbols,
    COUNT(DISTINCT api_batch_id) AS unique_batches,
    
    -- Completeness Metrics
    COUNT(CASE WHEN price_usd IS NOT NULL THEN 1 END) AS price_complete_count,
    CAST(COUNT(CASE WHEN price_usd IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS price_completeness_pct,
    
    COUNT(CASE WHEN market_cap_usd IS NOT NULL THEN 1 END) AS market_cap_complete_count,
    CAST(COUNT(CASE WHEN market_cap_usd IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS market_cap_completeness_pct,
    
    COUNT(CASE WHEN volume_24h_usd IS NOT NULL THEN 1 END) AS volume_complete_count,
    CAST(COUNT(CASE WHEN volume_24h_usd IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS volume_completeness_pct,
    
    -- Data Quality Flags
    COUNT(CASE WHEN price_usd <= 0 THEN 1 END) AS invalid_price_count,
    COUNT(CASE WHEN market_cap_usd < 0 THEN 1 END) AS invalid_market_cap_count,
    COUNT(CASE WHEN volume_24h_usd < 0 THEN 1 END) AS invalid_volume_count,
    
    -- Temporal Metrics
    MIN(collection_timestamp) AS oldest_record,
    MAX(collection_timestamp) AS newest_record,
    DATEDIFF(MINUTE, MAX(collection_timestamp), GETDATE()) AS minutes_since_last_update

FROM bronze.crypto_raw_data;
GO

-- View: API Performance Metrics
CREATE OR ALTER VIEW bronze.v_api_performance_metrics
AS
SELECT 
    api_endpoint,
    request_status,
    COUNT(*) AS total_requests,
    AVG(response_time_ms) AS avg_response_time_ms,
    MIN(response_time_ms) AS min_response_time_ms,
    MAX(response_time_ms) AS max_response_time_ms,
    SUM(records_returned) AS total_records_returned,
    AVG(records_returned) AS avg_records_per_request,
    SUM(ISNULL(api_credits_used, 0)) AS total_credits_used,
    MIN(request_timestamp) AS first_request,
    MAX(request_timestamp) AS latest_request,
    COUNT(CASE WHEN request_status = 'SUCCESS' THEN 1 END) AS successful_requests,
    COUNT(CASE WHEN request_status = 'ERROR' THEN 1 END) AS failed_requests,
    CAST(COUNT(CASE WHEN request_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS success_rate_pct
FROM bronze.api_request_log
GROUP BY api_endpoint, request_status;
GO

-- View: Data Freshness Check
CREATE OR ALTER VIEW bronze.v_data_freshness
AS
SELECT 
    symbol,
    name,
    MAX(collection_timestamp) AS latest_update,
    DATEDIFF(MINUTE, MAX(collection_timestamp), GETDATE()) AS minutes_behind,
    CASE 
        WHEN DATEDIFF(MINUTE, MAX(collection_timestamp), GETDATE()) <= 30 THEN 'FRESH'
        WHEN DATEDIFF(MINUTE, MAX(collection_timestamp), GETDATE()) <= 120 THEN 'STALE'
        ELSE 'VERY_STALE'
    END AS freshness_status,
    COUNT(*) AS total_records_for_symbol
FROM bronze.crypto_raw_data
GROUP BY symbol, name;
GO

-- View: Batch Processing Summary
CREATE OR ALTER VIEW bronze.v_batch_processing_summary
AS
SELECT 
    api_batch_id,
    MIN(collection_timestamp) AS batch_start_time,
    MAX(collection_timestamp) AS batch_end_time,
    COUNT(*) AS records_in_batch,
    COUNT(DISTINCT symbol) AS unique_symbols_in_batch,
    AVG(price_usd) AS avg_price_in_batch,
    COUNT(CASE WHEN price_usd IS NULL THEN 1 END) AS null_prices_in_batch,
    DATEDIFF(SECOND, MIN(collection_timestamp), MAX(collection_timestamp)) AS batch_duration_seconds
FROM bronze.crypto_raw_data
WHERE api_batch_id IS NOT NULL
GROUP BY api_batch_id;
GO

-- View: Data Volume Trends
CREATE OR ALTER VIEW bronze.v_data_volume_trends
AS
SELECT 
    CAST(collection_timestamp AS DATE) AS collection_date,
    COUNT(*) AS daily_record_count,
    COUNT(DISTINCT symbol) AS unique_symbols_per_day,
    COUNT(DISTINCT api_batch_id) AS batches_per_day,
    AVG(price_usd) AS avg_daily_price,
    SUM(CASE WHEN price_usd IS NULL THEN 1 ELSE 0 END) AS daily_null_price_count,
    CAST(SUM(CASE WHEN price_usd IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS daily_null_price_pct
FROM bronze.crypto_raw_data
GROUP BY CAST(collection_timestamp AS DATE);
GO

-- View: Top Cryptocurrencies by Record Count
CREATE OR ALTER VIEW bronze.v_top_cryptos_by_records
AS
SELECT TOP 50
    symbol,
    name,
    COUNT(*) AS total_records,
    MIN(collection_timestamp) AS first_seen,
    MAX(collection_timestamp) AS last_seen,
    DATEDIFF(DAY, MIN(collection_timestamp), MAX(collection_timestamp)) AS days_tracked,
    AVG(price_usd) AS avg_price,
    MAX(price_usd) AS max_price,
    MIN(price_usd) AS min_price,
    AVG(market_cap_usd) AS avg_market_cap,
    AVG(volume_24h_usd) AS avg_volume_24h,
    COUNT(DISTINCT CAST(collection_timestamp AS DATE)) AS unique_days_with_data
FROM bronze.crypto_raw_data
WHERE symbol IS NOT NULL
GROUP BY symbol, name
ORDER BY COUNT(*) DESC;
GO

-- View: Data Lineage Summary
CREATE OR ALTER VIEW bronze.v_data_lineage_summary
AS
SELECT 
    source_system,
    extraction_method,
    extraction_status,
    COUNT(*) AS total_extractions,
    SUM(records_extracted) AS total_records_extracted,
    AVG(records_extracted) AS avg_records_per_extraction,
    MIN(extraction_timestamp) AS first_extraction,
    MAX(extraction_timestamp) AS latest_extraction,
    COUNT(CASE WHEN extraction_status = 'SUCCESS' THEN 1 END) AS successful_extractions,
    CAST(COUNT(CASE WHEN extraction_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS extraction_success_rate_pct
FROM bronze.data_lineage
GROUP BY source_system, extraction_method, extraction_status;
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '';
PRINT '🥉 =====================================================';
PRINT '   BRONZE LAYER MONITORING VIEWS CREATED';
PRINT '=====================================================';
PRINT '';
PRINT '✅ Views Created:';
PRINT '   • bronze.v_latest_data_summary - Latest data by symbol';
PRINT '   • bronze.v_data_quality_dashboard - Quality metrics overview';
PRINT '   • bronze.v_api_performance_metrics - API performance tracking';
PRINT '   • bronze.v_data_freshness - Data freshness monitoring';
PRINT '   • bronze.v_batch_processing_summary - Batch processing insights';
PRINT '   • bronze.v_data_volume_trends - Daily volume trends';
PRINT '   • bronze.v_top_cryptos_by_records - Most tracked cryptocurrencies';
PRINT '   • bronze.v_data_lineage_summary - Data lineage overview';
PRINT '';
PRINT '📊 Purpose: Operational monitoring and data quality insights';
PRINT '🎯 Usage: SELECT * FROM bronze.v_data_quality_dashboard;';
PRINT '';
PRINT '💡 Bronze Layer Complete: Schema + Procedures + Views';
PRINT '=====================================================';
GO