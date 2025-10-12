-- =====================================================
-- SILVER LAYER - ETL PROCEDURES (BRONZE → SILVER)
-- =====================================================
-- Purpose: Clean, validate, and transform raw data from Bronze to Silver layer
-- Layer: Silver (Clean Data)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Data Flow: Bronze → Silver (Raw → Clean)
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- DATA QUALITY SCORING FUNCTION
-- =====================================================

CREATE OR ALTER FUNCTION silver.fn_calculate_data_quality_score(
    @crypto_id INT,
    @name NVARCHAR(100),
    @symbol NVARCHAR(20),
    @price_usd DECIMAL(18,8),
    @market_cap_usd DECIMAL(25,2),
    @volume_24h_usd DECIMAL(25,2),
    @percent_change_24h DECIMAL(10,4),
    @cmc_rank INT
)
RETURNS DECIMAL(3,2)
AS
BEGIN
    DECLARE @quality_score DECIMAL(3,2) = 0.00;
    DECLARE @total_checks INT = 8;
    DECLARE @passed_checks INT = 0;
    
    -- Check 1: Crypto ID is valid
    IF @crypto_id IS NOT NULL AND @crypto_id > 0
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 2: Name is present
    IF @name IS NOT NULL AND LEN(TRIM(@name)) > 0
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 3: Symbol is present and reasonable length
    IF @symbol IS NOT NULL AND LEN(TRIM(@symbol)) BETWEEN 1 AND 10
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 4: Price is positive and reasonable
    IF @price_usd IS NOT NULL AND @price_usd > 0 AND @price_usd < 10000000
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 5: Market cap is positive (if provided)
    IF @market_cap_usd IS NULL OR @market_cap_usd > 0
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 6: Volume is non-negative (if provided)
    IF @volume_24h_usd IS NULL OR @volume_24h_usd >= 0
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 7: Price change is within reasonable bounds
    IF @percent_change_24h IS NULL OR (@percent_change_24h BETWEEN -99.9 AND 10000.0)
        SET @passed_checks = @passed_checks + 1;
    
    -- Check 8: CMC rank is reasonable (if provided)
    IF @cmc_rank IS NULL OR (@cmc_rank > 0 AND @cmc_rank <= 10000)
        SET @passed_checks = @passed_checks + 1;
    
    -- Calculate final score
    SET @quality_score = CAST(@passed_checks AS DECIMAL(3,2)) / @total_checks;
    
    RETURN @quality_score;
END;
GO

-- =====================================================
-- MAIN ETL PROCEDURE: BRONZE → SILVER
-- =====================================================

