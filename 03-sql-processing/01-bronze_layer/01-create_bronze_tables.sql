-- ================================================================================================
-- CryptoSphere Analytics Platform - Bronze Layer Tables
-- ================================================================================================
-- Purpose: Create tables for raw cryptocurrency data from CoinMarketCap API
-- Layer: Bronze (Raw Data)
-- Author: CryptoSphere Analytics Team  
-- Created: 2025-10-07
-- ================================================================================================

-- Set search path to bronze schema
SET search_path TO bronze, public;

-- ================================================================================================
-- 1. RAW COINMARKETCAP API DATA TABLES
-- ================================================================================================

-- Raw cryptocurrency listings data
CREATE TABLE IF NOT EXISTS raw_crypto_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cmc_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    num_market_pairs INTEGER,
    date_added TIMESTAMP,
    tags TEXT[], -- Array of tags
    max_supply NUMERIC(38,8),
    circulating_supply NUMERIC(38,8),
    total_supply NUMERIC(38,8),
    platform_id INTEGER,
    platform_name VARCHAR(100),
    platform_token_address VARCHAR(255),
    cmc_rank INTEGER,
    last_updated TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_fiat BOOLEAN DEFAULT FALSE,
    -- Metadata fields
    raw_json JSONB, -- Store complete API response
    api_call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw cryptocurrency quotes data (prices, market cap, volume)
CREATE TABLE IF NOT EXISTS raw_crypto_quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cmc_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    price NUMERIC(20,8),
    volume_24h NUMERIC(20,2),
    volume_change_24h NUMERIC(10,4),
    percent_change_1h NUMERIC(10,4),
    percent_change_24h NUMERIC(10,4),
    percent_change_7d NUMERIC(10,4),
    percent_change_30d NUMERIC(10,4),
    percent_change_60d NUMERIC(10,4),
    percent_change_90d NUMERIC(10,4),
    market_cap NUMERIC(20,2),
    market_cap_dominance NUMERIC(10,4),
    fully_diluted_market_cap NUMERIC(20,2),
    tvl NUMERIC(20,2), -- Total Value Locked
    last_updated TIMESTAMP,
    -- Metadata fields
    quote_currency VARCHAR(10) DEFAULT 'USD',
    raw_json JSONB,
    api_call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw historical OHLCV data
