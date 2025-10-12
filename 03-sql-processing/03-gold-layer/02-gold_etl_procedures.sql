-- =====================================================
-- GOLD LAYER - ETL PROCEDURES (SILVER → GOLD)
-- =====================================================
-- Purpose: Transform clean data into business-ready analytics and ML features
-- Layer: Gold (Analytics & Business Intelligence)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Data Flow: Silver → Gold (Clean Data → Analytics)
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- TECHNICAL INDICATORS CALCULATION FUNCTIONS
-- =====================================================

-- Simple Moving Average Function
CREATE OR ALTER FUNCTION gold.fn_calculate_sma(
    @symbol NVARCHAR(20),
    @target_date DATE,
    @period_days INT
)
RETURNS DECIMAL(18,8)
AS
BEGIN
    DECLARE @sma DECIMAL(18,8);
    
    SELECT @sma = AVG(closing_price)
    FROM silver.crypto_daily_snapshots
    WHERE symbol = @symbol 
        AND snapshot_date <= @target_date
        AND snapshot_date >= DATEADD(DAY, -@period_days + 1, @target_date)
    HAVING COUNT(*) = @period_days; -- Only return if we have complete data
    
    RETURN @sma;
END;
GO

-- RSI Calculation Function (Simplified)
CREATE OR ALTER FUNCTION gold.fn_calculate_rsi(
    @symbol NVARCHAR(20),
    @target_date DATE,
    @period_days INT = 14
)
RETURNS DECIMAL(5,2)
AS
BEGIN
    DECLARE @rsi DECIMAL(5,2);
    DECLARE @avg_gain DECIMAL(18,8);
    DECLARE @avg_loss DECIMAL(18,8);
    DECLARE @rs DECIMAL(18,8);
    
    WITH price_changes AS (
        SELECT 
            snapshot_date,
            closing_price,
            LAG(closing_price) OVER (ORDER BY snapshot_date) AS prev_price,
            closing_price - LAG(closing_price) OVER (ORDER BY snapshot_date) AS price_change
        FROM silver.crypto_daily_snapshots
        WHERE symbol = @symbol 
            AND snapshot_date <= @target_date
            AND snapshot_date >= DATEADD(DAY, -@period_days - 1, @target_date)
    ),
    gains_losses AS (
        SELECT 
            CASE WHEN price_change > 0 THEN price_change ELSE 0 END AS gain,
            CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END AS loss
        FROM price_changes
        WHERE price_change IS NOT NULL
    )
    SELECT 
        @avg_gain = AVG(gain),
        @avg_loss = AVG(loss)
    FROM gains_losses;
    
    IF @avg_loss > 0
    BEGIN
        SET @rs = @avg_gain / @avg_loss;
        SET @rsi = 100 - (100 / (1 + @rs));
    END
    ELSE
    BEGIN
        SET @rsi = 100; -- If no losses, RSI = 100
    END
    
    RETURN @rsi;
END;
GO

-- =====================================================
-- MAIN ETL PROCEDURE: SILVER → GOLD (MARKET OVERVIEW)
-- =====================================================

