-- ================================================================================================
-- CryptoSphere Analytics Platform - Bronze Layer Views
-- ================================================================================================
-- Purpose: Views for accessing and analyzing raw cryptocurrency data
-- Layer: Bronze (Raw Data)
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- ================================================================================================

SET search_path TO bronze, metadata, public;

-- ================================================================================================
-- 1. CURRENT STATE VIEWS
-- ================================================================================================

-- View: Latest cryptocurrency quotes with enriched data
CREATE OR REPLACE VIEW v_latest_crypto_quotes AS
SELECT 
    q.cmc_id,
    q.symbol,
    l.name,
    l.slug,
    q.price,
    q.volume_24h,
    q.percent_change_1h,
    q.percent_change_24h,
    q.percent_change_7d,
    q.market_cap,
    q.market_cap_dominance,
    l.cmc_rank,
    l.circulating_supply,
    l.max_supply,
    q.last_updated,
    q.api_call_timestamp,
    -- Calculated fields
    CASE 
        WHEN l.circulating_supply > 0 THEN q.price * l.circulating_supply
        ELSE NULL
    END as calculated_market_cap,
    
    CASE 
        WHEN l.max_supply > 0 THEN q.price * l.max_supply
        ELSE NULL
    END as calculated_max_market_cap,
    
    -- Data quality indicators
    CASE 
        WHEN q.price IS NULL THEN 'MISSING_PRICE'
        WHEN q.price <= 0 THEN 'INVALID_PRICE'
        WHEN q.volume_24h IS NULL THEN 'MISSING_VOLUME'
        WHEN q.volume_24h < 0 THEN 'INVALID_VOLUME'
        ELSE 'VALID'
    END as data_quality_status,
    
    -- Freshness indicator
    CASE 
        WHEN q.api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '5 minutes' THEN 'FRESH'
        WHEN q.api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 'RECENT'
        WHEN q.api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 'STALE'
        ELSE 'OUTDATED'
    END as data_freshness
    
FROM raw_crypto_quotes q
LEFT JOIN raw_crypto_listings l ON q.cmc_id = l.cmc_id
WHERE q.api_call_timestamp = (
    SELECT MAX(api_call_timestamp)
    FROM raw_crypto_quotes q2
    WHERE q2.cmc_id = q.cmc_id
);

-- View: Top cryptocurrencies by market cap with latest data
CREATE OR REPLACE VIEW v_top_cryptos_current AS
SELECT 
    cmc_id,
    symbol,
    name,
    cmc_rank,
    price,
    market_cap,
    volume_24h,
    percent_change_24h,
    circulating_supply,
    max_supply,
    last_updated,
    data_quality_status,
    data_freshness
FROM v_latest_crypto_quotes
WHERE cmc_rank IS NOT NULL
  AND data_quality_status = 'VALID'
ORDER BY cmc_rank ASC
LIMIT 100;

-- ================================================================================================
-- 2. HISTORICAL ANALYSIS VIEWS
-- ================================================================================================

-- View: Hourly aggregated crypto data for time series analysis
CREATE OR REPLACE VIEW v_crypto_hourly_agg AS
SELECT 
    cmc_id,
    symbol,
    DATE_TRUNC('hour', api_call_timestamp) as hour_timestamp,
    
    -- Price aggregations
    FIRST_VALUE(price ORDER BY api_call_timestamp) as hour_open_price,
    MAX(price) as hour_high_price,
    MIN(price) as hour_low_price,
    LAST_VALUE(price ORDER BY api_call_timestamp) as hour_close_price,
    AVG(price) as hour_avg_price,
    
    -- Volume aggregations
    AVG(volume_24h) as avg_volume_24h,
    MAX(volume_24h) as max_volume_24h,
    
    -- Market cap aggregations
    FIRST_VALUE(market_cap ORDER BY api_call_timestamp) as hour_open_market_cap,
    LAST_VALUE(market_cap ORDER BY api_call_timestamp) as hour_close_market_cap,
    AVG(market_cap) as hour_avg_market_cap,
    
    -- Statistical measures
    STDDEV(price) as price_volatility,
    COUNT(*) as data_points,
    
    -- Data quality metrics
    COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as valid_price_points,
    COUNT(CASE WHEN volume_24h IS NOT NULL THEN 1 END) as valid_volume_points
    
FROM raw_crypto_quotes
WHERE api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY 
    cmc_id, 
    symbol, 
    DATE_TRUNC('hour', api_call_timestamp)
ORDER BY 
    symbol, 
    hour_timestamp DESC;

