-- ================================================================================================
-- CryptoSphere Analytics Platform - Bronze Layer Data Ingestion Procedures
-- ================================================================================================
-- Purpose: Stored procedures for ingesting raw cryptocurrency data
-- Layer: Bronze (Raw Data)
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- ================================================================================================

SET search_path TO bronze, metadata, public;

-- ================================================================================================
-- 1. BULK INSERT PROCEDURES FOR API DATA
-- ================================================================================================

-- Procedure to insert cryptocurrency listings data
CREATE OR REPLACE FUNCTION insert_crypto_listings_batch(
    p_listings_data JSONB,
    p_batch_id UUID DEFAULT uuid_generate_v4()
) RETURNS TABLE(
    inserted_count INTEGER,
    batch_id UUID,
    status TEXT
) AS $$
DECLARE
    v_insert_count INTEGER := 0;
    v_listing_record JSONB;
BEGIN
    -- Start transaction
    BEGIN
        -- Loop through each listing in the JSON array
        FOR v_listing_record IN SELECT jsonb_array_elements(p_listings_data->'data')
        LOOP
            INSERT INTO raw_crypto_listings (
                cmc_id,
                symbol,
                name,
                slug,
                num_market_pairs,
                date_added,
                tags,
                max_supply,
                circulating_supply,
                total_supply,
                cmc_rank,
                last_updated,
                is_active,
                is_fiat,
                raw_json,
                etl_batch_id
            ) VALUES (
                (v_listing_record->>'id')::INTEGER,
                v_listing_record->>'symbol',
                v_listing_record->>'name',
                v_listing_record->>'slug',
                (v_listing_record->>'num_market_pairs')::INTEGER,
                (v_listing_record->>'date_added')::TIMESTAMP,
                ARRAY(SELECT jsonb_array_elements_text(v_listing_record->'tags')),
                (v_listing_record->>'max_supply')::NUMERIC,
                (v_listing_record->>'circulating_supply')::NUMERIC,
                (v_listing_record->>'total_supply')::NUMERIC,
                (v_listing_record->'cmc_rank')::INTEGER,
                (v_listing_record->>'last_updated')::TIMESTAMP,
                COALESCE((v_listing_record->>'is_active')::BOOLEAN, TRUE),
                COALESCE((v_listing_record->>'is_fiat')::BOOLEAN, FALSE),
                v_listing_record,
                p_batch_id
            );
            
            v_insert_count := v_insert_count + 1;
        END LOOP;
        
        -- Log successful batch
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Crypto Listings Batch Insert',
            'DATA_INGESTION',
            'SUCCESS',
            'bronze',
            v_insert_count,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_insert_count, p_batch_id, 'SUCCESS'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        -- Log failed batch
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            error_message,
            end_time
        ) VALUES (
            'Crypto Listings Batch Insert',
            'DATA_INGESTION',
            'FAILED',
            'bronze',
            v_insert_count,
            SQLERRM,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_insert_count, p_batch_id, ('FAILED: ' || SQLERRM)::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

-- Procedure to insert cryptocurrency quotes data
CREATE OR REPLACE FUNCTION insert_crypto_quotes_batch(
    p_quotes_data JSONB,
    p_batch_id UUID DEFAULT uuid_generate_v4()
) RETURNS TABLE(
    inserted_count INTEGER,
    batch_id UUID,
    status TEXT
) AS $$
DECLARE
    v_insert_count INTEGER := 0;
    v_quote_record JSONB;
    v_usd_quote JSONB;
BEGIN
    BEGIN
        -- Loop through each quote in the JSON array
        FOR v_quote_record IN SELECT jsonb_array_elements(p_quotes_data->'data')
        LOOP
            -- Extract USD quote data
            v_usd_quote := v_quote_record->'quote'->'USD';
            
            INSERT INTO raw_crypto_quotes (
                cmc_id,
                symbol,
                price,
                volume_24h,
                volume_change_24h,
                percent_change_1h,
                percent_change_24h,
                percent_change_7d,
                percent_change_30d,
                percent_change_60d,
                percent_change_90d,
                market_cap,
                market_cap_dominance,
                fully_diluted_market_cap,
                tvl,
                last_updated,
                raw_json,
                etl_batch_id
            ) VALUES (
                (v_quote_record->>'id')::INTEGER,
                v_quote_record->>'symbol',
                (v_usd_quote->>'price')::NUMERIC,
                (v_usd_quote->>'volume_24h')::NUMERIC,
                (v_usd_quote->>'volume_change_24h')::NUMERIC,
                (v_usd_quote->>'percent_change_1h')::NUMERIC,
                (v_usd_quote->>'percent_change_24h')::NUMERIC,
                (v_usd_quote->>'percent_change_7d')::NUMERIC,
                (v_usd_quote->>'percent_change_30d')::NUMERIC,
                (v_usd_quote->>'percent_change_60d')::NUMERIC,
                (v_usd_quote->>'percent_change_90d')::NUMERIC,
                (v_usd_quote->>'market_cap')::NUMERIC,
                (v_usd_quote->>'market_cap_dominance')::NUMERIC,
                (v_usd_quote->>'fully_diluted_market_cap')::NUMERIC,
                (v_usd_quote->>'tvl')::NUMERIC,
                (v_usd_quote->>'last_updated')::TIMESTAMP,
                v_quote_record,
                p_batch_id
            );
            
            v_insert_count := v_insert_count + 1;
        END LOOP;
        
        -- Log successful batch
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Crypto Quotes Batch Insert',
            'DATA_INGESTION',
            'SUCCESS',
            'bronze',
            v_insert_count,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_insert_count, p_batch_id, 'SUCCESS'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            error_message,
            end_time
        ) VALUES (
            'Crypto Quotes Batch Insert',
            'DATA_INGESTION',
            'FAILED',
            'bronze',
            v_insert_count,
            SQLERRM,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_insert_count, p_batch_id, ('FAILED: ' || SQLERRM)::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 2. DATA CLEANUP PROCEDURES
-- ================================================================================================

-- Procedure to remove duplicate records
CREATE OR REPLACE FUNCTION cleanup_duplicate_quotes(
    p_lookback_hours INTEGER DEFAULT 24
) RETURNS TABLE(
    deleted_count INTEGER,
    status TEXT
) AS $$
DECLARE
    v_deleted_count INTEGER := 0;
    v_cutoff_time TIMESTAMP;
BEGIN
    v_cutoff_time := CURRENT_TIMESTAMP - (p_lookback_hours || ' hours')::INTERVAL;
    
    -- Delete duplicate quotes keeping the latest one for each cmc_id
    WITH duplicates AS (
        SELECT id
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY cmc_id, DATE_TRUNC('minute', api_call_timestamp)
                       ORDER BY api_call_timestamp DESC
                   ) as rn
            FROM raw_crypto_quotes
            WHERE api_call_timestamp >= v_cutoff_time
        ) ranked
        WHERE rn > 1
    )
    DELETE FROM raw_crypto_quotes
    WHERE id IN (SELECT id FROM duplicates);
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    -- Log cleanup operation
    INSERT INTO etl_jobs (
        job_name,
        job_type,
        status,
        target_schema,
        records_processed,
        end_time
    ) VALUES (
        'Cleanup Duplicate Quotes',
        'DATA_CLEANUP',
        'SUCCESS',
        'bronze',
        v_deleted_count,
        CURRENT_TIMESTAMP
    );
    
    RETURN QUERY SELECT v_deleted_count, 'SUCCESS'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 3. DATA VALIDATION PROCEDURES
