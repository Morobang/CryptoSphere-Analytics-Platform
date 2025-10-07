-- ================================================================================================
-- CryptoSphere Analytics Platform - Database Schema Setup
-- ================================================================================================
-- Purpose: Initialize the database structure for cryptocurrency analytics
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- Database: PostgreSQL (adaptable to other databases)
-- ================================================================================================

-- Create main database (uncomment if creating new database)
-- CREATE DATABASE cryptosphere_analytics;
-- \c cryptosphere_analytics;

-- ================================================================================================
-- 1. CREATE SCHEMAS FOR MEDALLION ARCHITECTURE
-- ================================================================================================

-- Bronze Layer: Raw data from APIs
CREATE SCHEMA IF NOT EXISTS bronze
    COMMENT = 'Bronze layer - Raw data from CoinMarketCap API and other sources';

-- Silver Layer: Cleaned and validated data
CREATE SCHEMA IF NOT EXISTS silver
    COMMENT = 'Silver layer - Cleaned, validated, and normalized cryptocurrency data';

-- Gold Layer: Business-ready data marts
CREATE SCHEMA IF NOT EXISTS gold
    COMMENT = 'Gold layer - Business-ready data marts and aggregated analytics';

-- Staging Schema: Temporary data processing
CREATE SCHEMA IF NOT EXISTS staging
    COMMENT = 'Staging area for ETL processes and data transformations';

-- Metadata Schema: System metadata and logging
CREATE SCHEMA IF NOT EXISTS metadata
    COMMENT = 'Metadata schema for ETL logs, data lineage, and system information';

-- ================================================================================================
-- 2. CREATE EXTENSIONS (PostgreSQL specific)
-- ================================================================================================

-- UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Time series extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- JSON processing extensions
CREATE EXTENSION IF NOT EXISTS "hstore";

-- ================================================================================================
-- 3. CREATE CUSTOM DATA TYPES
-- ================================================================================================

-- Cryptocurrency symbol type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'crypto_symbol') THEN
        CREATE TYPE crypto_symbol AS ENUM (
            'BTC', 'ETH', 'ADA', 'DOT', 'BNB', 'XRP', 
            'SOL', 'DOGE', 'MATIC', 'AVAX', 'LINK', 'UNI'
        );
    END IF;
END $$;

-- Data quality status type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'quality_status') THEN
        CREATE TYPE quality_status AS ENUM (
            'VALID', 'INVALID', 'SUSPICIOUS', 'MISSING', 'CORRECTED'
        );
    END IF;
END $$;

-- ETL job status type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
        CREATE TYPE job_status AS ENUM (
            'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED'
        );
    END IF;
END $$;

-- ================================================================================================
-- 4. CREATE UTILITY FUNCTIONS
-- ================================================================================================

-- Function to calculate percentage change
CREATE OR REPLACE FUNCTION calculate_percentage_change(
    old_value NUMERIC,
    new_value NUMERIC
) RETURNS NUMERIC AS $$
BEGIN
    IF old_value IS NULL OR old_value = 0 THEN
        RETURN NULL;
    END IF;
    RETURN ((new_value - old_value) / old_value) * 100;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to validate cryptocurrency data
CREATE OR REPLACE FUNCTION validate_crypto_data(
    symbol TEXT,
    price NUMERIC,
    volume NUMERIC,
    market_cap NUMERIC
) RETURNS quality_status AS $$
BEGIN
    -- Check for null or negative values
    IF symbol IS NULL OR price IS NULL OR price <= 0 THEN
        RETURN 'INVALID';
    END IF;
    
    -- Check for suspicious values
    IF volume IS NOT NULL AND volume < 0 THEN
        RETURN 'SUSPICIOUS';
    END IF;
    
    IF market_cap IS NOT NULL AND market_cap < 0 THEN
        RETURN 'SUSPICIOUS';
    END IF;
    
    -- Check for extremely high price changes (potential data errors)
    -- This would need historical data comparison in practice
    
    RETURN 'VALID';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ================================================================================================
-- 5. CREATE METADATA TABLES
-- ================================================================================================