CREATE OR ALTER PROCEDURE gold.sp_create_market_overview_daily
    @target_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @target_date IS NULL
        SET @target_date = CAST(GETDATE() AS DATE);
    
    DECLARE @job_id BIGINT;
    DECLARE @start_time DATETIME2 = GETDATE();
    
    -- Log ETL job start
    INSERT INTO dbo.etl_job_log (job_name, source_layer, target_layer, start_time, status)
    VALUES ('Silver to Gold - Market Overview', 'silver', 'gold', @start_time, 'RUNNING');
    
    SET @job_id = SCOPE_IDENTITY();
    
    BEGIN TRY
        -- Calculate market overview metrics
        DECLARE @total_cryptocurrencies INT;
        DECLARE @total_market_cap DECIMAL(30,2);
        DECLARE @total_volume_24h DECIMAL(30,2);
        DECLARE @bitcoin_dominance DECIMAL(5,2);
        DECLARE @ethereum_dominance DECIMAL(5,2);
        DECLARE @top_gainer_symbol NVARCHAR(20);
        DECLARE @top_gainer_change DECIMAL(10,4);
        DECLARE @top_loser_symbol NVARCHAR(20);
        DECLARE @top_loser_change DECIMAL(10,4);
        DECLARE @avg_market_cap DECIMAL(25,2);
        DECLARE @median_price DECIMAL(18,8);
        DECLARE @high_quality_count INT;
        
        -- Get basic market metrics from daily snapshots
        SELECT 
            @total_cryptocurrencies = COUNT(DISTINCT symbol),
            @total_market_cap = SUM(market_cap_close),
            @total_volume_24h = SUM(total_volume_24h),
            @avg_market_cap = AVG(market_cap_close),
            @high_quality_count = COUNT(*) FILTER (WHERE quality_score_avg >= 0.80)
        FROM silver.crypto_daily_snapshots
        WHERE snapshot_date = @target_date;
        
        -- Get median price
        SELECT @median_price = AVG(closing_price)
        FROM (
            SELECT closing_price,
                   ROW_NUMBER() OVER (ORDER BY closing_price) AS row_num,
                   COUNT(*) OVER () AS total_count
            FROM silver.crypto_daily_snapshots
            WHERE snapshot_date = @target_date
        ) AS median_calc
        WHERE row_num IN ((total_count + 1) / 2, (total_count + 2) / 2);
        
        -- Get Bitcoin dominance
        SELECT @bitcoin_dominance = 
            CASE 
                WHEN @total_market_cap > 0 THEN (market_cap_close * 100.0) / @total_market_cap 
                ELSE 0 
            END
        FROM silver.crypto_daily_snapshots
        WHERE snapshot_date = @target_date AND symbol = 'BTC';
        
        -- Get Ethereum dominance
        SELECT @ethereum_dominance = 
            CASE 
                WHEN @total_market_cap > 0 THEN (market_cap_close * 100.0) / @total_market_cap 
                ELSE 0 
            END
        FROM silver.crypto_daily_snapshots
        WHERE snapshot_date = @target_date AND symbol = 'ETH';
        
        -- Get top gainer
        SELECT TOP 1
            @top_gainer_symbol = symbol,
            @top_gainer_change = price_change_24h
        FROM silver.crypto_daily_snapshots
        WHERE snapshot_date = @target_date 
            AND price_change_24h IS NOT NULL
        ORDER BY price_change_24h DESC;
        
        -- Get top loser
        SELECT TOP 1
            @top_loser_symbol = symbol,
            @top_loser_change = price_change_24h
        FROM silver.crypto_daily_snapshots
        WHERE snapshot_date = @target_date 
            AND price_change_24h IS NOT NULL
        ORDER BY price_change_24h ASC;
        
        -- Insert or update market overview
        MERGE gold.market_overview_daily AS target
        USING (
            SELECT 
                @target_date AS report_date,
                @total_cryptocurrencies AS total_cryptocurrencies,
                @total_market_cap AS total_market_cap_usd,
                @total_volume_24h AS total_volume_24h_usd,
                @bitcoin_dominance AS bitcoin_dominance_pct,
                @ethereum_dominance AS ethereum_dominance_pct,
                @top_gainer_symbol AS top_gainer_symbol,
                @top_gainer_change AS top_gainer_change_pct,
                @top_loser_symbol AS top_loser_symbol,
                @top_loser_change AS top_loser_change_pct,
                @avg_market_cap AS avg_market_cap,
                @median_price AS median_price_usd,
                @high_quality_count AS high_quality_coins_count
        ) AS source ON target.report_date = source.report_date
        
        WHEN MATCHED THEN
            UPDATE SET
                total_cryptocurrencies = source.total_cryptocurrencies,
                total_market_cap_usd = source.total_market_cap_usd,
                total_volume_24h_usd = source.total_volume_24h_usd,
                bitcoin_dominance_pct = source.bitcoin_dominance_pct,
                ethereum_dominance_pct = source.ethereum_dominance_pct,
                top_gainer_symbol = source.top_gainer_symbol,
                top_gainer_change_pct = source.top_gainer_change_pct,
                top_loser_symbol = source.top_loser_symbol,
                top_loser_change_pct = source.top_loser_change_pct,
                avg_market_cap = source.avg_market_cap,
                median_price_usd = source.median_price_usd,
                high_quality_coins_count = source.high_quality_coins_count,
                created_timestamp = GETDATE()
        
        WHEN NOT MATCHED THEN
            INSERT (report_date, total_cryptocurrencies, total_market_cap_usd, total_volume_24h_usd,
                    bitcoin_dominance_pct, ethereum_dominance_pct, top_gainer_symbol, top_gainer_change_pct,
                    top_loser_symbol, top_loser_change_pct, avg_market_cap, median_price_usd, high_quality_coins_count)
            VALUES (source.report_date, source.total_cryptocurrencies, source.total_market_cap_usd, source.total_volume_24h_usd,
                    source.bitcoin_dominance_pct, source.ethereum_dominance_pct, source.top_gainer_symbol, source.top_gainer_change_pct,
                    source.top_loser_symbol, source.top_loser_change_pct, source.avg_market_cap, source.median_price_usd, source.high_quality_coins_count);
        
        -- Update ETL job log with success
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'SUCCESS',
            records_processed = 1,
            records_inserted = 1
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'SUCCESS' AS status,
            @target_date AS report_date,
            @total_cryptocurrencies AS cryptocurrencies_analyzed,
            DATEDIFF(SECOND, @start_time, GETDATE()) AS duration_seconds;
        
    END TRY
    BEGIN CATCH
        -- Update ETL job log with error
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'ERROR',
            error_message = ERROR_MESSAGE()
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'ERROR' AS status,
            @target_date AS report_date,
            ERROR_MESSAGE() AS error_message;
    END CATCH
