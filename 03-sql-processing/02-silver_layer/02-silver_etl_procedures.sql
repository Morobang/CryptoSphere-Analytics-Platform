-- ================================================================================================
-- CryptoSphere Analytics Platform - Silver Layer ETL Procedures
-- ================================================================================================
-- Purpose: ETL procedures to transform and clean data from Bronze to Silver layer
-- Layer: Silver (Cleaned Data)
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- ================================================================================================

SET search_path TO silver, bronze, metadata, public;

-- ================================================================================================
-- 1. DATA QUALITY VALIDATION FUNCTIONS
-- ================================================================================================

-- Function to calculate data quality score for crypto quotes
CREATE OR REPLACE FUNCTION calculate_quote_quality_score(
    p_price NUMERIC,
    p_volume_24h NUMERIC,
    p_market_cap NUMERIC,
    p_percent_change_24h NUMERIC,
    p_last_updated TIMESTAMP,
    p_api_call_timestamp TIMESTAMP
) RETURNS TABLE(
    quality_score NUMERIC,
    quality_flags TEXT[]
) AS $$
DECLARE
    v_score NUMERIC := 1.0;
    v_flags TEXT[] := ARRAY[]::TEXT[];
    v_time_diff_minutes NUMERIC;
BEGIN
    -- Check price validity
    IF p_price IS NULL THEN
        v_score := v_score - 0.4;
        v_flags := array_append(v_flags, 'MISSING_PRICE');
    ELSIF p_price <= 0 THEN
        v_score := v_score - 0.4;
        v_flags := array_append(v_flags, 'INVALID_PRICE');
    END IF;
    
    -- Check volume validity
    IF p_volume_24h IS NULL THEN
        v_score := v_score - 0.2;
        v_flags := array_append(v_flags, 'MISSING_VOLUME');
    ELSIF p_volume_24h < 0 THEN
        v_score := v_score - 0.2;
        v_flags := array_append(v_flags, 'INVALID_VOLUME');
    END IF;
    
    -- Check market cap consistency
    IF p_market_cap IS NULL THEN
        v_score := v_score - 0.1;
        v_flags := array_append(v_flags, 'MISSING_MARKET_CAP');
    ELSIF p_market_cap < 0 THEN
        v_score := v_score - 0.2;
        v_flags := array_append(v_flags, 'INVALID_MARKET_CAP');
    END IF;
    
    -- Check for extreme price changes (potential data error)
    IF p_percent_change_24h IS NOT NULL AND ABS(p_percent_change_24h) > 200 THEN
        v_score := v_score - 0.1;
        v_flags := array_append(v_flags, 'EXTREME_PRICE_CHANGE');
    END IF;
    
    -- Check timestamp freshness
    IF p_last_updated IS NOT NULL AND p_api_call_timestamp IS NOT NULL THEN
        v_time_diff_minutes := EXTRACT(MINUTES FROM (p_api_call_timestamp - p_last_updated));
        IF v_time_diff_minutes > 60 THEN
            v_score := v_score - 0.1;
            v_flags := array_append(v_flags, 'STALE_DATA');
        END IF;
    END IF;
    
    -- Ensure score doesn't go below 0
    v_score := GREATEST(v_score, 0.0);
    
    RETURN QUERY SELECT v_score, v_flags;
END;
$$ LANGUAGE plpgsql;

-- Function to detect statistical outliers using IQR method
CREATE OR REPLACE FUNCTION detect_price_outliers(
    p_symbol crypto_symbol,
    p_price NUMERIC,
    p_lookback_hours INTEGER DEFAULT 24
) RETURNS NUMERIC AS $$
DECLARE
    v_q1 NUMERIC;
    v_q3 NUMERIC;
    v_iqr NUMERIC;
    v_lower_bound NUMERIC;
    v_upper_bound NUMERIC;
    v_outlier_score NUMERIC := 0;