-- View: Daily aggregated crypto data
CREATE OR REPLACE VIEW v_crypto_daily_agg AS
SELECT 
    cmc_id,
    symbol,
    DATE_TRUNC('day', api_call_timestamp) as day_date,
    
    -- OHLC data
    FIRST_VALUE(price ORDER BY api_call_timestamp) as day_open_price,
    MAX(price) as day_high_price,
    MIN(price) as day_low_price,
    LAST_VALUE(price ORDER BY api_call_timestamp) as day_close_price,
    
    -- Volume and market cap
    AVG(volume_24h) as avg_volume_24h,
    FIRST_VALUE(market_cap ORDER BY api_call_timestamp) as day_open_market_cap,
    LAST_VALUE(market_cap ORDER BY api_call_timestamp) as day_close_market_cap,
    
    -- Price movements
    (LAST_VALUE(price ORDER BY api_call_timestamp) - FIRST_VALUE(price ORDER BY api_call_timestamp)) / 
    FIRST_VALUE(price ORDER BY api_call_timestamp) * 100 as daily_price_change_pct,
    
    -- Volatility measures
    STDDEV(price) as daily_price_volatility,
    (MAX(price) - MIN(price)) / FIRST_VALUE(price ORDER BY api_call_timestamp) * 100 as daily_price_range_pct,
    
    -- Data quality
    COUNT(*) as total_data_points,
    COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as valid_data_points
    
FROM raw_crypto_quotes
WHERE api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY 
    cmc_id, 
    symbol, 
    DATE_TRUNC('day', api_call_timestamp)
ORDER BY 
    symbol, 
    day_date DESC;

-- ================================================================================================
-- 3. DATA QUALITY AND MONITORING VIEWS
-- ================================================================================================

-- View: Data quality dashboard
CREATE OR REPLACE VIEW v_data_quality_dashboard AS
SELECT 
    symbol,
    COUNT(*) as total_records,
    COUNT(CASE WHEN price IS NULL THEN 1 END) as null_prices,
    COUNT(CASE WHEN price <= 0 THEN 1 END) as invalid_prices,
    COUNT(CASE WHEN volume_24h IS NULL THEN 1 END) as null_volumes,
    COUNT(CASE WHEN volume_24h < 0 THEN 1 END) as invalid_volumes,
    
    -- Quality percentages
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN price IS NULL OR price <= 0 THEN 1 END))::NUMERIC / 
        COUNT(*) * 100, 2
    ) as price_quality_pct,
    
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN volume_24h IS NULL OR volume_24h < 0 THEN 1 END))::NUMERIC / 
        COUNT(*) * 100, 2
    ) as volume_quality_pct,
    
    -- Temporal coverage
    MIN(api_call_timestamp) as first_record,
    MAX(api_call_timestamp) as latest_record,
    EXTRACT(HOURS FROM (MAX(api_call_timestamp) - MIN(api_call_timestamp))) as coverage_hours,
    
    -- Data freshness
    EXTRACT(MINUTES FROM (CURRENT_TIMESTAMP - MAX(api_call_timestamp))) as minutes_since_last_update
    
FROM raw_crypto_quotes
WHERE api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY symbol
ORDER BY latest_record DESC;

