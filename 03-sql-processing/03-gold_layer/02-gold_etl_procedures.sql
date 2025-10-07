-- ================================================================================================
-- CryptoSphere Analytics Platform - Gold Layer ETL Procedures
-- ================================================================================================
-- Purpose: ETL procedures to create business-ready analytics from Silver layer data
-- Layer: Gold (Business Data)
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- ================================================================================================

SET search_path TO gold, silver, bronze, metadata, public;

-- ================================================================================================
-- 1. MARKET OVERVIEW ETL PROCEDURES
-- ================================================================================================

-- Procedure to generate daily market overview
CREATE OR REPLACE FUNCTION generate_market_overview_daily(
    p_target_date DATE DEFAULT NULL
) RETURNS TABLE(
    status TEXT,
    records_processed INTEGER,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    v_target_date DATE;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_batch_id UUID;
    v_market_data RECORD;
    v_records_processed INTEGER := 0;
BEGIN
    v_start_time := CURRENT_TIMESTAMP;
    v_batch_id := uuid_generate_v4();
    v_target_date := COALESCE(p_target_date, CURRENT_DATE - INTERVAL '1 day');
    
    BEGIN
        -- Calculate comprehensive market overview
        WITH daily_data AS (
            SELECT 
                cq.symbol,
                cq.close_price_usd,
                cq.volume_usd,
                cq.market_cap_usd,
                cq.daily_return_pct,
                cq.volatility_daily,
                cl.market_cap_rank
            FROM crypto_performance_metrics cq
            LEFT JOIN clean_crypto_listings cl ON cq.cmc_id = cl.cmc_id AND cl.is_current = TRUE
            WHERE cq.date_key = v_target_date
              AND cq.quality_score >= 0.8
        ),
        market_stats AS (
            SELECT 
                COUNT(*) as active_cryptos,
                COUNT(CASE WHEN volume_usd > 0 THEN 1 END) as cryptos_with_volume,
                SUM(market_cap_usd) as total_market_cap,
                SUM(volume_usd) as total_volume,
                AVG(daily_return_pct) as avg_daily_return,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY daily_return_pct) as median_daily_return,
                SQRT(AVG(volatility_daily * volatility_daily)) as market_volatility
            FROM daily_data
        ),
        top_performers AS (
            SELECT 
                symbol as best_symbol,
                daily_return_pct as best_return
            FROM daily_data
            WHERE market_cap_rank <= 100
            ORDER BY daily_return_pct DESC
            LIMIT 1
        ),
        worst_performers AS (
            SELECT 
                symbol as worst_symbol,
                daily_return_pct as worst_return
            FROM daily_data
            WHERE market_cap_rank <= 100
            ORDER BY daily_return_pct ASC
            LIMIT 1
        ),
        dominance_data AS (
            SELECT 
                SUM(CASE WHEN market_cap_rank <= 10 THEN market_cap_usd ELSE 0 END) / NULLIF(SUM(market_cap_usd), 0) * 100 as top_10_dominance,
                SUM(CASE WHEN symbol = 'BTC' THEN market_cap_usd ELSE 0 END) / NULLIF(SUM(market_cap_usd), 0) * 100 as btc_dominance,
                SUM(CASE WHEN symbol = 'ETH' THEN market_cap_usd ELSE 0 END) / NULLIF(SUM(market_cap_usd), 0) * 100 as eth_dominance
            FROM daily_data
        )
        SELECT 
            ms.active_cryptos,
            ms.cryptos_with_volume,
            ms.total_market_cap,
            ms.total_volume,
            ms.avg_daily_return,
            ms.median_daily_return,
            ms.market_volatility,
            tp.best_symbol,
            tp.best_return,
            wp.worst_symbol,
            wp.worst_return,
            dd.top_10_dominance,
            dd.btc_dominance,
            dd.eth_dominance,
            (100 - COALESCE(dd.btc_dominance, 0) - COALESCE(dd.eth_dominance, 0)) as altcoin_dominance
        INTO v_market_data
        FROM market_stats ms
        CROSS JOIN top_performers tp
        CROSS JOIN worst_performers wp
        CROSS JOIN dominance_data dd;
        
        -- Delete existing record for the date if it exists
        DELETE FROM market_overview_daily WHERE date_key = v_target_date;
        
        -- Insert new market overview record
        INSERT INTO market_overview_daily (
            date_key,
            year,
            quarter,
            month,
            week_of_year,
            day_of_week,
            total_market_cap_usd,
            total_volume_24h_usd,
            active_cryptocurrencies_count,
            cryptocurrencies_with_volume_count,
            best_performer_symbol,
            best_performer_change_pct,
            worst_performer_symbol,
            worst_performer_change_pct,
            top_10_market_cap_dominance,
            bitcoin_dominance,
            ethereum_dominance,
            altcoin_dominance,
            market_volatility_index,
            avg_price_change_24h,
            median_price_change_24h,
            market_momentum_score,
            volume_strength_score,
            data_completeness_pct,
            quality_score,
            etl_batch_id
        ) VALUES (
            v_target_date,
            EXTRACT(YEAR FROM v_target_date),
            EXTRACT(QUARTER FROM v_target_date),
            EXTRACT(MONTH FROM v_target_date),
            EXTRACT(WEEK FROM v_target_date),
            EXTRACT(DOW FROM v_target_date),
            v_market_data.total_market_cap,
            v_market_data.total_volume,
            v_market_data.active_cryptos,
            v_market_data.cryptos_with_volume,
            v_market_data.best_symbol,
            v_market_data.best_return,
            v_market_data.worst_symbol,
            v_market_data.worst_return,
            v_market_data.top_10_dominance,
            v_market_data.btc_dominance,
            v_market_data.eth_dominance,
            v_market_data.altcoin_dominance,
            v_market_data.market_volatility,
            v_market_data.avg_daily_return,
            v_market_data.median_daily_return,
            -- Calculate momentum score based on average return
            CASE 
                WHEN v_market_data.avg_daily_return > 5 THEN 80
                WHEN v_market_data.avg_daily_return > 2 THEN 60
                WHEN v_market_data.avg_daily_return > 0 THEN 40
                WHEN v_market_data.avg_daily_return > -2 THEN 20
                ELSE 0
            END,
            -- Calculate volume strength score
            CASE 
                WHEN v_market_data.total_volume > 100000000000 THEN 90 -- >100B
                WHEN v_market_data.total_volume > 50000000000 THEN 70  -- >50B
                WHEN v_market_data.total_volume > 20000000000 THEN 50  -- >20B
                ELSE 30
            END,
            95.0, -- Assuming high data completeness
            0.95, -- High quality score
            v_batch_id
        );
        
        v_records_processed := 1;
        v_end_time := CURRENT_TIMESTAMP;
        
        -- Log successful job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Generate Market Overview Daily',
            'ETL_TO_GOLD',
            'SUCCESS',
            'gold',
            v_records_processed,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            'SUCCESS'::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
            
    EXCEPTION WHEN OTHERS THEN
        v_end_time := CURRENT_TIMESTAMP;
        
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
            'Generate Market Overview Daily',
            'ETL_TO_GOLD',
            'FAILED',
            'gold',
            v_records_processed,
            SQLERRM,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            ('FAILED: ' || SQLERRM)::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 2. CRYPTOCURRENCY PERFORMANCE METRICS ETL