BEGIN
    -- Calculate quartiles for the given symbol over the lookback period
    SELECT 
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price),
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price)
    INTO v_q1, v_q3
    FROM raw_crypto_quotes
    WHERE symbol = p_symbol
      AND price IS NOT NULL
      AND price > 0
      AND api_call_timestamp >= CURRENT_TIMESTAMP - (p_lookback_hours || ' hours')::INTERVAL;
    
    IF v_q1 IS NOT NULL AND v_q3 IS NOT NULL THEN
        v_iqr := v_q3 - v_q1;
        v_lower_bound := v_q1 - (1.5 * v_iqr);
        v_upper_bound := v_q3 + (1.5 * v_iqr);
        
        -- Calculate outlier score (how many IQRs away from normal range)
        IF p_price < v_lower_bound THEN
            v_outlier_score := (v_lower_bound - p_price) / v_iqr;
        ELSIF p_price > v_upper_bound THEN
            v_outlier_score := (p_price - v_upper_bound) / v_iqr;
        END IF;
    END IF;
    
    RETURN v_outlier_score;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 2. BRONZE TO SILVER ETL PROCEDURES
-- ================================================================================================

-- Procedure to process cryptocurrency listings from bronze to silver
CREATE OR REPLACE FUNCTION process_crypto_listings(
    p_batch_id UUID DEFAULT NULL,
    p_full_refresh BOOLEAN DEFAULT FALSE
) RETURNS TABLE(
    processed_count INTEGER,
    quality_issues_count INTEGER,
    status TEXT
) AS $$
DECLARE
    v_processed_count INTEGER := 0;
    v_quality_issues_count INTEGER := 0;
    v_batch_id UUID;
    v_listing_record RECORD;
    v_quality_score NUMERIC;
    v_quality_flags TEXT[];
    v_supply_ratio NUMERIC;
    v_is_fully_diluted BOOLEAN;
