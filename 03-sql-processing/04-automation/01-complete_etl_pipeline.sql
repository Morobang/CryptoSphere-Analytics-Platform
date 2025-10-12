-- =====================================================
-- COMPLETE ETL AUTOMATION PIPELINE
-- =====================================================
-- Purpose: End-to-end automation of the entire medallion architecture
-- Flow: API → Bronze → Silver → Gold
-- Server: SQL Server (DESKTOP-939GPCA)
-- Usage: Single procedure call to run the complete data pipeline
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- MASTER ETL PIPELINE PROCEDURE
-- =====================================================

CREATE OR ALTER PROCEDURE etl.sp_run_complete_medallion_pipeline
    @process_date DATE = NULL,
    @cleanup_old_data BIT = 0,
    @cleanup_days INT = 90
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @process_date IS NULL
        SET @process_date = CAST(GETDATE() AS DATE);
    
    DECLARE @pipeline_start DATETIME2 = GETDATE();
    DECLARE @step_start DATETIME2;
    DECLARE @step_duration INT;
    DECLARE @total_errors INT = 0;
    DECLARE @pipeline_id UNIQUEIDENTIFIER = NEWID();
    
    -- Create pipeline execution log
    CREATE TABLE #pipeline_log (
        step_order INT,
        step_name NVARCHAR(100),
        start_time DATETIME2,
        end_time DATETIME2,
        duration_seconds INT,
        status NVARCHAR(20),
        records_processed INT,
        error_message NVARCHAR(MAX)
    );
    
    PRINT '🚀 ====================================================';
    PRINT '   CRYPTOSPHERE MEDALLION ARCHITECTURE PIPELINE';
    PRINT '   Complete ETL: API → Bronze → Silver → Gold';
    PRINT '====================================================';
    PRINT CONCAT('📅 Processing Date: ', @process_date);
    PRINT CONCAT('🆔 Pipeline ID: ', @pipeline_id);
    PRINT CONCAT('⏰ Start Time: ', @pipeline_start);
    PRINT '';
    
    -- =====================================================
    -- STEP 1: BRONZE LAYER PROCESSING
    -- =====================================================
    
    SET @step_start = GETDATE();
    PRINT '🥉 STEP 1: Bronze Layer - Raw Data Processing';
    PRINT '   • Assuming API data has been inserted via Python notebook';
    PRINT '   • Running Bronze layer quality checks...';
    
    BEGIN TRY
        -- Run Bronze layer data quality check
        DECLARE @bronze_records INT = 0;
        SELECT @bronze_records = COUNT(*) 
        FROM bronze.crypto_raw_data 
        WHERE CAST(collection_timestamp AS DATE) = @process_date;
        
        EXEC bronze.sp_data_quality_check;
        
        SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
        
        INSERT INTO #pipeline_log VALUES (
            1, 'Bronze Layer Processing', @step_start, GETDATE(), @step_duration, 
            'SUCCESS', @bronze_records, NULL
        );
        
        PRINT CONCAT('   ✅ Bronze layer processed: ', @bronze_records, ' records');
        PRINT CONCAT('   ⏱️  Duration: ', @step_duration, ' seconds');
        
    END TRY
    BEGIN CATCH
        SET @total_errors = @total_errors + 1;
        SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
        
        INSERT INTO #pipeline_log VALUES (
            1, 'Bronze Layer Processing', @step_start, GETDATE(), @step_duration, 
            'ERROR', 0, ERROR_MESSAGE()
        );
        
        PRINT CONCAT('   ❌ Bronze layer error: ', ERROR_MESSAGE());
    END CATCH
    
    PRINT '';
    
    -- =====================================================
    -- STEP 2: SILVER LAYER ETL (BRONZE → SILVER)
    -- =====================================================
    
    SET @step_start = GETDATE();
    PRINT '🥈 STEP 2: Silver Layer - Data Cleaning & Validation';
    PRINT '   • Processing Bronze → Silver ETL...';
    
    BEGIN TRY
        DECLARE @silver_job_id BIGINT;
        DECLARE @silver_processed INT = 0;
        DECLARE @silver_inserted INT = 0;
        
        -- Run Bronze to Silver ETL
        CREATE TABLE #silver_results (
            etl_job_id BIGINT,
            batch_id UNIQUEIDENTIFIER,
            status NVARCHAR(20),
            records_processed INT,
            records_inserted INT,
            records_failed INT,
            duration_seconds INT,
            success_rate_pct DECIMAL(5,2)
        );
        
        INSERT INTO #silver_results
        EXEC silver.sp_process_bronze_to_silver @batch_size = 5000, @min_quality_score = 0.60;
        
        SELECT 
            @silver_job_id = etl_job_id,
            @silver_processed = records_processed,
            @silver_inserted = records_inserted
        FROM #silver_results;
        
        -- Create daily snapshots
        EXEC silver.sp_create_daily_snapshots @target_date = @process_date;
        
        SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
        
        INSERT INTO #pipeline_log VALUES (
            2, 'Silver Layer ETL', @step_start, GETDATE(), @step_duration, 
            'SUCCESS', @silver_inserted, NULL
        );
        
        PRINT CONCAT('   ✅ Silver ETL completed: ', @silver_inserted, ' records processed');
        PRINT CONCAT('   📊 Daily snapshots created');
        PRINT CONCAT('   ⏱️  Duration: ', @step_duration, ' seconds');
        
        DROP TABLE #silver_results;
        
    END TRY
    BEGIN CATCH
        SET @total_errors = @total_errors + 1;
        SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
        
        INSERT INTO #pipeline_log VALUES (
            2, 'Silver Layer ETL', @step_start, GETDATE(), @step_duration, 
            'ERROR', 0, ERROR_MESSAGE()
        );
        
        PRINT CONCAT('   ❌ Silver ETL error: ', ERROR_MESSAGE());
        
        IF OBJECT_ID('tempdb..#silver_results') IS NOT NULL
            DROP TABLE #silver_results;
    END CATCH
    
    PRINT '';
    
    -- =====================================================
    -- STEP 3: GOLD LAYER ETL (SILVER → GOLD)
    -- =====================================================
    
    SET @step_start = GETDATE();
    PRINT '🥇 STEP 3: Gold Layer - Analytics & Business Intelligence';
    PRINT '   • Processing Silver → Gold ETL...';
    
    BEGIN TRY
        -- Run complete Gold layer ETL
        CREATE TABLE #gold_results (
            status NVARCHAR(50),
            processing_date DATE,
            total_duration_seconds INT,
            completion_time DATETIME2
        );
        
        INSERT INTO #gold_results
        EXEC gold.sp_run_complete_gold_etl @target_date = @process_date;
        
        DECLARE @gold_duration INT;
        SELECT @gold_duration = total_duration_seconds FROM #gold_results;
        
        SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
        
        INSERT INTO #pipeline_log VALUES (
            3, 'Gold Layer ETL', @step_start, GETDATE(), @step_duration, 
            'SUCCESS', 0, NULL
        );
        
        PRINT '   ✅ Gold ETL completed:';
        PRINT '      📊 Market overview generated';
        PRINT '      📈 Technical indicators calculated';
        PRINT '      ⚡ Trading signals created';
        PRINT '      🤖 ML features engineered';
        PRINT CONCAT('   ⏱️  Duration: ', @step_duration, ' seconds');
        
        DROP TABLE #gold_results;
        
    END TRY
    BEGIN CATCH
        SET @total_errors = @total_errors + 1;
        SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
        
        INSERT INTO #pipeline_log VALUES (
            3, 'Gold Layer ETL', @step_start, GETDATE(), @step_duration, 
            'ERROR', 0, ERROR_MESSAGE()
        );
        
        PRINT CONCAT('   ❌ Gold ETL error: ', ERROR_MESSAGE());
        
        IF OBJECT_ID('tempdb..#gold_results') IS NOT NULL
            DROP TABLE #gold_results;
    END CATCH
    
    PRINT '';
    
    -- =====================================================
    -- STEP 4: DATA CLEANUP (OPTIONAL)
    -- =====================================================
    
    IF @cleanup_old_data = 1
    BEGIN
        SET @step_start = GETDATE();
        PRINT '🧹 STEP 4: Data Cleanup';
        PRINT CONCAT('   • Cleaning data older than ', @cleanup_days, ' days...');
        
        BEGIN TRY
            CREATE TABLE #cleanup_results (
                status NVARCHAR(20),
                records_deleted INT,
                cutoff_date DATETIME2,
                message NVARCHAR(500)
            );
            
            INSERT INTO #cleanup_results
            EXEC bronze.sp_cleanup_old_data @days_to_keep = @cleanup_days;
            
            DECLARE @deleted_count INT;
            SELECT @deleted_count = records_deleted FROM #cleanup_results;
            
            SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
            
            INSERT INTO #pipeline_log VALUES (
                4, 'Data Cleanup', @step_start, GETDATE(), @step_duration, 
                'SUCCESS', @deleted_count, NULL
            );
            
            PRINT CONCAT('   ✅ Cleanup completed: ', @deleted_count, ' old records removed');
            PRINT CONCAT('   ⏱️  Duration: ', @step_duration, ' seconds');
            
            DROP TABLE #cleanup_results;
            
        END TRY
        BEGIN CATCH
            SET @total_errors = @total_errors + 1;
            SET @step_duration = DATEDIFF(SECOND, @step_start, GETDATE());
            
            INSERT INTO #pipeline_log VALUES (
                4, 'Data Cleanup', @step_start, GETDATE(), @step_duration, 
                'ERROR', 0, ERROR_MESSAGE()
            );
            
            PRINT CONCAT('   ❌ Cleanup error: ', ERROR_MESSAGE());
            
            IF OBJECT_ID('tempdb..#cleanup_results') IS NOT NULL
                DROP TABLE #cleanup_results;
        END CATCH
        
        PRINT '';
    END
    
    -- =====================================================
    -- PIPELINE COMPLETION SUMMARY
    -- =====================================================
    
    DECLARE @total_duration INT = DATEDIFF(SECOND, @pipeline_start, GETDATE());
    DECLARE @success_steps INT = (SELECT COUNT(*) FROM #pipeline_log WHERE status = 'SUCCESS');
    DECLARE @total_steps INT = (SELECT COUNT(*) FROM #pipeline_log);
    
    PRINT '📊 ====================================================';
    PRINT '   PIPELINE EXECUTION SUMMARY';
    PRINT '====================================================';
    PRINT CONCAT('🆔 Pipeline ID: ', @pipeline_id);
    PRINT CONCAT('📅 Processing Date: ', @process_date);
    PRINT CONCAT('⏰ Total Duration: ', @total_duration, ' seconds (', @total_duration/60.0, ' minutes)');
    PRINT CONCAT('✅ Successful Steps: ', @success_steps, '/', @total_steps);
    PRINT CONCAT('❌ Failed Steps: ', @total_errors);
    PRINT CONCAT('📈 Overall Status: ', CASE WHEN @total_errors = 0 THEN 'SUCCESS' ELSE 'PARTIAL_SUCCESS' END);
    PRINT '';
    
    -- Show detailed step results
    SELECT 
        step_order,
        step_name,
        FORMAT(start_time, 'HH:mm:ss') AS start_time,
        FORMAT(end_time, 'HH:mm:ss') AS end_time,
        duration_seconds,
        status,
        records_processed,
        CASE WHEN error_message IS NOT NULL THEN LEFT(error_message, 100) + '...' ELSE NULL END AS error_summary
    FROM #pipeline_log
    ORDER BY step_order;
    
    -- Final statistics
    PRINT '📊 FINAL MEDALLION ARCHITECTURE STATISTICS:';
    
    -- Bronze Layer Stats
    DECLARE @bronze_total INT;
    SELECT @bronze_total = COUNT(*) FROM bronze.crypto_raw_data 
    WHERE CAST(collection_timestamp AS DATE) = @process_date;
    PRINT CONCAT('   🥉 Bronze Layer: ', @bronze_total, ' raw records');
    
    -- Silver Layer Stats
    DECLARE @silver_total INT, @silver_quality DECIMAL(3,2);
    SELECT 
        @silver_total = COUNT(*),
        @silver_quality = AVG(data_quality_score)
    FROM silver.crypto_clean_data 
    WHERE CAST(processed_timestamp AS DATE) = @process_date;
    PRINT CONCAT('   🥈 Silver Layer: ', @silver_total, ' clean records (avg quality: ', FORMAT(@silver_quality, 'N2'), ')');
    
    -- Gold Layer Stats
    DECLARE @gold_market INT, @gold_signals INT, @gold_ml INT;
    SELECT @gold_market = COUNT(*) FROM gold.market_overview_daily WHERE report_date = @process_date;
    SELECT @gold_signals = COUNT(*) FROM gold.trading_signals WHERE CAST(signal_date AS DATE) = @process_date;
    SELECT @gold_ml = COUNT(*) FROM gold.ml_features WHERE feature_date = @process_date;
    
    PRINT CONCAT('   🥇 Gold Layer: ', @gold_market, ' market reports, ', @gold_signals, ' trading signals, ', @gold_ml, ' ML features');
    
    PRINT '';
    PRINT CASE 
        WHEN @total_errors = 0 THEN '🎉 MEDALLION ARCHITECTURE PIPELINE COMPLETED SUCCESSFULLY!'
        ELSE '⚠️  PIPELINE COMPLETED WITH SOME ERRORS - CHECK LOGS'
    END;
    PRINT '====================================================';
    
    -- Return summary for external systems
    SELECT 
        @pipeline_id AS pipeline_id,
        @process_date AS processing_date,
        @total_duration AS total_duration_seconds,
        @success_steps AS successful_steps,
        @total_steps AS total_steps,
        @total_errors AS error_count,
        CASE WHEN @total_errors = 0 THEN 'SUCCESS' ELSE 'PARTIAL_SUCCESS' END AS overall_status,
        @bronze_total AS bronze_records,
        @silver_total AS silver_records,
        @gold_signals AS trading_signals_generated,
        @pipeline_start AS start_time,
        GETDATE() AS end_time
    FROM (VALUES (1)) AS dummy(x); -- Ensure single row result
    
    -- Cleanup
    DROP TABLE #pipeline_log;
END;
GO

-- =====================================================
-- SCHEDULED DAILY PIPELINE (EXAMPLE)
-- =====================================================

CREATE OR ALTER PROCEDURE etl.sp_daily_scheduled_pipeline
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @today DATE = CAST(GETDATE() AS DATE);
    
    PRINT CONCAT('🔄 Running Daily Scheduled Pipeline for ', @today);
    
    -- Run the complete pipeline with cleanup
    EXEC etl.sp_run_complete_medallion_pipeline 
        @process_date = @today,
        @cleanup_old_data = 1,
        @cleanup_days = 90;
        
    PRINT '✅ Daily scheduled pipeline completed';
END;
GO

-- =====================================================
-- PIPELINE MONITORING & HEALTH CHECK
-- =====================================================

CREATE OR ALTER PROCEDURE etl.sp_pipeline_health_check
AS
BEGIN
    SET NOCOUNT ON;
    
    PRINT '🏥 MEDALLION ARCHITECTURE HEALTH CHECK';
    PRINT '====================================';
    
    -- Check last ETL job executions
    PRINT '📊 Recent ETL Job Status:';
    SELECT TOP 10
        job_name,
        FORMAT(start_time, 'yyyy-MM-dd HH:mm:ss') AS start_time,
        status,
        records_processed,
        execution_duration_seconds AS duration_sec,
        CASE WHEN error_message IS NOT NULL THEN LEFT(error_message, 50) + '...' ELSE 'OK' END AS status_detail
    FROM dbo.etl_job_log
    ORDER BY start_time DESC;
    
    -- Data freshness check
    PRINT '';
    PRINT '📅 Data Freshness Check:';
    SELECT 
        'Bronze Layer' AS layer,
        MAX(collection_timestamp) AS latest_data,
        DATEDIFF(HOUR, MAX(collection_timestamp), GETDATE()) AS hours_behind
    FROM bronze.crypto_raw_data
    UNION ALL
    SELECT 
        'Silver Layer' AS layer,
        MAX(processed_timestamp) AS latest_data,
        DATEDIFF(HOUR, MAX(processed_timestamp), GETDATE()) AS hours_behind
    FROM silver.crypto_clean_data
    UNION ALL
    SELECT 
        'Gold Layer' AS layer,
        MAX(created_timestamp) AS latest_data,
        DATEDIFF(HOUR, MAX(created_timestamp), GETDATE()) AS hours_behind
    FROM gold.trading_signals;
    
    -- Data quality summary
    PRINT '';
    PRINT '🎯 Data Quality Summary:';
    SELECT 
        COUNT(*) AS total_silver_records,
        AVG(data_quality_score) AS avg_quality_score,
        COUNT(*) FILTER (WHERE data_quality_score >= 0.90) AS excellent_quality,
        COUNT(*) FILTER (WHERE data_quality_score < 0.60) AS poor_quality,
        COUNT(DISTINCT symbol) AS unique_symbols
    FROM silver.crypto_clean_data
    WHERE processed_timestamp >= DATEADD(DAY, -1, GETDATE());
    
    PRINT '';
    PRINT '✅ Health check completed';
END;
GO

-- =====================================================
-- CREATE ETL SCHEMA
-- =====================================================

-- Create ETL schema for automation procedures
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'etl')
BEGIN
    EXEC('CREATE SCHEMA etl');
    PRINT '✅ Schema [etl] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Schema [etl] already exists';
END
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '✅ Complete ETL Automation Pipeline Created Successfully!';
PRINT '';
PRINT '🚀 AVAILABLE PROCEDURES:';
PRINT '   • etl.sp_run_complete_medallion_pipeline - Master pipeline';
PRINT '   • etl.sp_daily_scheduled_pipeline - Daily automation';
PRINT '   • etl.sp_pipeline_health_check - Health monitoring';
PRINT '';
PRINT '💡 USAGE EXAMPLES:';
PRINT '   -- Run complete pipeline for today';
PRINT '   EXEC etl.sp_run_complete_medallion_pipeline;';
PRINT '';
PRINT '   -- Run with cleanup';
PRINT '   EXEC etl.sp_run_complete_medallion_pipeline @cleanup_old_data = 1;';
PRINT '';
PRINT '   -- Health check';
PRINT '   EXEC etl.sp_pipeline_health_check;';
PRINT '';
PRINT '🎉 MEDALLION ARCHITECTURE AUTOMATION COMPLETE!';
GO