CREATE TABLE IF NOT EXISTS raw_crypto_ohlcv (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cmc_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    time_period_start TIMESTAMP NOT NULL,
    time_period_end TIMESTAMP NOT NULL,
    time_open TIMESTAMP,
    time_close TIMESTAMP,
    time_high TIMESTAMP,
    time_low TIMESTAMP,
    price_open NUMERIC(20,8),
    price_high NUMERIC(20,8),
    price_low NUMERIC(20,8),
    price_close NUMERIC(20,8),
    volume_traded NUMERIC(20,2),
    trades_count INTEGER,
    -- Metadata fields
    data_source VARCHAR(50) DEFAULT 'coinmarketcap',
    raw_json JSONB,
    api_call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw market data (global metrics)
CREATE TABLE IF NOT EXISTS raw_market_global (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    active_cryptocurrencies INTEGER,
    total_cryptocurrencies INTEGER,
    active_market_pairs INTEGER,
    active_exchanges INTEGER,
    total_exchanges INTEGER,
    eth_dominance NUMERIC(10,4),
    btc_dominance NUMERIC(10,4),
    eth_dominance_yesterday NUMERIC(10,4),
    btc_dominance_yesterday NUMERIC(10,4),
    eth_dominance_24h_percentage_change NUMERIC(10,4),
    btc_dominance_24h_percentage_change NUMERIC(10,4),
    defi_volume_24h NUMERIC(20,2),
    defi_volume_24h_reported NUMERIC(20,2),
    defi_market_cap NUMERIC(20,2),
    defi_24h_percentage_change NUMERIC(10,4),
    stablecoin_volume_24h NUMERIC(20,2),
    stablecoin_volume_24h_reported NUMERIC(20,2),
    stablecoin_market_cap NUMERIC(20,2),
    stablecoin_24h_percentage_change NUMERIC(10,4),
    derivatives_volume_24h NUMERIC(20,2),
    derivatives_volume_24h_reported NUMERIC(20,2),
    derivatives_24h_percentage_change NUMERIC(10,4),
    quote_currency VARCHAR(10) DEFAULT 'USD',
    total_market_cap NUMERIC(20,2),
    total_volume_24h NUMERIC(20,2),
    total_volume_24h_reported NUMERIC(20,2),
    altcoin_volume_24h NUMERIC(20,2),
    altcoin_volume_24h_reported NUMERIC(20,2),
    altcoin_market_cap NUMERIC(20,2),
    last_updated TIMESTAMP,
    -- Metadata fields
    raw_json JSONB,
    api_call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================================================
-- 2. CREATE HYPERTABLES FOR TIME SERIES DATA (TimescaleDB)
-- ================================================================================================

-- Convert quotes table to hypertable for time-series optimization
SELECT create_hypertable('raw_crypto_quotes', 'api_call_timestamp', if_not_exists => TRUE);

-- Convert OHLCV table to hypertable
SELECT create_hypertable('raw_crypto_ohlcv', 'time_period_start', if_not_exists => TRUE);

-- Convert global market data to hypertable
SELECT create_hypertable('raw_market_global', 'api_call_timestamp', if_not_exists => TRUE);

-- ================================================================================================
-- 3. CREATE INDEXES FOR PERFORMANCE
-- ================================================================================================

-- Indexes for raw_crypto_listings
CREATE INDEX IF NOT EXISTS idx_raw_listings_cmc_id ON raw_crypto_listings(cmc_id);
CREATE INDEX IF NOT EXISTS idx_raw_listings_symbol ON raw_crypto_listings(symbol);
CREATE INDEX IF NOT EXISTS idx_raw_listings_rank ON raw_crypto_listings(cmc_rank);
CREATE INDEX IF NOT EXISTS idx_raw_listings_active ON raw_crypto_listings(is_active);
CREATE INDEX IF NOT EXISTS idx_raw_listings_batch ON raw_crypto_listings(etl_batch_id);

-- Indexes for raw_crypto_quotes
CREATE INDEX IF NOT EXISTS idx_raw_quotes_cmc_id ON raw_crypto_quotes(cmc_id);
CREATE INDEX IF NOT EXISTS idx_raw_quotes_symbol ON raw_crypto_quotes(symbol);
CREATE INDEX IF NOT EXISTS idx_raw_quotes_timestamp ON raw_crypto_quotes(api_call_timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_quotes_batch ON raw_crypto_quotes(etl_batch_id);
CREATE INDEX IF NOT EXISTS idx_raw_quotes_last_updated ON raw_crypto_quotes(last_updated);

-- Indexes for raw_crypto_ohlcv
CREATE INDEX IF NOT EXISTS idx_raw_ohlcv_cmc_id ON raw_crypto_ohlcv(cmc_id);
CREATE INDEX IF NOT EXISTS idx_raw_ohlcv_symbol ON raw_crypto_ohlcv(symbol);
CREATE INDEX IF NOT EXISTS idx_raw_ohlcv_period_start ON raw_crypto_ohlcv(time_period_start);
CREATE INDEX IF NOT EXISTS idx_raw_ohlcv_period_end ON raw_crypto_ohlcv(time_period_end);
CREATE INDEX IF NOT EXISTS idx_raw_ohlcv_batch ON raw_crypto_ohlcv(etl_batch_id);

-- Indexes for raw_market_global
CREATE INDEX IF NOT EXISTS idx_raw_global_timestamp ON raw_market_global(api_call_timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_global_last_updated ON raw_market_global(last_updated);
CREATE INDEX IF NOT EXISTS idx_raw_global_batch ON raw_market_global(etl_batch_id);

-- ================================================================================================
-- 4. CREATE PARTITIONS FOR LARGE TABLES (Optional)
-- ================================================================================================

-- Partition raw_crypto_quotes by month for better performance
-- This is handled automatically by TimescaleDB hypertables

-- ================================================================================================
-- 5. DATA RETENTION POLICIES
-- ================================================================================================

-- Set retention policy for raw quotes data (keep for 2 years)
SELECT add_retention_policy('raw_crypto_quotes', INTERVAL '2 years', if_not_exists => TRUE);

-- Set retention policy for OHLCV data (keep for 5 years)
SELECT add_retention_policy('raw_crypto_ohlcv', INTERVAL '5 years', if_not_exists => TRUE);

-- Set retention policy for global market data (keep for 2 years)
SELECT add_retention_policy('raw_market_global', INTERVAL '2 years', if_not_exists => TRUE);

-- ================================================================================================
-- 6. CREATE TRIGGERS FOR AUDIT AND VALIDATION
-- ================================================================================================

-- Function to validate incoming data
CREATE OR REPLACE FUNCTION validate_crypto_quote()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate price is positive
    IF NEW.price IS NOT NULL AND NEW.price <= 0 THEN
        RAISE EXCEPTION 'Invalid price: %', NEW.price;
    END IF;
    
    -- Validate market cap is not negative
    IF NEW.market_cap IS NOT NULL AND NEW.market_cap < 0 THEN
        RAISE EXCEPTION 'Invalid market cap: %', NEW.market_cap;
    END IF;
    
    -- Validate volume is not negative
    IF NEW.volume_24h IS NOT NULL AND NEW.volume_24h < 0 THEN
        RAISE EXCEPTION 'Invalid volume: %', NEW.volume_24h;
    END IF;
    
    -- Set last_updated if not provided
    IF NEW.last_updated IS NULL THEN
        NEW.last_updated := CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for quote validation
CREATE TRIGGER validate_quote_data
    BEFORE INSERT OR UPDATE ON raw_crypto_quotes
    FOR EACH ROW
    EXECUTE FUNCTION validate_crypto_quote();

-- ================================================================================================
-- 7. CREATE VIEWS FOR EASY ACCESS
-- ================================================================================================

-- Latest quotes view
CREATE OR REPLACE VIEW latest_crypto_quotes AS
SELECT DISTINCT ON (cmc_id)
    cmc_id,
    symbol,
    price,
    volume_24h,
    percent_change_24h,
    market_cap,
    market_cap_dominance,
    last_updated
FROM raw_crypto_quotes
ORDER BY cmc_id, last_updated DESC;

-- Latest listings view
CREATE OR REPLACE VIEW latest_crypto_listings AS
SELECT DISTINCT ON (cmc_id)
    cmc_id,
    symbol,
    name,
    cmc_rank,
    circulating_supply,
    total_supply,
    max_supply,
    last_updated
FROM raw_crypto_listings
ORDER BY cmc_id, last_updated DESC;

-- ================================================================================================
-- 8. GRANT PERMISSIONS
-- ================================================================================================

-- Grant permissions to application roles
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA bronze TO crypto_readwrite;
-- GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO crypto_readonly;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA bronze TO crypto_readwrite;

-- ================================================================================================
-- 9. LOG TABLE CREATION
-- ================================================================================================

-- Log the bronze layer creation
INSERT INTO metadata.etl_jobs (
    job_name,
    job_type,
    status,
    target_schema,
    end_time,
    records_processed
) VALUES (
    'Bronze Layer Table Creation',
    'SCHEMA_CREATION',
    'SUCCESS',
    'bronze',
    CURRENT_TIMESTAMP,
    0
);

-- Display creation summary
SELECT 
    'Bronze Layer Tables Created Successfully!' as message,
    schemaname,
    tablename,
    CASE 
        WHEN tablename LIKE 'raw_%' THEN 'Data Table'
        ELSE 'View/Other'
    END as table_type
FROM pg_tables 
WHERE schemaname = 'bronze'
ORDER BY tablename;

-- ================================================================================================
-- NOTES:
-- 1. All tables include raw_json field to store complete API responses
-- 2. ETL batch tracking for data lineage
-- 3. TimescaleDB hypertables for time-series optimization
-- 4. Automatic data validation via triggers
-- 5. Retention policies to manage storage
-- 6. Comprehensive indexing for query performance
-- ================================================================================================