BEGIN
    -- Generate batch ID if not provided
    v_batch_id := COALESCE(p_batch_id, uuid_generate_v4());
    
    BEGIN
        -- If full refresh, deactivate all current records
        IF p_full_refresh THEN
            UPDATE clean_crypto_listings 
            SET is_current = FALSE, 
                valid_to = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE is_current = TRUE;
        END IF;
        
        -- Process records from bronze layer
        FOR v_listing_record IN 
            SELECT DISTINCT ON (cmc_id)
                id as source_id,
                cmc_id,
                symbol,
                name,
                slug,
                num_market_pairs,
                cmc_rank,
                max_supply,
                circulating_supply,
                total_supply,
                tags,
                date_added,
                is_active,
                is_fiat,
                etl_batch_id
            FROM raw_crypto_listings
            WHERE (p_batch_id IS NULL OR etl_batch_id = p_batch_id)
            ORDER BY cmc_id, api_call_timestamp DESC
        LOOP
            -- Calculate supply metrics
            v_supply_ratio := NULL;
            v_is_fully_diluted := FALSE;
            
            IF v_listing_record.max_supply IS NOT NULL AND v_listing_record.max_supply > 0 THEN
                IF v_listing_record.circulating_supply IS NOT NULL THEN
                    v_supply_ratio := v_listing_record.circulating_supply / v_listing_record.max_supply;
                    v_is_fully_diluted := (v_supply_ratio >= 0.99);
                END IF;
            ELSE
                v_is_fully_diluted := TRUE; -- No max supply means fully diluted
            END IF;
            
            -- Calculate quality score
            v_quality_score := 1.0;
            v_quality_flags := ARRAY[]::TEXT[];
            
            -- Basic validation
            IF v_listing_record.name IS NULL OR LENGTH(v_listing_record.name) = 0 THEN
                v_quality_score := v_quality_score - 0.2;
                v_quality_flags := array_append(v_quality_flags, 'MISSING_NAME');
            END IF;
            
            IF v_listing_record.symbol IS NULL OR LENGTH(v_listing_record.symbol) = 0 THEN
                v_quality_score := v_quality_score - 0.3;
                v_quality_flags := array_append(v_quality_flags, 'MISSING_SYMBOL');
            END IF;
            
            IF v_listing_record.cmc_rank IS NULL THEN
                v_quality_score := v_quality_score - 0.1;
                v_quality_flags := array_append(v_quality_flags, 'MISSING_RANK');
            END IF;
            
            -- Supply validation
            IF v_listing_record.circulating_supply IS NOT NULL AND v_listing_record.max_supply IS NOT NULL THEN
                IF v_listing_record.circulating_supply > v_listing_record.max_supply THEN
                    v_quality_score := v_quality_score - 0.2;
                    v_quality_flags := array_append(v_quality_flags, 'INVALID_SUPPLY_RATIO');
                END IF;
            END IF;
            
            v_quality_score := GREATEST(v_quality_score, 0.0);
            
            -- Count quality issues
            IF array_length(v_quality_flags, 1) > 0 THEN
                v_quality_issues_count := v_quality_issues_count + 1;
            END IF;
            
            -- Deactivate existing current record if it exists
            UPDATE clean_crypto_listings 
            SET is_current = FALSE, 
                valid_to = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE cmc_id = v_listing_record.cmc_id 
              AND is_current = TRUE;
            
            -- Insert new record
            INSERT INTO clean_crypto_listings (
                cmc_id,
                symbol,
                name,
                slug,
                num_market_pairs,
                cmc_rank,
                max_supply,
                circulating_supply,
                total_supply,
                supply_ratio,
                is_fully_diluted,
                tags,
                date_added,
                is_active,
                is_fiat,
                source_record_id,
                data_quality_score,
                quality_flags,
                etl_batch_id
            ) VALUES (
                v_listing_record.cmc_id,
                v_listing_record.symbol,
                v_listing_record.name,
                v_listing_record.slug,
                v_listing_record.num_market_pairs,
                v_listing_record.cmc_rank,
                v_listing_record.max_supply,
                v_listing_record.circulating_supply,
                v_listing_record.total_supply,
                v_supply_ratio,
                v_is_fully_diluted,
                v_listing_record.tags,
                v_listing_record.date_added,
                v_listing_record.is_active,
                v_listing_record.is_fiat,
                v_listing_record.source_id,
                v_quality_score,
                v_quality_flags,
                v_batch_id
            );
            
            v_processed_count := v_processed_count + 1;
        END LOOP;
        
        -- Log ETL job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            source_schema,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Process Crypto Listings to Silver',
            'ETL_BRONZE_TO_SILVER',
            'SUCCESS',
            'bronze',
            'silver',
            v_processed_count,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_processed_count, v_quality_issues_count, 'SUCCESS'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        -- Log failed job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            source_schema,
            target_schema,
            records_processed,
            error_message,
            end_time
        ) VALUES (
            'Process Crypto Listings to Silver',
            'ETL_BRONZE_TO_SILVER',
            'FAILED',
            'bronze',
            'silver',
            v_processed_count,
            SQLERRM,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_processed_count, v_quality_issues_count, ('FAILED: ' || SQLERRM)::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

-- Procedure to process cryptocurrency quotes from bronze to silver
CREATE OR REPLACE FUNCTION process_crypto_quotes(
    p_batch_id UUID DEFAULT NULL,
    p_lookback_hours INTEGER DEFAULT 1
) RETURNS TABLE(
    processed_count INTEGER,
    quality_issues_count INTEGER,
    outliers_detected INTEGER,
    status TEXT
) AS $$
DECLARE
    v_processed_count INTEGER := 0;
    v_quality_issues_count INTEGER := 0;
    v_outliers_detected INTEGER := 0;
    v_batch_id UUID;
    v_quote_record RECORD;
    v_quality_result RECORD;
    v_outlier_score NUMERIC;
    v_cutoff_time TIMESTAMP;
BEGIN
    -- Generate batch ID if not provided
    v_batch_id := COALESCE(p_batch_id, uuid_generate_v4());
    v_cutoff_time := CURRENT_TIMESTAMP - (p_lookback_hours || ' hours')::INTERVAL;
    
    BEGIN
        -- Process records from bronze layer
        FOR v_quote_record IN 
            SELECT 
                id as source_id,
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
                api_call_timestamp,
                etl_batch_id
            FROM raw_crypto_quotes
            WHERE (p_batch_id IS NULL OR etl_batch_id = p_batch_id)
              AND api_call_timestamp >= v_cutoff_time
              AND price IS NOT NULL
              AND price > 0
        LOOP
            -- Calculate data quality score
            SELECT * INTO v_quality_result
            FROM calculate_quote_quality_score(
                v_quote_record.price,
                v_quote_record.volume_24h,
                v_quote_record.market_cap,
                v_quote_record.percent_change_24h,
                v_quote_record.last_updated,
                v_quote_record.api_call_timestamp
            );
            
            -- Detect outliers
            v_outlier_score := detect_price_outliers(
                v_quote_record.symbol,
                v_quote_record.price,
                24
            );
            
            -- Count quality issues and outliers
            IF array_length(v_quality_result.quality_flags, 1) > 0 THEN
                v_quality_issues_count := v_quality_issues_count + 1;
            END IF;
            
            IF v_outlier_score > 1.5 THEN
                v_outliers_detected := v_outliers_detected + 1;
            END IF;
            
            -- Insert cleaned record
            INSERT INTO clean_crypto_quotes (
                cmc_id,
                symbol,
                price,
                price_usd,
                volume_24h,
                volume_24h_usd,
                volume_change_24h,
                percent_change_1h,
                percent_change_24h,
                percent_change_7d,
                percent_change_30d,
                percent_change_60d,
                percent_change_90d,
                market_cap,
                market_cap_usd,
                market_cap_dominance,
                fully_diluted_market_cap,
                tvl,
                data_quality_score,
                quality_flags,
                outlier_score,
                timestamp_utc,
                last_updated,
                source_record_id,
                etl_batch_id
            ) VALUES (
                v_quote_record.cmc_id,
                v_quote_record.symbol,
                v_quote_record.price,
                v_quote_record.price, -- Assuming input is already in USD
                v_quote_record.volume_24h,
                v_quote_record.volume_24h, -- Assuming input is already in USD
                v_quote_record.volume_change_24h,
                v_quote_record.percent_change_1h,
                v_quote_record.percent_change_24h,
                v_quote_record.percent_change_7d,
                v_quote_record.percent_change_30d,
                v_quote_record.percent_change_60d,
                v_quote_record.percent_change_90d,
                v_quote_record.market_cap,
                v_quote_record.market_cap, -- Assuming input is already in USD
                v_quote_record.market_cap_dominance,
                v_quote_record.fully_diluted_market_cap,
                v_quote_record.tvl,
                v_quality_result.quality_score,
                v_quality_result.quality_flags,
                v_outlier_score,
                v_quote_record.api_call_timestamp,
                v_quote_record.last_updated,
                v_quote_record.source_id,
                v_batch_id
            );
            
            v_processed_count := v_processed_count + 1;
        END LOOP;
        
        -- Log ETL job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            source_schema,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Process Crypto Quotes to Silver',
            'ETL_BRONZE_TO_SILVER',
            'SUCCESS',
            'bronze',
            'silver',
            v_processed_count,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_processed_count, v_quality_issues_count, v_outliers_detected, 'SUCCESS'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        -- Log failed job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            source_schema,
            target_schema,
            records_processed,
            error_message,
            end_time
        ) VALUES (
            'Process Crypto Quotes to Silver',
            'ETL_BRONZE_TO_SILVER',
            'FAILED',
            'bronze',
            'silver',
            v_processed_count,
            SQLERRM,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_processed_count, v_quality_issues_count, v_outliers_detected, ('FAILED: ' || SQLERRM)::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 3. DATA AGGREGATION PROCEDURES
-- ================================================================================================

-- Procedure to generate OHLCV snapshots
CREATE OR REPLACE FUNCTION generate_price_snapshots(
    p_snapshot_type VARCHAR(20), -- 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY'
    p_target_timestamp TIMESTAMP DEFAULT NULL
) RETURNS TABLE(
    generated_count INTEGER,
    status TEXT
) AS $$
DECLARE
    v_generated_count INTEGER := 0;
    v_target_timestamp TIMESTAMP;
    v_interval_start TIMESTAMP;
    v_interval_end TIMESTAMP;
    v_crypto_record RECORD;
    v_batch_id UUID;
BEGIN
    v_batch_id := uuid_generate_v4();
    
    -- Set target timestamp based on snapshot type
    IF p_target_timestamp IS NULL THEN
        CASE p_snapshot_type
            WHEN 'HOURLY' THEN
                v_target_timestamp := DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '1 hour');
            WHEN 'DAILY' THEN
                v_target_timestamp := DATE_TRUNC('day', CURRENT_TIMESTAMP - INTERVAL '1 day');
            WHEN 'WEEKLY' THEN
                v_target_timestamp := DATE_TRUNC('week', CURRENT_TIMESTAMP - INTERVAL '1 week');
            WHEN 'MONTHLY' THEN
                v_target_timestamp := DATE_TRUNC('month', CURRENT_TIMESTAMP - INTERVAL '1 month');
            ELSE
                RAISE EXCEPTION 'Invalid snapshot type: %', p_snapshot_type;
        END CASE;
    ELSE
        v_target_timestamp := p_target_timestamp;
    END IF;
    
    -- Calculate interval boundaries
    CASE p_snapshot_type
        WHEN 'HOURLY' THEN
            v_interval_start := v_target_timestamp;
            v_interval_end := v_target_timestamp + INTERVAL '1 hour';
        WHEN 'DAILY' THEN
            v_interval_start := v_target_timestamp;
            v_interval_end := v_target_timestamp + INTERVAL '1 day';
        WHEN 'WEEKLY' THEN
            v_interval_start := v_target_timestamp;
            v_interval_end := v_target_timestamp + INTERVAL '1 week';
        WHEN 'MONTHLY' THEN
            v_interval_start := v_target_timestamp;
            v_interval_end := v_target_timestamp + INTERVAL '1 month';
    END CASE;
    
    BEGIN
        -- Generate snapshots for each cryptocurrency
        FOR v_crypto_record IN
            SELECT 
                cmc_id,
                symbol,
                FIRST_VALUE(price_usd ORDER BY timestamp_utc) as open_price,
                MAX(price_usd) as high_price,
                MIN(price_usd) as low_price,
                LAST_VALUE(price_usd ORDER BY timestamp_utc) as close_price,
                AVG(volume_24h_usd) as avg_volume,
                FIRST_VALUE(market_cap_usd ORDER BY timestamp_utc) as open_market_cap,
                LAST_VALUE(market_cap_usd ORDER BY timestamp_utc) as close_market_cap,
                STDDEV(price_usd) as price_volatility,
                SUM(price_usd * COALESCE(volume_24h_usd, 0)) / NULLIF(SUM(COALESCE(volume_24h_usd, 0)), 0) as volume_weighted_price,
                COUNT(*) as data_points,
                AVG(data_quality_score) as avg_quality_score
            FROM clean_crypto_quotes
            WHERE timestamp_utc >= v_interval_start
              AND timestamp_utc < v_interval_end
              AND data_quality_score >= 0.7 -- Only use high-quality data
            GROUP BY cmc_id, symbol
            HAVING COUNT(*) >= 1 -- At least 1 data point required
        LOOP
            -- Check if snapshot already exists
            IF NOT EXISTS (
                SELECT 1 FROM crypto_price_snapshots
                WHERE symbol = v_crypto_record.symbol
                  AND snapshot_timestamp = v_target_timestamp
                  AND snapshot_type = p_snapshot_type
            ) THEN
                INSERT INTO crypto_price_snapshots (
                    cmc_id,
                    symbol,
                    snapshot_timestamp,
                    snapshot_type,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    market_cap_open,
                    market_cap_close,
                    price_volatility,
                    volume_weighted_price,
                    price_change_abs,
                    price_change_pct,
                    data_points_count,
                    quality_score,
                    etl_batch_id
                ) VALUES (
                    v_crypto_record.cmc_id,
                    v_crypto_record.symbol,
                    v_target_timestamp,
                    p_snapshot_type,
                    v_crypto_record.open_price,
                    v_crypto_record.high_price,
                    v_crypto_record.low_price,
                    v_crypto_record.close_price,
                    v_crypto_record.avg_volume,
                    v_crypto_record.open_market_cap,
                    v_crypto_record.close_market_cap,
                    v_crypto_record.price_volatility,
                    v_crypto_record.volume_weighted_price,
                    v_crypto_record.close_price - v_crypto_record.open_price,
                    CASE 
                        WHEN v_crypto_record.open_price > 0 THEN
                            (v_crypto_record.close_price - v_crypto_record.open_price) / v_crypto_record.open_price * 100
                        ELSE NULL
                    END,
                    v_crypto_record.data_points,
                    v_crypto_record.avg_quality_score,
                    v_batch_id
                );
                
                v_generated_count := v_generated_count + 1;
            END IF;
        END LOOP;
        
        -- Log ETL job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Generate ' || p_snapshot_type || ' Price Snapshots',
            'DATA_AGGREGATION',
            'SUCCESS',
            'silver',
            v_generated_count,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_generated_count, 'SUCCESS'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        -- Log failed job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            error_message,
            end_time
        ) VALUES (
            'Generate ' || p_snapshot_type || ' Price Snapshots',
            'DATA_AGGREGATION',
            'FAILED',
            'silver',
            v_generated_count,
            SQLERRM,
            CURRENT_TIMESTAMP
        );
        
        RETURN QUERY SELECT v_generated_count, ('FAILED: ' || SQLERRM)::TEXT;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 4. COMPREHENSIVE ETL ORCHESTRATION