END;
GO

-- =====================================================
-- CRYPTO PERFORMANCE METRICS (TECHNICAL ANALYSIS)
-- =====================================================

CREATE OR ALTER PROCEDURE gold.sp_create_performance_metrics
    @target_date DATE = NULL,
    @symbol NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @target_date IS NULL
        SET @target_date = CAST(GETDATE() AS DATE);
    
    DECLARE @job_id BIGINT;
    DECLARE @start_time DATETIME2 = GETDATE();
    DECLARE @records_processed INT = 0;
    
    -- Log ETL job start
    INSERT INTO dbo.etl_job_log (job_name, source_layer, target_layer, start_time, status)
    VALUES ('Silver to Gold - Performance Metrics', 'silver', 'gold', @start_time, 'RUNNING');
    
    SET @job_id = SCOPE_IDENTITY();
    
    BEGIN TRY
        -- Process symbols (either specific symbol or all symbols)
        DECLARE @symbols_to_process TABLE (symbol NVARCHAR(20));
        
        IF @symbol IS NOT NULL
            INSERT INTO @symbols_to_process VALUES (@symbol);
        ELSE
            INSERT INTO @symbols_to_process 
            SELECT DISTINCT symbol 
            FROM silver.crypto_daily_snapshots 
            WHERE snapshot_date = @target_date;
        
        -- Cursor for processing each symbol
        DECLARE symbol_cursor CURSOR FOR
        SELECT symbol FROM @symbols_to_process;
        
        DECLARE @current_symbol NVARCHAR(20);
        
        OPEN symbol_cursor;
        FETCH NEXT FROM symbol_cursor INTO @current_symbol;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Calculate technical indicators for this symbol
            DECLARE @sma_7d DECIMAL(18,8) = gold.fn_calculate_sma(@current_symbol, @target_date, 7);
            DECLARE @sma_30d DECIMAL(18,8) = gold.fn_calculate_sma(@current_symbol, @target_date, 30);
            DECLARE @sma_90d DECIMAL(18,8) = gold.fn_calculate_sma(@current_symbol, @target_date, 90);
            DECLARE @rsi_14d DECIMAL(5,2) = gold.fn_calculate_rsi(@current_symbol, @target_date, 14);
            
            -- Get current price and volume data
            DECLARE @current_price DECIMAL(18,8);
            DECLARE @current_volume DECIMAL(25,2);
            DECLARE @price_change_24h DECIMAL(10,4);
            
            SELECT 
                @current_price = closing_price,
                @current_volume = total_volume_24h,
                @price_change_24h = price_change_24h
            FROM silver.crypto_daily_snapshots
            WHERE symbol = @current_symbol AND snapshot_date = @target_date;
            
            -- Calculate additional metrics
            DECLARE @volatility_7d DECIMAL(10,6);
            DECLARE @return_7d DECIMAL(10,4);
            DECLARE @return_30d DECIMAL(10,4);
            DECLARE @volume_sma_7d DECIMAL(25,2);
            
            -- Calculate 7-day volatility (standard deviation of daily returns)
            WITH daily_returns AS (
                SELECT 
                    (closing_price - LAG(closing_price) OVER (ORDER BY snapshot_date)) / LAG(closing_price) OVER (ORDER BY snapshot_date) AS daily_return
                FROM silver.crypto_daily_snapshots
                WHERE symbol = @current_symbol 
                    AND snapshot_date <= @target_date
                    AND snapshot_date >= DATEADD(DAY, -7, @target_date)
            )
            SELECT @volatility_7d = STDEV(daily_return)
            FROM daily_returns
            WHERE daily_return IS NOT NULL;
            
            -- Calculate returns
            SELECT @return_7d = 
                CASE 
                    WHEN LAG(closing_price, 7) OVER (ORDER BY snapshot_date) > 0 
                    THEN ((closing_price - LAG(closing_price, 7) OVER (ORDER BY snapshot_date)) * 100.0) / LAG(closing_price, 7) OVER (ORDER BY snapshot_date)
                    ELSE NULL 
                END
            FROM silver.crypto_daily_snapshots
            WHERE symbol = @current_symbol AND snapshot_date = @target_date;
            
            SELECT @return_30d = 
                CASE 
                    WHEN LAG(closing_price, 30) OVER (ORDER BY snapshot_date) > 0 
                    THEN ((closing_price - LAG(closing_price, 30) OVER (ORDER BY snapshot_date)) * 100.0) / LAG(closing_price, 30) OVER (ORDER BY snapshot_date)
                    ELSE NULL 
                END
            FROM silver.crypto_daily_snapshots
            WHERE symbol = @current_symbol AND snapshot_date = @target_date;
            
            -- Calculate volume SMA
            SELECT @volume_sma_7d = AVG(total_volume_24h)
            FROM silver.crypto_daily_snapshots
            WHERE symbol = @current_symbol 
                AND snapshot_date <= @target_date
                AND snapshot_date >= DATEADD(DAY, -7, @target_date);
            
            -- Insert or update performance metrics
            MERGE gold.crypto_performance_metrics AS target
            USING (
                SELECT 
                    @current_symbol AS symbol,
                    @target_date AS analysis_date,
                    @sma_7d AS sma_7d,
                    @sma_30d AS sma_30d,
                    @sma_90d AS sma_90d,
                    @rsi_14d AS rsi_14d,
                    @volatility_7d AS volatility_7d,
                    @return_7d AS return_7d,
                    @return_30d AS return_30d,
                    @volume_sma_7d AS volume_sma_7d,
                    CASE WHEN @volume_sma_7d > 0 THEN @current_volume / @volume_sma_7d ELSE NULL END AS volume_ratio_24h
            ) AS source ON target.symbol = source.symbol AND target.analysis_date = source.analysis_date
            
            WHEN MATCHED THEN
                UPDATE SET
                    sma_7d = source.sma_7d,
                    sma_30d = source.sma_30d,
                    sma_90d = source.sma_90d,
                    rsi_14d = source.rsi_14d,
                    volatility_7d = source.volatility_7d,
                    return_7d = source.return_7d,
                    return_30d = source.return_30d,
                    volume_sma_7d = source.volume_sma_7d,
                    volume_ratio_24h = source.volume_ratio_24h,
                    created_timestamp = GETDATE()
            
            WHEN NOT MATCHED THEN
                INSERT (symbol, analysis_date, sma_7d, sma_30d, sma_90d, rsi_14d, 
                        volatility_7d, return_7d, return_30d, volume_sma_7d, volume_ratio_24h)
                VALUES (source.symbol, source.analysis_date, source.sma_7d, source.sma_30d, source.sma_90d, 
                        source.rsi_14d, source.volatility_7d, source.return_7d, source.return_30d, 
                        source.volume_sma_7d, source.volume_ratio_24h);
            
            SET @records_processed = @records_processed + 1;
            
            FETCH NEXT FROM symbol_cursor INTO @current_symbol;
        END
        
        CLOSE symbol_cursor;
        DEALLOCATE symbol_cursor;
        
        -- Update ETL job log with success
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'SUCCESS',
            records_processed = @records_processed,
            records_inserted = @records_processed
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'SUCCESS' AS status,
            @target_date AS analysis_date,
            @records_processed AS symbols_processed,
            DATEDIFF(SECOND, @start_time, GETDATE()) AS duration_seconds;
        
    END TRY
    BEGIN CATCH
        -- Handle errors
        IF CURSOR_STATUS('global', 'symbol_cursor') >= 0
        BEGIN
            CLOSE symbol_cursor;
            DEALLOCATE symbol_cursor;
        END
        
        -- Update ETL job log with error
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'ERROR',
            records_processed = @records_processed,
            error_message = ERROR_MESSAGE()
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'ERROR' AS status,
            @target_date AS analysis_date,
            @records_processed AS symbols_processed,
            ERROR_MESSAGE() AS error_message;
    END CATCH
