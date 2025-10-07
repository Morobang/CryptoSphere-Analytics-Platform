-- ================================================================================================
-- CryptoSphere Analytics Platform - Silver Layer Tables
-- ================================================================================================
-- Purpose: Clean, validated, and standardized cryptocurrency data tables
-- Layer: Silver (Cleaned Data)
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- ================================================================================================

-- Create silver schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS silver;
SET search_path TO silver, bronze, metadata, public;

-- ================================================================================================
-- 1. CLEANED CRYPTOCURRENCY LISTINGS TABLE
-- ================================================================================================

CREATE TABLE clean_crypto_listings (
    -- Primary identifiers
    id SERIAL PRIMARY KEY,
    cmc_id INTEGER NOT NULL,
    symbol crypto_symbol NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    
    -- Market data
    num_market_pairs INTEGER,
    cmc_rank INTEGER,
    
    -- Supply data (cleaned and validated)
    max_supply NUMERIC(30,8),
    circulating_supply NUMERIC(30,8),
    total_supply NUMERIC(30,8),
    
    -- Calculated fields
    supply_ratio NUMERIC(5,4), -- circulating/max supply
    is_fully_diluted BOOLEAN,
    
    -- Metadata
    tags TEXT[],
    date_added TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_fiat BOOLEAN DEFAULT FALSE,
    
    -- Data lineage and quality
    source_record_id BIGINT, -- Reference to bronze layer
    data_quality_score NUMERIC(3,2), -- 0.00 to 1.00
    quality_flags TEXT[],
    last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Temporal tracking
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT '9999-12-31'::TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- ETL metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    -- Constraints
    CONSTRAINT chk_supply_positive CHECK (
        (max_supply IS NULL OR max_supply >= 0) AND
        (circulating_supply IS NULL OR circulating_supply >= 0) AND
        (total_supply IS NULL OR total_supply >= 0)
    ),
    CONSTRAINT chk_supply_ratio CHECK (supply_ratio IS NULL OR (supply_ratio >= 0 AND supply_ratio <= 1)),
    CONSTRAINT chk_quality_score CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    CONSTRAINT chk_valid_period CHECK (valid_from <= valid_to),
    CONSTRAINT uq_silver_listings_current UNIQUE (cmc_id, is_current) DEFERRABLE INITIALLY DEFERRED
);

-- Create indexes for efficient querying
CREATE INDEX idx_clean_crypto_listings_symbol ON clean_crypto_listings(symbol);
CREATE INDEX idx_clean_crypto_listings_cmc_id ON clean_crypto_listings(cmc_id);
CREATE INDEX idx_clean_crypto_listings_rank ON clean_crypto_listings(cmc_rank) WHERE cmc_rank IS NOT NULL;
CREATE INDEX idx_clean_crypto_listings_active ON clean_crypto_listings(is_active, is_current);
CREATE INDEX idx_clean_crypto_listings_valid_period ON clean_crypto_listings(valid_from, valid_to);
CREATE INDEX idx_clean_crypto_listings_quality ON clean_crypto_listings(data_quality_score);

-- ================================================================================================
-- 2. CLEANED CRYPTOCURRENCY QUOTES TABLE (HYPERTABLE)
-- ================================================================================================