-- ================================================================================================

-- Procedure to validate data quality in bronze layer
CREATE OR REPLACE FUNCTION validate_bronze_data_quality()
RETURNS TABLE(
    table_name TEXT,
    validation_type TEXT,
    validation_result TEXT,
    record_count INTEGER,
    validation_timestamp TIMESTAMP
) AS $$
BEGIN
    -- Validate quotes data
    RETURN QUERY
    SELECT 
        'raw_crypto_quotes'::TEXT as table_name,
        'null_prices'::TEXT as validation_type,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END as validation_result,
        COUNT(*)::INTEGER as record_count,
        CURRENT_TIMESTAMP as validation_timestamp
    FROM raw_crypto_quotes
    WHERE price IS NULL
      AND api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    -- Validate negative prices
    RETURN QUERY
    SELECT 
        'raw_crypto_quotes'::TEXT,
        'negative_prices'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END,
        COUNT(*)::INTEGER,
        CURRENT_TIMESTAMP
    FROM raw_crypto_quotes
    WHERE price < 0
      AND api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    -- Validate extreme price changes (>1000% in 1 hour)
    RETURN QUERY
    WITH price_changes AS (
        SELECT 
            cmc_id,
            price,
            LAG(price) OVER (PARTITION BY cmc_id ORDER BY api_call_timestamp) as prev_price
        FROM raw_crypto_quotes
        WHERE api_call_timestamp >= CURRENT_TIMESTAMP - INTERVAL '2 hours'
    )
    SELECT 
        'raw_crypto_quotes'::TEXT,
        'extreme_price_changes'::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'SUSPICIOUS'
        END,
        COUNT(*)::INTEGER,
        CURRENT_TIMESTAMP
    FROM price_changes
    WHERE prev_price IS NOT NULL
      AND prev_price > 0
      AND ABS((price - prev_price) / prev_price) > 10; -- 1000% change
    
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 4. API TRACKING PROCEDURES
-- ================================================================================================