END;
GO

-- =====================================================
-- TRADING SIGNALS GENERATION
-- =====================================================

CREATE OR ALTER PROCEDURE gold.sp_generate_trading_signals
    @target_date DATE = NULL,
    @min_confidence DECIMAL(3,2) = 0.60
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @target_date IS NULL
        SET @target_date = CAST(GETDATE() AS DATE);
    
    DECLARE @job_id BIGINT;
    DECLARE @start_time DATETIME2 = GETDATE();
    DECLARE @records_processed INT = 0;
    
    -- Log ETL job start
    INSERT INTO dbo.etl_job_log (job_name, source_layer, target_layer, start_time, status)
    VALUES ('Silver to Gold - Trading Signals', 'silver', 'gold', @start_time, 'RUNNING');
    
    SET @job_id = SCOPE_IDENTITY();
    
    BEGIN TRY
        -- Generate trading signals based on technical indicators
        INSERT INTO gold.trading_signals (
            symbol, signal_date, signal_type, confidence_score, signal_strength,
            price_trend_signal, volume_signal, momentum_signal, 
            current_price, signal_algorithm, market_condition
        )
        SELECT 
            p.symbol,
            GETDATE() AS signal_date,
            -- Simple signal logic based on SMA crossover and RSI
            CASE 
                WHEN s.closing_price > p.sma_7d AND p.sma_7d > p.sma_30d AND p.rsi_14d < 70 THEN 'BUY'
                WHEN s.closing_price < p.sma_7d AND p.sma_7d < p.sma_30d AND p.rsi_14d > 30 THEN 'SELL'
                ELSE 'HOLD'
            END AS signal_type,
            -- Confidence calculation
            CASE 
                WHEN s.closing_price > p.sma_7d AND p.sma_7d > p.sma_30d AND p.rsi_14d BETWEEN 30 AND 70 THEN 0.85
                WHEN s.closing_price < p.sma_7d AND p.sma_7d < p.sma_30d AND p.rsi_14d BETWEEN 30 AND 70 THEN 0.80
                WHEN ABS(s.closing_price - p.sma_7d) / s.closing_price < 0.02 THEN 0.45 -- Near SMA = low confidence
                ELSE 0.60
            END AS confidence_score,
            -- Signal strength
            CASE 
                WHEN ABS(s.price_change_24h) > 10 THEN 'STRONG'
                WHEN ABS(s.price_change_24h) > 5 THEN 'MODERATE'
                ELSE 'WEAK'
            END AS signal_strength,
            -- Component signals
            CASE 
                WHEN s.closing_price > p.sma_30d THEN 'BULLISH'
                WHEN s.closing_price < p.sma_30d THEN 'BEARISH'
                ELSE 'NEUTRAL'
            END AS price_trend_signal,
            CASE 
                WHEN p.volume_ratio_24h > 1.5 THEN 'HIGH'
                WHEN p.volume_ratio_24h < 0.5 THEN 'LOW'
                ELSE 'NORMAL'
            END AS volume_signal,
            CASE 
                WHEN p.rsi_14d > 70 THEN 'OVERBOUGHT'
                WHEN p.rsi_14d < 30 THEN 'OVERSOLD'
                ELSE 'NEUTRAL'
            END AS momentum_signal,
            s.closing_price AS current_price,
            'SMA_RSI_V1.0' AS signal_algorithm,
            -- Market condition based on volatility
            CASE 
                WHEN p.volatility_7d > 0.05 THEN 'VOLATILE'
                WHEN p.return_7d > 10 THEN 'BULL'
                WHEN p.return_7d < -10 THEN 'BEAR'
                ELSE 'SIDEWAYS'
            END AS market_condition
        FROM gold.crypto_performance_metrics p
        INNER JOIN silver.crypto_daily_snapshots s ON p.symbol = s.symbol AND s.snapshot_date = @target_date
        WHERE p.analysis_date = @target_date
            AND p.sma_7d IS NOT NULL
            AND p.sma_30d IS NOT NULL
            AND p.rsi_14d IS NOT NULL
            AND s.quality_score_avg >= 0.70; -- Only high-quality data
        
        SET @records_processed = @@ROWCOUNT;
        
        -- Update ETL job log with success
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'SUCCESS',
            records_processed = @records_processed,
            records_inserted = @records_processed
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'SUCCESS' AS status,
            @target_date AS signal_date,
            @records_processed AS signals_generated,
            DATEDIFF(SECOND, @start_time, GETDATE()) AS duration_seconds;
        
    END TRY
    BEGIN CATCH
        -- Update ETL job log with error
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'ERROR',
            error_message = ERROR_MESSAGE()
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'ERROR' AS status,
            @target_date AS signal_date,
            ERROR_MESSAGE() AS error_message;
    END CATCH