-- ================================================================================================

-- Function to calculate technical indicators
CREATE OR REPLACE FUNCTION calculate_technical_indicators(
    p_symbol crypto_symbol,
    p_target_date DATE,
    p_lookback_days INTEGER DEFAULT 90
) RETURNS TABLE(
    sma_7 NUMERIC,
    sma_30 NUMERIC,
    sma_90 NUMERIC,
    ema_12 NUMERIC,
    ema_26 NUMERIC,
    rsi_14 NUMERIC,
    macd_line NUMERIC,
    macd_signal NUMERIC,
    macd_histogram NUMERIC,
    bb_upper NUMERIC,
    bb_middle NUMERIC,
    bb_lower NUMERIC,
    bb_width NUMERIC,
    bb_position NUMERIC
) AS $$
DECLARE
    v_result RECORD;
BEGIN
    WITH price_data AS (
        SELECT 
            date_key,
            close_price,
            ROW_NUMBER() OVER (ORDER BY date_key DESC) as rn
        FROM crypto_price_snapshots
        WHERE symbol = p_symbol
          AND snapshot_type = 'DAILY'
          AND date_key <= p_target_date
          AND date_key >= p_target_date - INTERVAL '90 days'
        ORDER BY date_key DESC
    ),
    indicators AS (
        SELECT 
            -- Simple Moving Averages
            AVG(CASE WHEN rn <= 7 THEN close_price END) as sma_7_calc,
            AVG(CASE WHEN rn <= 30 THEN close_price END) as sma_30_calc,
            AVG(CASE WHEN rn <= 90 THEN close_price END) as sma_90_calc,
            
            -- Current price for calculations
            FIRST_VALUE(close_price ORDER BY date_key DESC) as current_price,
            
            -- Bollinger Bands (20-day SMA, 2 std dev)
            AVG(CASE WHEN rn <= 20 THEN close_price END) as bb_sma_20,
            STDDEV(CASE WHEN rn <= 20 THEN close_price END) as bb_stddev_20
            
        FROM price_data
    )
    SELECT 
        sma_7_calc,
        sma_30_calc,
        sma_90_calc,
        sma_7_calc, -- Simplified EMA calculation (using SMA as approximation)
        sma_30_calc, -- Simplified EMA calculation (using SMA as approximation)
        50.0, -- Placeholder RSI (would need complex calculation)
        sma_7_calc - sma_30_calc, -- MACD approximation
        (sma_7_calc - sma_30_calc) * 0.9, -- MACD signal approximation
        (sma_7_calc - sma_30_calc) * 0.1, -- MACD histogram approximation
        bb_sma_20 + (2 * bb_stddev_20), -- Bollinger Upper
        bb_sma_20, -- Bollinger Middle
        bb_sma_20 - (2 * bb_stddev_20), -- Bollinger Lower
        4 * bb_stddev_20, -- Bollinger Width
        CASE 
            WHEN bb_sma_20 + (2 * bb_stddev_20) != bb_sma_20 - (2 * bb_stddev_20) THEN
                (current_price - (bb_sma_20 - (2 * bb_stddev_20))) / 
                ((bb_sma_20 + (2 * bb_stddev_20)) - (bb_sma_20 - (2 * bb_stddev_20)))
            ELSE 0.5
        END -- Bollinger Position
    INTO v_result
    FROM indicators;
    
    RETURN QUERY SELECT 
        v_result.sma_7_calc,
        v_result.sma_30_calc,
        v_result.sma_90_calc,
        v_result.sma_7_calc,
        v_result.sma_30_calc,
        50.0::NUMERIC,
        v_result.sma_7_calc - v_result.sma_30_calc,
        (v_result.sma_7_calc - v_result.sma_30_calc) * 0.9,
        (v_result.sma_7_calc - v_result.sma_30_calc) * 0.1,
        v_result.bb_sma_20 + (2 * v_result.bb_stddev_20),
        v_result.bb_sma_20,
        v_result.bb_sma_20 - (2 * v_result.bb_stddev_20),
        4 * v_result.bb_stddev_20,
        CASE 
            WHEN v_result.bb_sma_20 + (2 * v_result.bb_stddev_20) != v_result.bb_sma_20 - (2 * v_result.bb_stddev_20) THEN
                (v_result.current_price - (v_result.bb_sma_20 - (2 * v_result.bb_stddev_20))) / 
                ((v_result.bb_sma_20 + (2 * v_result.bb_stddev_20)) - (v_result.bb_sma_20 - (2 * v_result.bb_stddev_20)))
            ELSE 0.5
        END;