-- ETL job tracking
CREATE TABLE IF NOT EXISTS metadata.etl_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status job_status DEFAULT 'PENDING',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    source_schema VARCHAR(50),
    target_schema VARCHAR(50),
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    created_by VARCHAR(100) DEFAULT CURRENT_USER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data lineage tracking
CREATE TABLE IF NOT EXISTS metadata.data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_table VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    transformation_type VARCHAR(50) NOT NULL,
    job_id UUID REFERENCES metadata.etl_jobs(job_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality metrics
CREATE TABLE IF NOT EXISTS metadata.data_quality_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    metric_type VARCHAR(50) NOT NULL, -- 'completeness', 'accuracy', 'consistency', etc.
    metric_value NUMERIC,
    measurement_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API call tracking
CREATE TABLE IF NOT EXISTS metadata.api_calls (
    call_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_name VARCHAR(50) NOT NULL, -- 'coinmarketcap', 'coingecko', etc.
    endpoint VARCHAR(200) NOT NULL,
    http_status INTEGER,
    response_time_ms INTEGER,
    records_returned INTEGER,
    call_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rate_limit_remaining INTEGER,
    cost_credits INTEGER DEFAULT 1
);

-- ================================================================================================
-- 6. CREATE INDEXES FOR METADATA TABLES
-- ================================================================================================

CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON metadata.etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_start_time ON metadata.etl_jobs(start_time);
CREATE INDEX IF NOT EXISTS idx_data_lineage_source ON metadata.data_lineage(source_table);
CREATE INDEX IF NOT EXISTS idx_data_lineage_target ON metadata.data_lineage(target_table);
CREATE INDEX IF NOT EXISTS idx_data_quality_table ON metadata.data_quality_metrics(table_name);
CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON metadata.api_calls(call_timestamp);
CREATE INDEX IF NOT EXISTS idx_api_calls_api_name ON metadata.api_calls(api_name);

-- ================================================================================================
-- 7. GRANT PERMISSIONS
-- ================================================================================================

-- Create roles (uncomment if needed)
-- CREATE ROLE crypto_readonly;
-- CREATE ROLE crypto_readwrite;
-- CREATE ROLE crypto_admin;

-- Grant schema permissions
-- GRANT USAGE ON SCHEMA bronze TO crypto_readonly, crypto_readwrite, crypto_admin;
-- GRANT USAGE ON SCHEMA silver TO crypto_readonly, crypto_readwrite, crypto_admin;
-- GRANT USAGE ON SCHEMA gold TO crypto_readonly, crypto_readwrite, crypto_admin;
-- GRANT USAGE ON SCHEMA metadata TO crypto_admin;

-- Grant table permissions
-- GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO crypto_readonly, crypto_readwrite;
-- GRANT SELECT ON ALL TABLES IN SCHEMA silver TO crypto_readonly, crypto_readwrite;
-- GRANT SELECT ON ALL TABLES IN SCHEMA gold TO crypto_readonly, crypto_readwrite;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bronze TO crypto_readwrite;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA silver TO crypto_readwrite;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gold TO crypto_readwrite;

-- ================================================================================================
-- 8. INITIAL CONFIGURATION DATA
-- ================================================================================================

-- Insert supported cryptocurrencies
CREATE TABLE IF NOT EXISTS metadata.supported_cryptocurrencies (
    symbol crypto_symbol PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    coinmarketcap_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    added_date DATE DEFAULT CURRENT_DATE,
    description TEXT
);

-- Insert initial cryptocurrency data
INSERT INTO metadata.supported_cryptocurrencies (symbol, name, coinmarketcap_id, description) VALUES
    ('BTC', 'Bitcoin', 1, 'The first and largest cryptocurrency by market cap'),
    ('ETH', 'Ethereum', 1027, 'Smart contract platform and second-largest cryptocurrency'),
    ('ADA', 'Cardano', 2010, 'Proof-of-stake blockchain platform'),
    ('DOT', 'Polkadot', 6636, 'Multi-chain protocol for interoperability'),
    ('BNB', 'Binance Coin', 1839, 'Native token of Binance exchange'),
    ('XRP', 'XRP', 52, 'Digital payment protocol'),
    ('SOL', 'Solana', 5426, 'High-performance blockchain'),
    ('DOGE', 'Dogecoin', 74, 'Meme cryptocurrency with strong community'),
    ('MATIC', 'Polygon', 3890, 'Ethereum scaling solution'),
    ('AVAX', 'Avalanche', 5805, 'Smart contracts platform')
ON CONFLICT (symbol) DO NOTHING;

-- ================================================================================================
-- SETUP COMPLETE
-- ================================================================================================

-- Log setup completion
INSERT INTO metadata.etl_jobs (
    job_name, 
    job_type, 
    status, 
    end_time,
    records_processed
) VALUES (
    'Initial Schema Setup',
    'SCHEMA_CREATION',
    'SUCCESS',
    CURRENT_TIMESTAMP,
    (SELECT COUNT(*) FROM metadata.supported_cryptocurrencies)
);

-- Display setup summary
SELECT 
    'CryptoSphere Analytics Database Setup Complete!' as message,
    CURRENT_TIMESTAMP as setup_time,
    COUNT(*) as cryptocurrencies_loaded
FROM metadata.supported_cryptocurrencies;

-- ================================================================================================
-- NOTES:
-- 1. This script is designed for PostgreSQL but can be adapted for other databases
-- 2. Uncomment permission grants if using role-based security
-- 3. Adjust cryptocurrency list based on your analysis requirements
-- 4. Consider enabling TimescaleDB for time-series data if using PostgreSQL
-- ================================================================================================