END;
GO

-- =====================================================
-- ML FEATURES GENERATION
-- =====================================================

CREATE OR ALTER PROCEDURE gold.sp_create_ml_features
    @target_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @target_date IS NULL
        SET @target_date = CAST(GETDATE() AS DATE);
    
    DECLARE @job_id BIGINT;
    DECLARE @start_time DATETIME2 = GETDATE();
    DECLARE @records_processed INT = 0;
    
    -- Log ETL job start
    INSERT INTO dbo.etl_job_log (job_name, source_layer, target_layer, start_time, status)
    VALUES ('Silver to Gold - ML Features', 'silver', 'gold', @start_time, 'RUNNING');
    
    SET @job_id = SCOPE_IDENTITY();
    
    BEGIN TRY
        -- Create ML features dataset
        MERGE gold.ml_features AS target
        USING (
            SELECT 
                s.symbol,
                @target_date AS feature_date,
                s.closing_price AS price_current,
                s.price_change_24h,
                p.return_7d AS price_change_7d,
                p.volatility_7d AS price_volatility_7d,
                p.volatility_30d,
                RANK() OVER (ORDER BY s.market_cap_close DESC) AS market_cap_rank,
                s.market_cap_close AS market_cap_usd,
                s.total_volume_24h AS volume_24h_usd,
                RANK() OVER (ORDER BY s.total_volume_24h DESC) AS volume_rank,
                mo.bitcoin_dominance_pct / 100.0 AS market_dominance,
                p.rsi_14d AS rsi_14,
                CASE 
                    WHEN p.sma_7d > 0 THEN (s.closing_price - p.sma_7d) / p.sma_7d 
                    ELSE NULL 
                END AS sma_trend_7d,
                p.volume_ratio_24h AS volume_ratio,
                -- Target variables (for supervised learning) - using future data
                LEAD(s.price_change_24h) OVER (PARTITION BY s.symbol ORDER BY s.snapshot_date) AS target_price_change_24h,
                CASE 
                    WHEN LEAD(s.price_change_24h) OVER (PARTITION BY s.symbol ORDER BY s.snapshot_date) > 0 THEN 1 
                    ELSE 0 
                END AS target_direction_24h,
                LEAD(p.volatility_7d) OVER (PARTITION BY s.symbol ORDER BY s.snapshot_date) AS target_volatility_24h,
                -- Feature completeness score
                (
                    CASE WHEN s.closing_price IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN s.price_change_24h IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN p.return_7d IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN p.volatility_7d IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN s.market_cap_close IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN s.total_volume_24h IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN p.rsi_14d IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN p.sma_7d IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN p.volume_ratio_24h IS NOT NULL THEN 1 ELSE 0 END
                ) / 9.0 AS feature_completeness,
                s.quality_score_avg AS data_quality_score
            FROM silver.crypto_daily_snapshots s
            LEFT JOIN gold.crypto_performance_metrics p ON s.symbol = p.symbol AND p.analysis_date = @target_date
            LEFT JOIN gold.market_overview_daily mo ON mo.report_date = @target_date
            WHERE s.snapshot_date = @target_date
                AND s.quality_score_avg >= 0.60
        ) AS source ON target.symbol = source.symbol AND target.feature_date = source.feature_date
        
        WHEN MATCHED THEN
            UPDATE SET
                price_current = source.price_current,
                price_change_1h = NULL, -- Not available in current data
                price_change_24h = source.price_change_24h,
                price_change_7d = source.price_change_7d,
                price_volatility_7d = source.price_volatility_7d,
                price_volatility_30d = source.price_volatility_30d,
                market_cap_rank = source.market_cap_rank,
                market_cap_usd = source.market_cap_usd,
                volume_24h_usd = source.volume_24h_usd,
                volume_rank = source.volume_rank,
                market_dominance = source.market_dominance,
                rsi_14 = source.rsi_14,
                sma_trend_7d = source.sma_trend_7d,
                volume_ratio = source.volume_ratio,
                target_price_change_24h = source.target_price_change_24h,
                target_direction_24h = source.target_direction_24h,
                target_volatility_24h = source.target_volatility_24h,
                feature_completeness = source.feature_completeness,
                data_quality_score = source.data_quality_score,
                created_timestamp = GETDATE()
        
        WHEN NOT MATCHED THEN
            INSERT (symbol, feature_date, price_current, price_change_24h, price_change_7d,
                    price_volatility_7d, price_volatility_30d, market_cap_rank, market_cap_usd,
                    volume_24h_usd, volume_rank, market_dominance, rsi_14, sma_trend_7d, volume_ratio,
                    target_price_change_24h, target_direction_24h, target_volatility_24h,
                    feature_completeness, data_quality_score)
            VALUES (source.symbol, source.feature_date, source.price_current, source.price_change_24h, source.price_change_7d,
                    source.price_volatility_7d, source.price_volatility_30d, source.market_cap_rank, source.market_cap_usd,
                    source.volume_24h_usd, source.volume_rank, source.market_dominance, source.rsi_14, source.sma_trend_7d, source.volume_ratio,
                    source.target_price_change_24h, source.target_direction_24h, source.target_volatility_24h,
                    source.feature_completeness, source.data_quality_score);
        
        SET @records_processed = @@ROWCOUNT;
        
        -- Update ETL job log with success
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'SUCCESS',
            records_processed = @records_processed,
            records_inserted = @records_processed
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'SUCCESS' AS status,
            @target_date AS feature_date,
            @records_processed AS ml_records_created,
            DATEDIFF(SECOND, @start_time, GETDATE()) AS duration_seconds;
        
    END TRY
    BEGIN CATCH
        -- Update ETL job log with error
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'ERROR',
            error_message = ERROR_MESSAGE()
        WHERE id = @job_id;
        
        SELECT 
            @job_id AS etl_job_id,
            'ERROR' AS status,
            @target_date AS feature_date,
            ERROR_MESSAGE() AS error_message;
    END CATCH