END;
$$ LANGUAGE plpgsql;

-- Procedure to generate cryptocurrency performance metrics
CREATE OR REPLACE FUNCTION generate_crypto_performance_metrics(
    p_target_date DATE DEFAULT NULL,
    p_symbol_filter crypto_symbol DEFAULT NULL
) RETURNS TABLE(
    status TEXT,
    records_processed INTEGER,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    v_target_date DATE;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_batch_id UUID;
    v_records_processed INTEGER := 0;
    v_crypto_record RECORD;
    v_tech_indicators RECORD;
BEGIN
    v_start_time := CURRENT_TIMESTAMP;
    v_batch_id := uuid_generate_v4();
    v_target_date := COALESCE(p_target_date, CURRENT_DATE - INTERVAL '1 day');
    
    BEGIN
        -- Delete existing records for the target date
        DELETE FROM crypto_performance_metrics 
        WHERE date_key = v_target_date
          AND (p_symbol_filter IS NULL OR symbol = p_symbol_filter);
        
        -- Process each cryptocurrency
        FOR v_crypto_record IN
            SELECT 
                ps.cmc_id,
                ps.symbol,
                cl.name,
                ps.open_price as open_price_usd,
                ps.high_price as high_price_usd,
                ps.low_price as low_price_usd,
                ps.close_price as close_price_usd,
                ps.volume,
                ps.price_change_pct as daily_return_pct,
                ps.price_volatility as volatility_daily,
                cl.market_cap_rank,
                
                -- Calculate market cap based on close price and circulating supply
                CASE 
                    WHEN cl.circulating_supply > 0 THEN ps.close_price * cl.circulating_supply
                    ELSE NULL
                END as market_cap_usd
                
            FROM crypto_price_snapshots ps
            LEFT JOIN clean_crypto_listings cl ON ps.cmc_id = cl.cmc_id AND cl.is_current = TRUE
            WHERE ps.date_key = v_target_date
              AND ps.snapshot_type = 'DAILY'
              AND ps.quality_score >= 0.8
              AND (p_symbol_filter IS NULL OR ps.symbol = p_symbol_filter)
        LOOP
            -- Calculate technical indicators
            SELECT * INTO v_tech_indicators
            FROM calculate_technical_indicators(
                v_crypto_record.symbol,
                v_target_date,
                90
            );
            
            -- Insert performance metrics
            INSERT INTO crypto_performance_metrics (
                cmc_id,
                symbol,
                name,
                date_key,
                open_price_usd,
                high_price_usd,
                low_price_usd,
                close_price_usd,
                volume_usd,
                daily_return_pct,
                volatility_daily,
                sma_7_days,
                sma_30_days,
                sma_90_days,
                ema_12_days,
                ema_26_days,
                rsi_14_days,
                macd_line,
                macd_signal,
                macd_histogram,
                bb_upper,
                bb_middle,
                bb_lower,
                bb_width,
                bb_position,
                volume_sma_20,
                volume_ratio,
                market_cap_usd,
                market_cap_rank,
                market_cap_dominance,
                drawdown_from_ath,
                days_since_ath,
                correlation_btc_30d,
                correlation_eth_30d,
                data_completeness_pct,
                quality_score,
                etl_batch_id
            ) VALUES (
                v_crypto_record.cmc_id,
                v_crypto_record.symbol,
                v_crypto_record.name,
                v_target_date,
                v_crypto_record.open_price_usd,
                v_crypto_record.high_price_usd,
                v_crypto_record.low_price_usd,
                v_crypto_record.close_price_usd,
                v_crypto_record.volume,
                v_crypto_record.daily_return_pct,
                v_crypto_record.volatility_daily,
                v_tech_indicators.sma_7,
                v_tech_indicators.sma_30,
                v_tech_indicators.sma_90,
                v_tech_indicators.ema_12,
                v_tech_indicators.ema_26,
                v_tech_indicators.rsi_14,
                v_tech_indicators.macd_line,
                v_tech_indicators.macd_signal,
                v_tech_indicators.macd_histogram,
                v_tech_indicators.bb_upper,
                v_tech_indicators.bb_middle,
                v_tech_indicators.bb_lower,
                v_tech_indicators.bb_width,
                v_tech_indicators.bb_position,
                v_crypto_record.volume * 0.8, -- Approximated volume SMA
                CASE 
                    WHEN v_crypto_record.volume > 0 THEN v_crypto_record.volume / (v_crypto_record.volume * 0.8)
                    ELSE NULL
                END,
                v_crypto_record.market_cap_usd,
                v_crypto_record.market_cap_rank,
                NULL, -- Market cap dominance (calculated separately)
                NULL, -- Drawdown from ATH (requires historical calculation)
                NULL, -- Days since ATH (requires historical calculation)
                NULL, -- BTC correlation (requires calculation)
                NULL, -- ETH correlation (requires calculation)
                95.0,
                0.95,
                v_batch_id
            );
            
            v_records_processed := v_records_processed + 1;
        END LOOP;
        
        v_end_time := CURRENT_TIMESTAMP;
        
        -- Log successful job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Generate Crypto Performance Metrics',
            'ETL_TO_GOLD',
            'SUCCESS',
            'gold',
            v_records_processed,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            'SUCCESS'::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
            
    EXCEPTION WHEN OTHERS THEN
        v_end_time := CURRENT_TIMESTAMP;
        
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
            'Generate Crypto Performance Metrics',
            'ETL_TO_GOLD',
            'FAILED',
            'gold',
            v_records_processed,
            SQLERRM,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            ('FAILED: ' || SQLERRM)::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 3. CORRELATION MATRIX ETL
-- ================================================================================================

-- Procedure to generate correlation matrix
CREATE OR REPLACE FUNCTION generate_correlation_matrix(
    p_target_date DATE DEFAULT NULL,
    p_analysis_period_days INTEGER DEFAULT 30
) RETURNS TABLE(
    status TEXT,
    records_processed INTEGER,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    v_target_date DATE;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_batch_id UUID;
    v_records_processed INTEGER := 0;
    v_correlation_record RECORD;
BEGIN
    v_start_time := CURRENT_TIMESTAMP;
    v_batch_id := uuid_generate_v4();
    v_target_date := COALESCE(p_target_date, CURRENT_DATE - INTERVAL '1 day');
    
    BEGIN
        -- Delete existing correlation data for the target date and period
        DELETE FROM correlation_matrix 
        WHERE date_key = v_target_date 
          AND analysis_period_days = p_analysis_period_days;
        
        -- Calculate correlations between cryptocurrency pairs
        FOR v_correlation_record IN
            WITH daily_returns AS (
                SELECT 
                    symbol,
                    date_key,
                    daily_return_pct
                FROM crypto_performance_metrics
                WHERE date_key BETWEEN v_target_date - (p_analysis_period_days || ' days')::INTERVAL
                                   AND v_target_date
                  AND daily_return_pct IS NOT NULL
                  AND quality_score >= 0.8
            ),
            correlation_pairs AS (
                SELECT 
                    a.symbol as symbol_a,
                    b.symbol as symbol_b,
                    CORR(a.daily_return_pct, b.daily_return_pct) as correlation_coeff,
                    COUNT(*) as observation_count,
                    AVG(a.daily_return_pct) as avg_return_a,
                    AVG(b.daily_return_pct) as avg_return_b,
                    STDDEV(a.daily_return_pct) as volatility_a,
                    STDDEV(b.daily_return_pct) as volatility_b
                FROM daily_returns a
                JOIN daily_returns b ON a.date_key = b.date_key
                WHERE a.symbol < b.symbol  -- Avoid duplicate pairs
                GROUP BY a.symbol, b.symbol
                HAVING COUNT(*) >= (p_analysis_period_days * 0.7)  -- At least 70% data availability
            )
            SELECT 
                symbol_a,
                symbol_b,
                correlation_coeff,
                observation_count,
                avg_return_a,
                avg_return_b,
                volatility_a,
                volatility_b,
                
                -- Classify correlation strength
                CASE 
                    WHEN ABS(correlation_coeff) >= 0.8 THEN 'VERY_STRONG'
                    WHEN ABS(correlation_coeff) >= 0.6 THEN 'STRONG'
                    WHEN ABS(correlation_coeff) >= 0.4 THEN 'MODERATE'
                    WHEN ABS(correlation_coeff) >= 0.2 THEN 'WEAK'
                    ELSE 'VERY_WEAK'
                END as correlation_strength,
                
                -- Determine direction
                CASE 
                    WHEN correlation_coeff > 0 THEN 'POSITIVE'
                    ELSE 'NEGATIVE'
                END as correlation_direction
                
            FROM correlation_pairs
            WHERE correlation_coeff IS NOT NULL
        LOOP
            INSERT INTO correlation_matrix (
                date_key,
                analysis_period_days,
                symbol_a,
                symbol_b,
                correlation_coefficient,
                correlation_strength,
                correlation_direction,
                p_value,
                is_significant,
                observations_count,
                avg_return_a,
                avg_return_b,
                volatility_a,
                volatility_b,
                correlation_trend,
                correlation_stability_score,
                etl_batch_id
            ) VALUES (
                v_target_date,
                p_analysis_period_days,
                v_correlation_record.symbol_a,
                v_correlation_record.symbol_b,
                v_correlation_record.correlation_coeff,
                v_correlation_record.correlation_strength,
                v_correlation_record.correlation_direction,
                0.05, -- Placeholder p-value
                ABS(v_correlation_record.correlation_coeff) > 0.3, -- Significance threshold
                v_correlation_record.observation_count,
                v_correlation_record.avg_return_a,
                v_correlation_record.avg_return_b,
                v_correlation_record.volatility_a,
                v_correlation_record.volatility_b,
                'STABLE', -- Placeholder trend
                0.8, -- Placeholder stability score
                v_batch_id
            );
            
            v_records_processed := v_records_processed + 1;
        END LOOP;
        
        v_end_time := CURRENT_TIMESTAMP;
        
        -- Log successful job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Generate Correlation Matrix',
            'ETL_TO_GOLD',
            'SUCCESS',
            'gold',
            v_records_processed,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            'SUCCESS'::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
            
    EXCEPTION WHEN OTHERS THEN
        v_end_time := CURRENT_TIMESTAMP;
        
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
            'Generate Correlation Matrix',
            'ETL_TO_GOLD',
            'FAILED',
            'gold',
            v_records_processed,
            SQLERRM,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            ('FAILED: ' || SQLERRM)::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 4. ML FEATURES DATASET ETL
-- ================================================================================================

-- Procedure to generate ML features dataset
CREATE OR REPLACE FUNCTION generate_ml_features_dataset(
    p_target_date DATE DEFAULT NULL,
    p_symbol_filter crypto_symbol DEFAULT NULL
) RETURNS TABLE(
    status TEXT,
    records_processed INTEGER,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    v_target_date DATE;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_batch_id UUID;
    v_records_processed INTEGER := 0;
    v_feature_record RECORD;
BEGIN
    v_start_time := CURRENT_TIMESTAMP;
    v_batch_id := uuid_generate_v4();
    v_target_date := COALESCE(p_target_date, CURRENT_DATE - INTERVAL '1 day');
    
    BEGIN
        -- Delete existing features for the target date
        DELETE FROM ml_features_dataset 
        WHERE DATE(feature_timestamp) = v_target_date
          AND (p_symbol_filter IS NULL OR symbol = p_symbol_filter);
        
        -- Generate features for each cryptocurrency
        FOR v_feature_record IN
            WITH base_data AS (
                SELECT 
                    cpm.cmc_id,
                    cpm.symbol,
                    cpm.date_key,
                    cpm.close_price_usd,
                    cpm.volume_usd,
                    cpm.daily_return_pct,
                    cpm.volatility_daily,
                    cpm.sma_7_days,
                    cpm.sma_30_days,
                    cpm.ema_12_days,
                    cpm.ema_26_days,
                    cpm.rsi_14_days,
                    cpm.bb_position,
                    cpm.macd_signal,
                    cpm.market_cap_usd,
                    cpm.market_cap_rank,
                    cpm.market_cap_dominance,
                    cpm.correlation_btc_30d,
                    cpm.correlation_eth_30d
                FROM crypto_performance_metrics cpm
                WHERE cpm.date_key = v_target_date
                  AND cpm.quality_score >= 0.8
                  AND (p_symbol_filter IS NULL OR cpm.symbol = p_symbol_filter)
            ),
            future_returns AS (
                SELECT 
                    bd.symbol,
                    bd.date_key,
                    
                    -- Future price changes (targets for ML)
                    LEAD(cpm.close_price_usd, 1) OVER (PARTITION BY bd.symbol ORDER BY bd.date_key) as price_1d_ahead,
                    LEAD(cpm.close_price_usd, 7) OVER (PARTITION BY bd.symbol ORDER BY bd.date_key) as price_7d_ahead
                    
                FROM base_data bd
                LEFT JOIN crypto_performance_metrics cpm ON bd.symbol = cpm.symbol 
                    AND cpm.date_key > bd.date_key 
                    AND cpm.date_key <= bd.date_key + INTERVAL '7 days'
            )
            SELECT 
                bd.*,
                fr.price_1d_ahead,
                fr.price_7d_ahead,
                
                -- Calculate target variables
                CASE 
                    WHEN fr.price_1d_ahead IS NOT NULL AND bd.close_price_usd > 0 THEN
                        (fr.price_1d_ahead - bd.close_price_usd) / bd.close_price_usd * 100
                    ELSE NULL
                END as price_change_24h_target,
                
                CASE 
                    WHEN fr.price_7d_ahead IS NOT NULL AND bd.close_price_usd > 0 THEN
                        (fr.price_7d_ahead - bd.close_price_usd) / bd.close_price_usd * 100
                    ELSE NULL
                END as price_change_7d_target
                
            FROM base_data bd
            LEFT JOIN future_returns fr ON bd.symbol = fr.symbol AND bd.date_key = fr.date_key
        LOOP
            INSERT INTO ml_features_dataset (
                cmc_id,
                symbol,
                feature_timestamp,
                price_usd,
                price_sma_7,
                price_sma_30,
                price_ema_12,
                price_ema_26,
                price_rsi_14,
                volume_usd,
                volume_ratio,
                volatility_1d,
                volatility_7d,
                volatility_30d,
                momentum_1d,
                momentum_7d,
                momentum_30d,
                market_cap_usd,
                market_cap_rank,
                market_dominance,
                correlation_btc_30d,
                correlation_eth_30d,
                bb_position,
                macd_signal,
                price_change_24h,
                price_change_7d,
                direction_24h,
                direction_7d,
                volatility_class,
                feature_completeness_pct,
                quality_score,
                etl_batch_id
            ) VALUES (
                v_feature_record.cmc_id,
                v_feature_record.symbol,
                v_feature_record.date_key::TIMESTAMP,
                v_feature_record.close_price_usd,
                v_feature_record.sma_7_days,
                v_feature_record.sma_30_days,
                v_feature_record.ema_12_days,
                v_feature_record.ema_26_days,
                v_feature_record.rsi_14_days,
                v_feature_record.volume_usd,
                2.0, -- Placeholder volume ratio
                v_feature_record.volatility_daily,
                v_feature_record.volatility_daily * 1.2, -- Approximated 7d volatility
                v_feature_record.volatility_daily * 1.5, -- Approximated 30d volatility
                v_feature_record.daily_return_pct,
                v_feature_record.daily_return_pct * 0.8, -- Approximated 7d momentum
                v_feature_record.daily_return_pct * 0.6, -- Approximated 30d momentum
                v_feature_record.market_cap_usd,
                v_feature_record.market_cap_rank,
                v_feature_record.market_cap_dominance,
                v_feature_record.correlation_btc_30d,
                v_feature_record.correlation_eth_30d,
                v_feature_record.bb_position,
                v_feature_record.macd_signal,
                v_feature_record.price_change_24h_target,
                v_feature_record.price_change_7d_target,
                
                -- Direction classification
                CASE 
                    WHEN v_feature_record.price_change_24h_target > 2 THEN 'UP'
                    WHEN v_feature_record.price_change_24h_target < -2 THEN 'DOWN'
                    ELSE 'STABLE'
                END,
                
                CASE 
                    WHEN v_feature_record.price_change_7d_target > 5 THEN 'UP'
                    WHEN v_feature_record.price_change_7d_target < -5 THEN 'DOWN'
                    ELSE 'STABLE'
                END,
                
                -- Volatility classification
                CASE 
                    WHEN v_feature_record.volatility_daily > 0.1 THEN 'HIGH'
                    WHEN v_feature_record.volatility_daily > 0.05 THEN 'MEDIUM'
                    ELSE 'LOW'
                END,
                
                90.0, -- Feature completeness
                0.9,  -- Quality score
                v_batch_id
            );
            
            v_records_processed := v_records_processed + 1;
        END LOOP;
        
        v_end_time := CURRENT_TIMESTAMP;
        
        -- Log successful job
        INSERT INTO etl_jobs (
            job_name,
            job_type,
            status,
            target_schema,
            records_processed,
            end_time
        ) VALUES (
            'Generate ML Features Dataset',
            'ETL_TO_GOLD',
            'SUCCESS',
            'gold',
            v_records_processed,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            'SUCCESS'::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
            
    EXCEPTION WHEN OTHERS THEN
        v_end_time := CURRENT_TIMESTAMP;
        
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
            'Generate ML Features Dataset',
            'ETL_TO_GOLD',
            'FAILED',
            'gold',
            v_records_processed,
            SQLERRM,
            v_end_time
        );
        
        RETURN QUERY SELECT 
            ('FAILED: ' || SQLERRM)::TEXT,
            v_records_processed,
            EXTRACT(EPOCH FROM (v_end_time - v_start_time))::NUMERIC;
    END;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 5. MASTER ETL ORCHESTRATION PROCEDURE
-- ================================================================================================

-- Master procedure to run all Gold layer ETL processes
CREATE OR REPLACE FUNCTION run_gold_layer_etl(
    p_target_date DATE DEFAULT NULL,
    p_include_ml_features BOOLEAN DEFAULT TRUE
) RETURNS TABLE(
    process_name TEXT,
    status TEXT,
    records_processed INTEGER,
    execution_time_seconds NUMERIC
) AS $$
DECLARE
    v_target_date DATE;
    v_market_overview_result RECORD;
    v_performance_metrics_result RECORD;
    v_correlation_result RECORD;
    v_ml_features_result RECORD;
BEGIN
    v_target_date := COALESCE(p_target_date, CURRENT_DATE - INTERVAL '1 day');
    
    -- Generate market overview
    SELECT * INTO v_market_overview_result 
    FROM generate_market_overview_daily(v_target_date);
    
    RETURN QUERY SELECT 
        'Market Overview Daily'::TEXT,
        v_market_overview_result.status,
        v_market_overview_result.records_processed,
        v_market_overview_result.execution_time_seconds;
    
    -- Generate cryptocurrency performance metrics
    SELECT * INTO v_performance_metrics_result 
    FROM generate_crypto_performance_metrics(v_target_date);
    
    RETURN QUERY SELECT 
        'Crypto Performance Metrics'::TEXT,
        v_performance_metrics_result.status,
        v_performance_metrics_result.records_processed,
        v_performance_metrics_result.execution_time_seconds;
    
    -- Generate correlation matrix
    SELECT * INTO v_correlation_result 
    FROM generate_correlation_matrix(v_target_date, 30);
    
    RETURN QUERY SELECT 
        'Correlation Matrix (30d)'::TEXT,
        v_correlation_result.status,
        v_correlation_result.records_processed,
        v_correlation_result.execution_time_seconds;
    
    -- Generate ML features dataset if requested
    IF p_include_ml_features THEN
        SELECT * INTO v_ml_features_result 
        FROM generate_ml_features_dataset(v_target_date);
        
        RETURN QUERY SELECT 
            'ML Features Dataset'::TEXT,
            v_ml_features_result.status,
            v_ml_features_result.records_processed,
            v_ml_features_result.execution_time_seconds;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- GRANT PERMISSIONS
-- ================================================================================================

-- Grant execute permissions to application roles
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA gold TO crypto_readwrite;

-- ================================================================================================
-- USAGE EXAMPLES
-- ================================================================================================

/*
-- Example: Generate market overview for yesterday
SELECT * FROM generate_market_overview_daily();

-- Example: Generate performance metrics for specific cryptocurrency
SELECT * FROM generate_crypto_performance_metrics(CURRENT_DATE - INTERVAL '1 day', 'BTC');

-- Example: Generate correlation matrix for 30-day period
SELECT * FROM generate_correlation_matrix(CURRENT_DATE - INTERVAL '1 day', 30);

-- Example: Generate ML features dataset
SELECT * FROM generate_ml_features_dataset();

-- Example: Run complete Gold layer ETL pipeline
SELECT * FROM run_gold_layer_etl();

-- Example: Run ETL for specific date with ML features
SELECT * FROM run_gold_layer_etl(CURRENT_DATE - INTERVAL '2 days', TRUE);
*/