CREATE OR ALTER PROCEDURE silver.sp_process_bronze_to_silver
    @batch_size INT = 1000,
    @min_quality_score DECIMAL(3,2) = 0.60
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @job_id BIGINT;
    DECLARE @batch_id UNIQUEIDENTIFIER = NEWID();
    DECLARE @start_time DATETIME2 = GETDATE();
    DECLARE @records_processed INT = 0;
    DECLARE @records_inserted INT = 0;
    DECLARE @records_failed INT = 0;
    
    -- Log ETL job start
    INSERT INTO dbo.etl_job_log (job_name, source_layer, target_layer, start_time, status, batch_id)
    VALUES ('Bronze to Silver ETL', 'bronze', 'silver', @start_time, 'RUNNING', @batch_id);
    
    SET @job_id = SCOPE_IDENTITY();
    
    BEGIN TRY
        -- Process Bronze data that hasn't been processed yet
        DECLARE bronze_cursor CURSOR FOR
        SELECT TOP (@batch_size)
            id, crypto_id, name, symbol, slug, cmc_rank,
            circulating_supply, total_supply, max_supply,
            price_usd, volume_24h_usd, market_cap_usd,
            percent_change_1h, percent_change_24h, percent_change_7d,
            percent_change_30d, percent_change_60d, percent_change_90d,
            volume_change_24h, market_cap_dominance, fully_diluted_market_cap,
            tvl, last_updated, collection_timestamp
        FROM bronze.crypto_raw_data b
        WHERE NOT EXISTS (
            SELECT 1 FROM silver.crypto_clean_data s 
            WHERE s.bronze_source_id = b.id
        )
        ORDER BY collection_timestamp DESC;
        
        DECLARE @bronze_id BIGINT, @crypto_id INT, @name NVARCHAR(100), @symbol NVARCHAR(20),
                @slug NVARCHAR(100), @cmc_rank INT, @circulating_supply DECIMAL(30,8),
                @total_supply DECIMAL(30,8), @max_supply DECIMAL(30,8), @price_usd DECIMAL(18,8),
                @volume_24h_usd DECIMAL(25,2), @market_cap_usd DECIMAL(25,2),
                @percent_change_1h DECIMAL(10,4), @percent_change_24h DECIMAL(10,4),
                @percent_change_7d DECIMAL(10,4), @percent_change_30d DECIMAL(10,4),
                @percent_change_60d DECIMAL(10,4), @percent_change_90d DECIMAL(10,4),
                @volume_change_24h DECIMAL(10,4), @market_cap_dominance DECIMAL(8,4),
                @fully_diluted_market_cap DECIMAL(25,2), @tvl DECIMAL(25,2),
                @last_updated DATETIME2, @collection_timestamp DATETIME2;
        
        OPEN bronze_cursor;
        
        FETCH NEXT FROM bronze_cursor INTO
            @bronze_id, @crypto_id, @name, @symbol, @slug, @cmc_rank,
            @circulating_supply, @total_supply, @max_supply,
            @price_usd, @volume_24h_usd, @market_cap_usd,
            @percent_change_1h, @percent_change_24h, @percent_change_7d,
            @percent_change_30d, @percent_change_60d, @percent_change_90d,
            @volume_change_24h, @market_cap_dominance, @fully_diluted_market_cap,
            @tvl, @last_updated, @collection_timestamp;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            SET @records_processed = @records_processed + 1;
            
            -- Calculate data quality score
            DECLARE @quality_score DECIMAL(3,2) = silver.fn_calculate_data_quality_score(
                @crypto_id, @name, @symbol, @price_usd, @market_cap_usd, 
                @volume_24h_usd, @percent_change_24h, @cmc_rank
            );
            
            -- Only insert records that meet minimum quality threshold
            IF @quality_score >= @min_quality_score
            BEGIN
                BEGIN TRY
                    INSERT INTO silver.crypto_clean_data (
                        crypto_id, name, symbol, slug, cmc_rank,
                        circulating_supply, total_supply, max_supply,
                        price_usd, volume_24h_usd, market_cap_usd,
                        percent_change_1h, percent_change_24h, percent_change_7d,
                        percent_change_30d, percent_change_60d, percent_change_90d,
                        volume_change_24h, market_cap_dominance, fully_diluted_market_cap,
                        tvl, last_updated, processed_timestamp, data_quality_score,
                        bronze_source_id, is_active
                    )
                    VALUES (
                        @crypto_id, @name, @symbol, @slug, @cmc_rank,
                        @circulating_supply, @total_supply, @max_supply,
                        @price_usd, @volume_24h_usd, @market_cap_usd,
                        @percent_change_1h, @percent_change_24h, @percent_change_7d,
                        @percent_change_30d, @percent_change_60d, @percent_change_90d,
                        @volume_change_24h, @market_cap_dominance, @fully_diluted_market_cap,
                        @tvl, @last_updated, GETDATE(), @quality_score,
                        @bronze_id, 1
                    );
                    
                    SET @records_inserted = @records_inserted + 1;
                    
                    -- Log individual quality metrics if score is below 0.9
                    IF @quality_score < 0.90
                    BEGIN
                        DECLARE @silver_id BIGINT = SCOPE_IDENTITY();
                        
                        INSERT INTO silver.data_quality_metrics (silver_record_id, metric_name, metric_value, threshold_passed, notes)
                        VALUES (@silver_id, 'Overall_Quality_Score', @quality_score, 
                                CASE WHEN @quality_score >= 0.80 THEN 1 ELSE 0 END,
                                CONCAT('Quality score: ', @quality_score, ' for symbol: ', @symbol));
                    END
                    
                END TRY
                BEGIN CATCH
                    SET @records_failed = @records_failed + 1;
                END CATCH
            END
            ELSE
            BEGIN
                SET @records_failed = @records_failed + 1;
            END
            
            FETCH NEXT FROM bronze_cursor INTO
                @bronze_id, @crypto_id, @name, @symbol, @slug, @cmc_rank,
                @circulating_supply, @total_supply, @max_supply,
                @price_usd, @volume_24h_usd, @market_cap_usd,
                @percent_change_1h, @percent_change_24h, @percent_change_7d,
                @percent_change_30d, @percent_change_60d, @percent_change_90d,
                @volume_change_24h, @market_cap_dominance, @fully_diluted_market_cap,
                @tvl, @last_updated, @collection_timestamp;
        END
        
        CLOSE bronze_cursor;
        DEALLOCATE bronze_cursor;
        
        -- Update ETL job log with success
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'SUCCESS',
            records_processed = @records_processed,
            records_inserted = @records_inserted,
            records_failed = @records_failed
        WHERE id = @job_id;
        
        -- Return summary
        SELECT 
            @job_id AS etl_job_id,
            @batch_id AS batch_id,
            'SUCCESS' AS status,
            @records_processed AS records_processed,
            @records_inserted AS records_inserted,
            @records_failed AS records_failed,
            DATEDIFF(SECOND, @start_time, GETDATE()) AS duration_seconds,
            CASE 
                WHEN @records_processed > 0 THEN 
                    CAST((@records_inserted * 100.0) / @records_processed AS DECIMAL(5,2))
                ELSE 0 
            END AS success_rate_pct;
        
    END TRY
    BEGIN CATCH
        -- Handle errors
        IF CURSOR_STATUS('global', 'bronze_cursor') >= 0
        BEGIN
            CLOSE bronze_cursor;
            DEALLOCATE bronze_cursor;
        END
        
        -- Update ETL job log with error
        UPDATE dbo.etl_job_log 
        SET 
            end_time = GETDATE(),
            status = 'ERROR',
            records_processed = @records_processed,
            records_inserted = @records_inserted,
            records_failed = @records_failed,
            error_message = ERROR_MESSAGE()
        WHERE id = @job_id;
        
        -- Return error details
        SELECT 
            @job_id AS etl_job_id,
            @batch_id AS batch_id,
            'ERROR' AS status,
            @records_processed AS records_processed,
            @records_inserted AS records_inserted,
            @records_failed AS records_failed,
            DATEDIFF(SECOND, @start_time, GETDATE()) AS duration_seconds,
            ERROR_MESSAGE() AS error_message;
    END CATCH