END;
GO

-- =====================================================
-- COMPLETE GOLD LAYER ETL PIPELINE
-- =====================================================

CREATE OR ALTER PROCEDURE gold.sp_run_complete_gold_etl
    @target_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @target_date IS NULL
        SET @target_date = CAST(GETDATE() AS DATE);
    
    DECLARE @overall_start DATETIME2 = GETDATE();
    
    PRINT CONCAT('🚀 Starting Complete Gold Layer ETL for ', @target_date);
    
    -- Step 1: Market Overview
    PRINT '📊 Creating Market Overview...';
    EXEC gold.sp_create_market_overview_daily @target_date;
    
    -- Step 2: Performance Metrics (Technical Analysis)
    PRINT '📈 Calculating Performance Metrics...';
    EXEC gold.sp_create_performance_metrics @target_date;
    
    -- Step 3: Trading Signals
    PRINT '⚡ Generating Trading Signals...';
    EXEC gold.sp_generate_trading_signals @target_date;
    
    -- Step 4: ML Features
    PRINT '🤖 Creating ML Features...';
    EXEC gold.sp_create_ml_features @target_date;
    
    DECLARE @total_duration INT = DATEDIFF(SECOND, @overall_start, GETDATE());
    
    PRINT CONCAT('✅ Gold Layer ETL Complete! Duration: ', @total_duration, ' seconds');
    
    -- Return summary
    SELECT 
        'GOLD_ETL_COMPLETE' AS status,
        @target_date AS processing_date,
        @total_duration AS total_duration_seconds,
        GETDATE() AS completion_time;
END;
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '✅ Gold Layer ETL Procedures Created Successfully:';
PRINT '   • fn_calculate_sma - Simple Moving Average calculation';
PRINT '   • fn_calculate_rsi - RSI technical indicator';
PRINT '   • sp_create_market_overview_daily - Daily market analysis';
PRINT '   • sp_create_performance_metrics - Technical indicators';
PRINT '   • sp_generate_trading_signals - ML trading signals';
PRINT '   • sp_create_ml_features - Machine learning features';
PRINT '   • sp_run_complete_gold_etl - Complete Gold layer pipeline';
PRINT '';
PRINT '🔄 ETL Flow: Silver → Gold (Clean Data → Analytics)';
PRINT '📊 Features: Technical analysis, trading signals, ML features';
PRINT '🚀 Ready for complete pipeline automation!';
GO