CREATE TABLE clean_crypto_quotes (
    -- Primary identifiers
    id BIGSERIAL,
    cmc_id INTEGER NOT NULL,
    symbol crypto_symbol NOT NULL,
    
    -- Price data (cleaned and validated)
    price NUMERIC(20,8) NOT NULL,
    price_usd NUMERIC(20,8) NOT NULL, -- Standardized USD price
    
    -- Volume data
    volume_24h NUMERIC(25,8),
    volume_24h_usd NUMERIC(25,8),
    volume_change_24h NUMERIC(10,4),
    
    -- Price change percentages (cleaned)
    percent_change_1h NUMERIC(10,4),
    percent_change_24h NUMERIC(10,4),
    percent_change_7d NUMERIC(10,4),
    percent_change_30d NUMERIC(10,4),
    percent_change_60d NUMERIC(10,4),
    percent_change_90d NUMERIC(10,4),
    
    -- Market capitalization
    market_cap NUMERIC(25,8),
    market_cap_usd NUMERIC(25,8),
    market_cap_dominance NUMERIC(8,4),
    fully_diluted_market_cap NUMERIC(25,8),
    
    -- Additional metrics
    tvl NUMERIC(25,8), -- Total Value Locked
    
    -- Calculated technical indicators
    price_volatility_1h NUMERIC(10,6),
    price_momentum_24h NUMERIC(10,6),
    volume_price_ratio NUMERIC(15,6),
    
    -- Data quality metrics
    data_quality_score NUMERIC(3,2) NOT NULL,
    quality_flags TEXT[],
    outlier_score NUMERIC(5,4), -- Statistical outlier detection
    
    -- Temporal information
    timestamp_utc TIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    
    -- Data lineage
    source_record_id BIGINT, -- Reference to bronze layer
    etl_batch_id UUID,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_silver_quotes_price_positive CHECK (price > 0 AND price_usd > 0),
    CONSTRAINT chk_silver_quotes_volume_nonnegative CHECK (
        (volume_24h IS NULL OR volume_24h >= 0) AND
        (volume_24h_usd IS NULL OR volume_24h_usd >= 0)
    ),
    CONSTRAINT chk_silver_quotes_market_cap_positive CHECK (
        (market_cap IS NULL OR market_cap >= 0) AND
        (market_cap_usd IS NULL OR market_cap_usd >= 0)
    ),
    CONSTRAINT chk_silver_quotes_quality_score CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    CONSTRAINT chk_silver_quotes_dominance CHECK (
        market_cap_dominance IS NULL OR (market_cap_dominance >= 0 AND market_cap_dominance <= 100)
    )
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('clean_crypto_quotes', 'timestamp_utc', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for efficient querying
CREATE INDEX idx_clean_crypto_quotes_symbol_time ON clean_crypto_quotes(symbol, timestamp_utc DESC);
CREATE INDEX idx_clean_crypto_quotes_cmc_id_time ON clean_crypto_quotes(cmc_id, timestamp_utc DESC);
CREATE INDEX idx_clean_crypto_quotes_quality ON clean_crypto_quotes(data_quality_score) WHERE data_quality_score < 0.8;
CREATE INDEX idx_clean_crypto_quotes_price ON clean_crypto_quotes(price_usd);
CREATE INDEX idx_clean_crypto_quotes_volume ON clean_crypto_quotes(volume_24h_usd) WHERE volume_24h_usd IS NOT NULL;
CREATE INDEX idx_clean_crypto_quotes_market_cap ON clean_crypto_quotes(market_cap_usd) WHERE market_cap_usd IS NOT NULL;

-- ================================================================================================
-- 3. CRYPTOCURRENCY EXCHANGE RATES (FOR MULTI-CURRENCY SUPPORT)
-- ================================================================================================

CREATE TABLE currency_exchange_rates (
    id SERIAL PRIMARY KEY,
    
    -- Currency information
    from_currency VARCHAR(10) NOT NULL,
    to_currency VARCHAR(10) NOT NULL,
    exchange_rate NUMERIC(20,8) NOT NULL,
    
    -- Temporal information
    rate_timestamp TIMESTAMP NOT NULL,
    
    -- Data source
    source_provider VARCHAR(50) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT chk_exchange_rate_positive CHECK (exchange_rate > 0),
    CONSTRAINT uq_currency_pair_timestamp UNIQUE (from_currency, to_currency, rate_timestamp)
);

-- Create hypertable for exchange rates
SELECT create_hypertable('currency_exchange_rates', 'rate_timestamp', chunk_time_interval => INTERVAL '1 day');

-- ================================================================================================
-- 4. DATA QUALITY TRACKING TABLE
-- ================================================================================================

CREATE TABLE data_quality_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Target information
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    symbol crypto_symbol,
    
    -- Quality metrics
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15,6),
    metric_threshold NUMERIC(15,6),
    is_passed BOOLEAN NOT NULL,
    
    -- Context
    measurement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    measurement_period_start TIMESTAMP,
    measurement_period_end TIMESTAMP,
    
    -- Details
    details JSONB,
    
    -- ETL metadata
    etl_batch_id UUID
);