-- ================================================================================================

-- Master procedure to run the complete Bronze to Silver ETL process
CREATE OR REPLACE FUNCTION run_bronze_to_silver_etl(
    p_batch_id UUID DEFAULT NULL,
    p_include_snapshots BOOLEAN DEFAULT TRUE
) RETURNS TABLE(
    process_name TEXT,
    records_processed INTEGER,
    status TEXT,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    v_batch_id UUID;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_listings_result RECORD;
    v_quotes_result RECORD;
    v_hourly_snapshots_result RECORD;
    v_daily_snapshots_result RECORD;
BEGIN
    v_batch_id := COALESCE(p_batch_id, uuid_generate_v4());
    
    -- Process crypto listings
    v_start_time := CURRENT_TIMESTAMP;
    SELECT * INTO v_listings_result FROM process_crypto_listings(v_batch_id, FALSE);
    v_end_time := CURRENT_TIMESTAMP;
    
    RETURN QUERY SELECT 
        'Crypto Listings ETL'::TEXT,
        v_listings_result.processed_count,
        v_listings_result.status,
        EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
    
    -- Process crypto quotes
    v_start_time := CURRENT_TIMESTAMP;
    SELECT * INTO v_quotes_result FROM process_crypto_quotes(v_batch_id, 6);
    v_end_time := CURRENT_TIMESTAMP;
    
    RETURN QUERY SELECT 
        'Crypto Quotes ETL'::TEXT,
        v_quotes_result.processed_count,
        v_quotes_result.status,
        EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
    
    -- Generate snapshots if requested
    IF p_include_snapshots THEN
        -- Hourly snapshots
        v_start_time := CURRENT_TIMESTAMP;
        SELECT * INTO v_hourly_snapshots_result FROM generate_price_snapshots('HOURLY');
        v_end_time := CURRENT_TIMESTAMP;
        
        RETURN QUERY SELECT 
            'Hourly Snapshots'::TEXT,
            v_hourly_snapshots_result.generated_count,
            v_hourly_snapshots_result.status,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
        
        -- Daily snapshots (only run once per day)
        IF EXTRACT(HOUR FROM CURRENT_TIMESTAMP) = 0 THEN
            v_start_time := CURRENT_TIMESTAMP;
            SELECT * INTO v_daily_snapshots_result FROM generate_price_snapshots('DAILY');
            v_end_time := CURRENT_TIMESTAMP;
            
            RETURN QUERY SELECT 
                'Daily Snapshots'::TEXT,
                v_daily_snapshots_result.generated_count,
                v_daily_snapshots_result.status,
                EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- GRANT PERMISSIONS
-- ================================================================================================

-- Grant execute permissions to application roles
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA silver TO crypto_readwrite;

-- ================================================================================================
-- USAGE EXAMPLES AND TESTING
-- ================================================================================================

/*
-- Example: Process crypto listings from bronze to silver
SELECT * FROM process_crypto_listings();

-- Example: Process crypto quotes from the last 2 hours
SELECT * FROM process_crypto_quotes(NULL, 2);

-- Example: Generate hourly price snapshots
SELECT * FROM generate_price_snapshots('HOURLY');

-- Example: Run complete ETL pipeline
SELECT * FROM run_bronze_to_silver_etl();

-- Example: Check data quality for a specific symbol
SELECT 
    symbol,
    AVG(data_quality_score) as avg_quality,
    COUNT(*) as total_records,
    COUNT(CASE WHEN array_length(quality_flags, 1) > 0 THEN 1 END) as flagged_records
FROM clean_crypto_quotes
WHERE symbol = 'BTC'
  AND timestamp_utc >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY symbol;

-- Example: Find statistical outliers
SELECT 
    symbol,
    price_usd,
    outlier_score,
    timestamp_utc
FROM clean_crypto_quotes
WHERE outlier_score > 2.0
  AND timestamp_utc >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY outlier_score DESC;
*/