-- Procedure to log API calls
CREATE OR REPLACE FUNCTION log_api_call(
    p_api_name VARCHAR(50),
    p_endpoint VARCHAR(200),
    p_http_status INTEGER,
    p_response_time_ms INTEGER,
    p_records_returned INTEGER,
    p_rate_limit_remaining INTEGER DEFAULT NULL,
    p_cost_credits INTEGER DEFAULT 1
) RETURNS UUID AS $$
DECLARE
    v_call_id UUID;
BEGIN
    INSERT INTO api_calls (
        api_name,
        endpoint,
        http_status,
        response_time_ms,
        records_returned,
        rate_limit_remaining,
        cost_credits
    ) VALUES (
        p_api_name,
        p_endpoint,
        p_http_status,
        p_response_time_ms,
        p_records_returned,
        p_rate_limit_remaining,
        p_cost_credits
    ) RETURNING call_id INTO v_call_id;
    
    RETURN v_call_id;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 5. UTILITY FUNCTIONS
-- ================================================================================================

-- Function to get latest data timestamp for a cryptocurrency
CREATE OR REPLACE FUNCTION get_latest_data_timestamp(p_symbol VARCHAR(10))
RETURNS TIMESTAMP AS $$
DECLARE
    v_latest_timestamp TIMESTAMP;
BEGIN
    SELECT MAX(last_updated)
    INTO v_latest_timestamp
    FROM raw_crypto_quotes
    WHERE symbol = p_symbol;
    
    RETURN COALESCE(v_latest_timestamp, '1970-01-01'::TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

-- Function to get data coverage statistics
CREATE OR REPLACE FUNCTION get_data_coverage_stats()
RETURNS TABLE(
    symbol VARCHAR(10),
    first_record TIMESTAMP,
    latest_record TIMESTAMP,
    total_records BIGINT,
    avg_records_per_day NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        q.symbol,
        MIN(q.api_call_timestamp) as first_record,
        MAX(q.api_call_timestamp) as latest_record,
        COUNT(*) as total_records,
        CASE 
            WHEN MIN(q.api_call_timestamp) = MAX(q.api_call_timestamp) THEN 0
            ELSE COUNT(*)::NUMERIC / EXTRACT(DAYS FROM (MAX(q.api_call_timestamp) - MIN(q.api_call_timestamp)))
        END as avg_records_per_day
    FROM raw_crypto_quotes q
    GROUP BY q.symbol
    ORDER BY latest_record DESC;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- GRANT PERMISSIONS
-- ================================================================================================

-- Grant execute permissions to application roles
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA bronze TO crypto_readwrite;

-- ================================================================================================
-- USAGE EXAMPLES
-- ================================================================================================

/*
-- Example: Insert cryptocurrency listings from API response
SELECT * FROM insert_crypto_listings_batch(
    '{"data": [{"id": 1, "symbol": "BTC", "name": "Bitcoin", ...}]}'::JSONB
);

-- Example: Insert cryptocurrency quotes from API response  
SELECT * FROM insert_crypto_quotes_batch(
    '{"data": [{"id": 1, "symbol": "BTC", "quote": {"USD": {"price": 50000, ...}}}]}'::JSONB
);

-- Example: Clean up duplicate records
SELECT * FROM cleanup_duplicate_quotes(24);

-- Example: Validate data quality
SELECT * FROM validate_bronze_data_quality();

-- Example: Log an API call
SELECT log_api_call('coinmarketcap', '/v1/cryptocurrency/listings/latest', 200, 500, 100, 332, 1);

-- Example: Get latest timestamp for Bitcoin
SELECT get_latest_data_timestamp('BTC');

-- Example: Get data coverage statistics
SELECT * FROM get_data_coverage_stats();
*/