CREATE INDEX idx_data_quality_table_metric ON data_quality_metrics(table_name, metric_name, measurement_timestamp DESC);
CREATE INDEX idx_data_quality_symbol ON data_quality_metrics(symbol, measurement_timestamp DESC) WHERE symbol IS NOT NULL;
CREATE INDEX idx_data_quality_failed ON data_quality_metrics(is_passed, measurement_timestamp DESC) WHERE NOT is_passed;

-- ================================================================================================
-- 5. HISTORICAL PRICE SNAPSHOTS (MATERIALIZED FOR PERFORMANCE)
-- ================================================================================================

CREATE TABLE crypto_price_snapshots (
    id SERIAL PRIMARY KEY,
    
    -- Cryptocurrency information
    cmc_id INTEGER NOT NULL,
    symbol crypto_symbol NOT NULL,
    
    -- Snapshot information
    snapshot_timestamp TIMESTAMP NOT NULL,
    snapshot_type VARCHAR(20) NOT NULL, -- 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY'
    
    -- OHLCV data
    open_price NUMERIC(20,8) NOT NULL,
    high_price NUMERIC(20,8) NOT NULL,
    low_price NUMERIC(20,8) NOT NULL,
    close_price NUMERIC(20,8) NOT NULL,
    volume NUMERIC(25,8),
    
    -- Market data
    market_cap_open NUMERIC(25,8),
    market_cap_close NUMERIC(25,8),
    
    -- Statistical measures
    price_volatility NUMERIC(10,6),
    volume_weighted_price NUMERIC(20,8),
    
    -- Calculated metrics
    price_change_abs NUMERIC(20,8),
    price_change_pct NUMERIC(10,4),
    volume_change_pct NUMERIC(10,4),
    
    -- Data quality
    data_points_count INTEGER NOT NULL,
    quality_score NUMERIC(3,2) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT chk_snapshots_ohlc_valid CHECK (
        low_price <= open_price AND low_price <= close_price AND
        high_price >= open_price AND high_price >= close_price AND
        low_price <= high_price
    ),
    CONSTRAINT chk_snapshots_quality CHECK (quality_score >= 0 AND quality_score <= 1),
    CONSTRAINT uq_snapshot_symbol_time_type UNIQUE (symbol, snapshot_timestamp, snapshot_type)
);

-- Convert to hypertable
SELECT create_hypertable('crypto_price_snapshots', 'snapshot_timestamp', chunk_time_interval => INTERVAL '7 days');

-- Create indexes
CREATE INDEX idx_snapshots_symbol_type_time ON crypto_price_snapshots(symbol, snapshot_type, snapshot_timestamp DESC);
CREATE INDEX idx_snapshots_cmc_id_time ON crypto_price_snapshots(cmc_id, snapshot_timestamp DESC);
CREATE INDEX idx_snapshots_type_time ON crypto_price_snapshots(snapshot_type, snapshot_timestamp DESC);

-- ================================================================================================
-- 6. TRIGGER FUNCTIONS FOR AUTOMATIC UPDATES
-- ================================================================================================

-- Function to update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables that need automatic timestamp updates
CREATE TRIGGER tr_clean_crypto_listings_updated_at
    BEFORE UPDATE ON clean_crypto_listings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================================================================
-- 7. DATA RETENTION POLICIES
-- ================================================================================================

-- Retention policy for cleaned quotes (keep 2 years of detailed data)
SELECT add_retention_policy('clean_crypto_quotes', INTERVAL '2 years');