-- View: API performance monitoring
CREATE OR REPLACE VIEW v_api_performance_monitor AS
SELECT 
    DATE_TRUNC('hour', call_timestamp) as hour_timestamp,
    api_name,
    endpoint,
    
    -- Call statistics
    COUNT(*) as total_calls,
    COUNT(CASE WHEN http_status = 200 THEN 1 END) as successful_calls,
    COUNT(CASE WHEN http_status != 200 THEN 1 END) as failed_calls,
    
    -- Performance metrics
    AVG(response_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,
    
    -- Rate limiting
    AVG(rate_limit_remaining) as avg_rate_limit_remaining,
    MIN(rate_limit_remaining) as min_rate_limit_remaining,
    
    -- Cost tracking
    SUM(cost_credits) as total_credits_used,
    
    -- Success rate
    ROUND(
        COUNT(CASE WHEN http_status = 200 THEN 1 END)::NUMERIC / 
        COUNT(*) * 100, 2
    ) as success_rate_pct
    
FROM api_calls
WHERE call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY 
    DATE_TRUNC('hour', call_timestamp),
    api_name,
    endpoint
ORDER BY 
    hour_timestamp DESC,
    api_name,
    endpoint;

-- ================================================================================================
-- 4. ANALYSIS AND INSIGHTS VIEWS
-- ================================================================================================

-- View: Price movement analysis
CREATE OR REPLACE VIEW v_price_movement_analysis AS
WITH price_with_lag AS (
    SELECT 
        cmc_id,
        symbol,
        api_call_timestamp,
        price,
        LAG(price, 1) OVER (PARTITION BY cmc_id ORDER BY api_call_timestamp) as prev_price,
        LAG(api_call_timestamp, 1) OVER (PARTITION BY cmc_id ORDER BY api_call_timestamp) as prev_timestamp
    FROM raw_crypto_quotes
    WHERE api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
      AND price IS NOT NULL
      AND price > 0
)
SELECT 
    cmc_id,
    symbol,
    api_call_timestamp,
    price,
    prev_price,
    
    -- Price change calculations
    CASE 
        WHEN prev_price IS NOT NULL AND prev_price > 0 THEN
            (price - prev_price) / prev_price * 100
        ELSE NULL
    END as price_change_pct,
    
    -- Time between updates
    CASE 
        WHEN prev_timestamp IS NOT NULL THEN
            EXTRACT(MINUTES FROM (api_call_timestamp - prev_timestamp))
        ELSE NULL
    END as minutes_since_prev_update,
    
    -- Movement classification
    CASE 
        WHEN prev_price IS NULL THEN 'NO_PREVIOUS_DATA'
        WHEN ABS((price - prev_price) / prev_price) < 0.001 THEN 'STABLE'
        WHEN (price - prev_price) / prev_price > 0.05 THEN 'STRONG_UP'
        WHEN (price - prev_price) / prev_price > 0.01 THEN 'MODERATE_UP'
        WHEN (price - prev_price) / prev_price > 0 THEN 'SLIGHT_UP'
        WHEN (price - prev_price) / prev_price < -0.05 THEN 'STRONG_DOWN'
        WHEN (price - prev_price) / prev_price < -0.01 THEN 'MODERATE_DOWN'
        WHEN (price - prev_price) / prev_price < 0 THEN 'SLIGHT_DOWN'
        ELSE 'STABLE'
    END as movement_classification
    
FROM price_with_lag
ORDER BY 
    symbol,
    api_call_timestamp DESC;

-- View: Market correlation matrix (simplified for top 10 cryptos)
CREATE OR REPLACE VIEW v_market_correlation_matrix AS
WITH hourly_returns AS (
    SELECT 
        symbol,
        DATE_TRUNC('hour', api_call_timestamp) as hour_timestamp,
        AVG(price) as avg_price
    FROM raw_crypto_quotes
    WHERE api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
      AND price IS NOT NULL
      AND price > 0
    GROUP BY symbol, DATE_TRUNC('hour', api_call_timestamp)
),
returns_with_lag AS (
    SELECT 
        symbol,
        hour_timestamp,
        avg_price,
        LAG(avg_price) OVER (PARTITION BY symbol ORDER BY hour_timestamp) as prev_price,
        CASE 
            WHEN LAG(avg_price) OVER (PARTITION BY symbol ORDER BY hour_timestamp) IS NOT NULL 
            AND LAG(avg_price) OVER (PARTITION BY symbol ORDER BY hour_timestamp) > 0 THEN
                (avg_price - LAG(avg_price) OVER (PARTITION BY symbol ORDER BY hour_timestamp)) / 
                LAG(avg_price) OVER (PARTITION BY symbol ORDER BY hour_timestamp)
            ELSE NULL
        END as hourly_return
    FROM hourly_returns
)
SELECT 
    a.symbol as symbol_a,
    b.symbol as symbol_b,
    COUNT(*) as observation_count,
    CORR(a.hourly_return, b.hourly_return) as correlation_coefficient,
    
    -- Correlation strength classification
    CASE 
        WHEN ABS(CORR(a.hourly_return, b.hourly_return)) >= 0.8 THEN 'VERY_STRONG'
        WHEN ABS(CORR(a.hourly_return, b.hourly_return)) >= 0.6 THEN 'STRONG'
        WHEN ABS(CORR(a.hourly_return, b.hourly_return)) >= 0.4 THEN 'MODERATE'
        WHEN ABS(CORR(a.hourly_return, b.hourly_return)) >= 0.2 THEN 'WEAK'
        ELSE 'VERY_WEAK'
    END as correlation_strength
    
FROM returns_with_lag a
JOIN returns_with_lag b ON a.hour_timestamp = b.hour_timestamp
WHERE a.hourly_return IS NOT NULL
  AND b.hourly_return IS NOT NULL
  AND a.symbol <= b.symbol  -- Avoid duplicate pairs
GROUP BY a.symbol, b.symbol
HAVING COUNT(*) >= 24  -- At least 24 hours of data
ORDER BY ABS(CORR(a.hourly_return, b.hourly_return)) DESC;

-- ================================================================================================
-- GRANT PERMISSIONS
-- ================================================================================================

-- Grant select permissions to read-only roles
-- GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO crypto_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO crypto_readwrite;

-- ================================================================================================
-- USAGE EXAMPLES
-- ================================================================================================

/*
-- Example: Get latest quotes for top 10 cryptocurrencies
SELECT * FROM v_top_cryptos_current LIMIT 10;

-- Example: Get hourly Bitcoin data for the last 24 hours
SELECT * FROM v_crypto_hourly_agg 
WHERE symbol = 'BTC' 
  AND hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY hour_timestamp DESC;

-- Example: Check data quality for all cryptocurrencies
SELECT * FROM v_data_quality_dashboard
ORDER BY price_quality_pct DESC;

-- Example: Monitor API performance
SELECT * FROM v_api_performance_monitor
WHERE hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '6 hours'
ORDER BY hour_timestamp DESC;

-- Example: Analyze recent price movements
SELECT * FROM v_price_movement_analysis
WHERE symbol IN ('BTC', 'ETH', 'ADA')
  AND api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '2 hours'
ORDER BY symbol, api_call_timestamp DESC;

-- Example: Check market correlations
SELECT * FROM v_market_correlation_matrix
WHERE correlation_strength IN ('STRONG', 'VERY_STRONG')
ORDER BY ABS(correlation_coefficient) DESC;
*/