END;
GO

-- =====================================================
-- CREATE DAILY SNAPSHOTS PROCEDURE
-- =====================================================

CREATE OR ALTER PROCEDURE silver.sp_create_daily_snapshots
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
    VALUES ('Silver Daily Snapshots', 'silver', 'silver', @start_time, 'RUNNING');
    
    SET @job_id = SCOPE_IDENTITY();
    
    BEGIN TRY
        -- Create or update daily snapshots
        MERGE silver.crypto_daily_snapshots AS target
        USING (
            SELECT 
                s.symbol,
                @target_date AS snapshot_date,
                MIN(s.price_usd) AS low_price,
                MAX(s.price_usd) AS high_price,
                AVG(s.price_usd) AS avg_price,
                FIRST_VALUE(s.price_usd) OVER (PARTITION BY s.symbol ORDER BY s.processed_timestamp) AS opening_price,
                LAST_VALUE(s.price_usd) OVER (PARTITION BY s.symbol ORDER BY s.processed_timestamp 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS closing_price,
                AVG(s.volume_24h_usd) AS total_volume_24h,
                AVG(s.market_cap_usd) AS market_cap_close,
                AVG(s.percent_change_24h) AS price_change_24h,
                AVG(s.volume_change_24h) AS volume_change_24h,
                COUNT(*) AS records_processed,
                AVG(s.data_quality_score) AS quality_score_avg
            FROM silver.crypto_clean_data s
            WHERE CAST(s.processed_timestamp AS DATE) = @target_date
                AND s.is_active = 1
            GROUP BY s.symbol
        ) AS source ON target.symbol = source.symbol AND target.snapshot_date = source.snapshot_date
        
        WHEN MATCHED THEN
            UPDATE SET
                opening_price = source.opening_price,
                closing_price = source.closing_price,
                high_price = source.high_price,
                low_price = source.low_price,
                avg_price = source.avg_price,
                total_volume_24h = source.total_volume_24h,
                market_cap_close = source.market_cap_close,
                price_change_24h = source.price_change_24h,
                volume_change_24h = source.volume_change_24h,
                records_processed = source.records_processed,
                quality_score_avg = source.quality_score_avg,
                created_timestamp = GETDATE()
        
        WHEN NOT MATCHED THEN
            INSERT (symbol, snapshot_date, opening_price, closing_price, high_price, low_price,
                    avg_price, total_volume_24h, market_cap_close, price_change_24h, 
                    volume_change_24h, records_processed, quality_score_avg)
            VALUES (source.symbol, source.snapshot_date, source.opening_price, source.closing_price,
                    source.high_price, source.low_price, source.avg_price, source.total_volume_24h,
                    source.market_cap_close, source.price_change_24h, source.volume_change_24h,
                    source.records_processed, source.quality_score_avg);
        
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
            @target_date AS snapshot_date,
            @records_processed AS snapshots_created,
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
            @target_date AS snapshot_date,
            0 AS snapshots_created,
            ERROR_MESSAGE() AS error_message;
    END CATCH
END;
GO

-- =====================================================
-- SILVER LAYER MONITORING PROCEDURES
-- =====================================================

CREATE OR ALTER PROCEDURE silver.sp_data_quality_dashboard
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Overall quality metrics
    SELECT 
        'Silver Layer Quality Dashboard' AS dashboard_section,
        COUNT(*) AS total_clean_records,
        COUNT(DISTINCT symbol) AS unique_symbols,
        AVG(data_quality_score) AS avg_quality_score,
        MIN(data_quality_score) AS min_quality_score,
        MAX(data_quality_score) AS max_quality_score,
        COUNT(*) FILTER (WHERE data_quality_score >= 0.95) AS excellent_quality_count,
        COUNT(*) FILTER (WHERE data_quality_score >= 0.80) AS good_quality_count,
        COUNT(*) FILTER (WHERE data_quality_score < 0.60) AS poor_quality_count,
        MIN(processed_timestamp) AS oldest_record,
        MAX(processed_timestamp) AS newest_record
    FROM silver.crypto_clean_data
    WHERE is_active = 1;
    
    -- Quality by symbol
    SELECT 
        'Quality by Symbol (Top 20)' AS dashboard_section,
        symbol,
        COUNT(*) AS record_count,
        AVG(data_quality_score) AS avg_quality_score,
        MIN(data_quality_score) AS min_quality_score,
        MAX(processed_timestamp) AS latest_update
    FROM silver.crypto_clean_data
    WHERE is_active = 1
    GROUP BY symbol
    ORDER BY COUNT(*) DESC, AVG(data_quality_score) DESC;
    
    -- Recent processing activity
    SELECT 
        'Recent ETL Activity' AS dashboard_section,
        job_name,
        start_time,
        end_time,
        status,
        records_processed,
        records_inserted,
        CASE 
            WHEN records_processed > 0 THEN 
                CAST((records_inserted * 100.0) / records_processed AS DECIMAL(5,2))
            ELSE 0 
        END AS success_rate_pct,
        execution_duration_seconds
    FROM dbo.etl_job_log
    WHERE target_layer = 'silver'
        AND start_time >= DATEADD(DAY, -7, GETDATE())
    ORDER BY start_time DESC;
END;
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '✅ Silver Layer ETL Procedures Created Successfully:';
PRINT '   • fn_calculate_data_quality_score - Quality scoring function';
PRINT '   • sp_process_bronze_to_silver - Main Bronze→Silver ETL';
PRINT '   • sp_create_daily_snapshots - Daily aggregation procedure';
PRINT '   • sp_data_quality_dashboard - Quality monitoring dashboard';
PRINT '';
PRINT '🔄 ETL Flow: Bronze → Silver (Raw Data → Clean Data)';
PRINT '📊 Features: Quality scoring, validation, daily snapshots';
PRINT '🚀 Ready for Gold layer ETL procedures!';
GO