-- Retention policy for price snapshots (keep 5 years)
SELECT add_retention_policy('crypto_price_snapshots', INTERVAL '5 years');

-- Retention policy for exchange rates (keep 1 year)
SELECT add_retention_policy('currency_exchange_rates', INTERVAL '1 year');

-- ================================================================================================
-- 8. TABLE COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON SCHEMA silver IS 'Silver layer containing cleaned, validated, and standardized cryptocurrency data';

COMMENT ON TABLE clean_crypto_listings IS 'Cleaned and validated cryptocurrency listing information with data quality tracking';
COMMENT ON COLUMN clean_crypto_listings.data_quality_score IS 'Quality score from 0.00 to 1.00 based on completeness, accuracy, and consistency';
COMMENT ON COLUMN clean_crypto_listings.quality_flags IS 'Array of quality issues identified during validation';
COMMENT ON COLUMN clean_crypto_listings.supply_ratio IS 'Ratio of circulating supply to max supply (0.0 to 1.0)';

COMMENT ON TABLE clean_crypto_quotes IS 'Cleaned and validated cryptocurrency quote data optimized for time-series analysis';
COMMENT ON COLUMN clean_crypto_quotes.price_usd IS 'Standardized price in USD for consistent cross-currency analysis';
COMMENT ON COLUMN clean_crypto_quotes.outlier_score IS 'Statistical measure of how much this data point deviates from normal patterns';

COMMENT ON TABLE crypto_price_snapshots IS 'Pre-aggregated OHLCV data for different time intervals to improve query performance';
COMMENT ON TABLE data_quality_metrics IS 'Tracking table for data quality measurements and validation results';

-- ================================================================================================
-- GRANT PERMISSIONS
-- ================================================================================================

-- Grant permissions to application roles
-- GRANT SELECT ON ALL TABLES IN SCHEMA silver TO crypto_readonly;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA silver TO crypto_readwrite;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA silver TO crypto_readwrite;

-- ================================================================================================
-- INITIAL DATA VALIDATION SETUP
-- ================================================================================================

-- Insert initial quality thresholds
INSERT INTO data_quality_metrics (table_name, metric_name, metric_threshold, is_passed, details, measurement_timestamp) VALUES
('clean_crypto_quotes', 'minimum_quality_score', 0.8, true, '{"description": "Minimum acceptable quality score for processed quotes"}', CURRENT_TIMESTAMP),
('clean_crypto_quotes', 'maximum_outlier_score', 3.0, true, '{"description": "Maximum outlier score before flagging as suspicious"}', CURRENT_TIMESTAMP),
('clean_crypto_listings', 'minimum_quality_score', 0.9, true, '{"description": "Minimum acceptable quality score for listing data"}', CURRENT_TIMESTAMP);

-- ================================================================================================
-- USAGE EXAMPLES
-- ================================================================================================

/*
-- Example: Query latest cleaned quotes for top 10 cryptocurrencies
SELECT 
    symbol,
    price_usd,
    volume_24h_usd,
    market_cap_usd,
    percent_change_24h,
    data_quality_score
FROM clean_crypto_quotes 
WHERE timestamp_utc = (
    SELECT MAX(timestamp_utc) 
    FROM clean_crypto_quotes
)
ORDER BY market_cap_usd DESC NULLS LAST
LIMIT 10;

-- Example: Get daily OHLCV data for Bitcoin
SELECT 
    snapshot_timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    price_change_pct
FROM crypto_price_snapshots
WHERE symbol = 'BTC'
  AND snapshot_type = 'DAILY'
  AND snapshot_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY snapshot_timestamp DESC;

-- Example: Check data quality for recent quotes
SELECT 
    symbol,
    AVG(data_quality_score) as avg_quality,
    COUNT(*) as record_count,
    COUNT(CASE WHEN array_length(quality_flags, 1) > 0 THEN 1 END) as flagged_records
FROM clean_crypto_quotes
WHERE timestamp_utc >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY symbol
ORDER BY avg_quality DESC;
*/
