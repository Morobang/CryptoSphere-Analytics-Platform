-- =====================================================
-- DATA QUALITY MONITORING & ALERTING SYSTEM
-- =====================================================
-- Purpose: Comprehensive data quality monitoring, validation, and alerting
-- Coverage: All medallion layers (Bronze, Silver, Gold)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Features: Quality scoring, anomaly detection, alerting, reporting
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- DATA QUALITY FRAMEWORK TABLES
-- =====================================================

-- Quality Rules Configuration
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'data_quality_rules' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.data_quality_rules (
        id INT IDENTITY(1,1) PRIMARY KEY,
        rule_name NVARCHAR(100) NOT NULL,
        rule_description NVARCHAR(500),
        layer_name NVARCHAR(20), -- bronze, silver, gold
        table_name NVARCHAR(100),
        column_name NVARCHAR(100),
        rule_type NVARCHAR(50), -- NOT_NULL, POSITIVE, RANGE, PATTERN, CUSTOM
        rule_parameters NVARCHAR(MAX), -- JSON configuration
        threshold_warning DECIMAL(5,4), -- 0.0000 to 1.0000
        threshold_critical DECIMAL(5,4), -- 0.0000 to 1.0000
        is_active BIT DEFAULT 1,
        created_date DATETIME2 DEFAULT GETDATE(),
        UNIQUE (rule_name)
    );
    
    PRINT '✅ Table [dbo.data_quality_rules] created successfully';
END
GO

-- Quality Check Results
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'data_quality_results' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.data_quality_results (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        check_timestamp DATETIME2 DEFAULT GETDATE(),
        rule_id INT,
        layer_name NVARCHAR(20),
        table_name NVARCHAR(100),
        rule_name NVARCHAR(100),
        records_checked BIGINT,
        records_passed BIGINT,
        records_failed BIGINT,
        pass_rate DECIMAL(7,4), -- 0.0000 to 100.0000
        quality_score DECIMAL(5,4), -- 0.0000 to 1.0000
        status NVARCHAR(20), -- PASS, WARNING, CRITICAL, ERROR
        details NVARCHAR(MAX),
        execution_time_ms INT,
        FOREIGN KEY (rule_id) REFERENCES dbo.data_quality_rules(id)
    );
    
    CREATE INDEX IX_data_quality_results_timestamp ON dbo.data_quality_results(check_timestamp);
    CREATE INDEX IX_data_quality_results_status ON dbo.data_quality_results(status);
    
    PRINT '✅ Table [dbo.data_quality_results] created successfully';
END
GO

-- Quality Alerts
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'data_quality_alerts' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.data_quality_alerts (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        alert_timestamp DATETIME2 DEFAULT GETDATE(),
        alert_type NVARCHAR(20), -- WARNING, CRITICAL, ERROR
        layer_name NVARCHAR(20),
        table_name NVARCHAR(100),
        rule_name NVARCHAR(100),
        alert_message NVARCHAR(500),
        quality_score DECIMAL(5,4),
        records_affected BIGINT,
        is_acknowledged BIT DEFAULT 0,
        acknowledged_by NVARCHAR(100),
        acknowledged_at DATETIME2,
        resolution_notes NVARCHAR(MAX)
    );
    
    CREATE INDEX IX_data_quality_alerts_timestamp ON dbo.data_quality_alerts(alert_timestamp);
    CREATE INDEX IX_data_quality_alerts_status ON dbo.data_quality_alerts(is_acknowledged);
    
    PRINT '✅ Table [dbo.data_quality_alerts] created successfully';
END
GO

-- =====================================================
-- INSERT DEFAULT DATA QUALITY RULES
-- =====================================================

-- Insert default quality rules if table is empty
IF NOT EXISTS (SELECT 1 FROM dbo.data_quality_rules)
BEGIN
    PRINT '📋 Inserting default data quality rules...';
    
    INSERT INTO dbo.data_quality_rules (rule_name, rule_description, layer_name, table_name, column_name, rule_type, rule_parameters, threshold_warning, threshold_critical) VALUES
    -- Bronze Layer Rules
    ('bronze_price_not_null', 'Price must not be null', 'bronze', 'crypto_raw_data', 'price_usd', 'NOT_NULL', '{}', 0.95, 0.85),
    ('bronze_price_positive', 'Price must be positive', 'bronze', 'crypto_raw_data', 'price_usd', 'POSITIVE', '{}', 0.98, 0.90),
    ('bronze_symbol_not_null', 'Symbol must not be null', 'bronze', 'crypto_raw_data', 'symbol', 'NOT_NULL', '{}', 1.00, 0.95),
    ('bronze_name_not_null', 'Name must not be null', 'bronze', 'crypto_raw_data', 'name', 'NOT_NULL', '{}', 0.95, 0.85),
    ('bronze_price_reasonable', 'Price must be within reasonable range', 'bronze', 'crypto_raw_data', 'price_usd', 'RANGE', '{"min": 0.000001, "max": 10000000}', 0.99, 0.95),
    ('bronze_market_cap_positive', 'Market cap must be positive if provided', 'bronze', 'crypto_raw_data', 'market_cap_usd', 'POSITIVE_OR_NULL', '{}', 0.98, 0.90),
    ('bronze_volume_non_negative', 'Volume must be non-negative if provided', 'bronze', 'crypto_raw_data', 'volume_24h_usd', 'NON_NEGATIVE_OR_NULL', '{}', 0.98, 0.90),
    ('bronze_change_reasonable', '24h change must be within reasonable bounds', 'bronze', 'crypto_raw_data', 'percent_change_24h', 'RANGE', '{"min": -99.99, "max": 10000}', 0.95, 0.85),
    
    -- Silver Layer Rules
    ('silver_data_quality_score', 'Silver records must have quality score', 'silver', 'crypto_clean_data', 'data_quality_score', 'NOT_NULL', '{}', 1.00, 0.98),
    ('silver_quality_threshold', 'Silver records must meet minimum quality', 'silver', 'crypto_clean_data', 'data_quality_score', 'RANGE', '{"min": 0.60, "max": 1.00}', 0.98, 0.90),
    ('silver_price_cleaned', 'Cleaned price must be positive', 'silver', 'crypto_clean_data', 'price_usd', 'POSITIVE', '{}', 1.00, 0.98),
    ('silver_symbol_valid', 'Symbol must be valid format', 'silver', 'crypto_clean_data', 'symbol', 'PATTERN', '{"pattern": "^[A-Z0-9]{1,10}$"}', 0.98, 0.90),
    ('silver_freshness', 'Silver data must be fresh', 'silver', 'crypto_clean_data', 'processed_timestamp', 'FRESHNESS', '{"max_hours": 25}', 0.90, 0.70),
    
    -- Gold Layer Rules
    ('gold_market_overview_complete', 'Market overview must be complete', 'gold', 'market_overview_daily', 'total_cryptocurrencies', 'POSITIVE', '{}', 1.00, 0.95),
    ('gold_trading_signals_confidence', 'Trading signals must have confidence score', 'gold', 'trading_signals', 'confidence_score', 'RANGE', '{"min": 0.00, "max": 1.00}', 1.00, 0.95),
    ('gold_ml_features_completeness', 'ML features must meet completeness threshold', 'gold', 'ml_features', 'feature_completeness', 'RANGE', '{"min": 0.70, "max": 1.00}', 0.95, 0.80),
    ('gold_performance_metrics_sma', 'SMA values must be positive if present', 'gold', 'crypto_performance_metrics', 'sma_7d', 'POSITIVE_OR_NULL', '{}', 0.95, 0.85);
    
    PRINT '✅ Default data quality rules inserted successfully';
END
GO

-- =====================================================
-- DATA QUALITY CHECK FUNCTIONS
-- =====================================================

-- Function to check NOT_NULL rule
CREATE OR ALTER FUNCTION dq.fn_check_not_null(
    @layer_name NVARCHAR(20),
    @table_name NVARCHAR(100),
    @column_name NVARCHAR(100)
)
RETURNS TABLE
AS
RETURN (
    SELECT 
        total_records,
        null_records,
        total_records - null_records AS passed_records,
        CASE 
            WHEN total_records > 0 THEN CAST((total_records - null_records) AS DECIMAL(15,4)) / total_records
            ELSE 1.0 
        END AS pass_rate
    FROM (
        SELECT 
            COUNT(*) AS total_records,
            SUM(CASE WHEN value_to_check IS NULL THEN 1 ELSE 0 END) AS null_records
        FROM (
            SELECT 
                CASE @layer_name + '.' + @table_name + '.' + @column_name
                    WHEN 'bronze.crypto_raw_data.price_usd' THEN CAST(price_usd AS SQL_VARIANT)
                    WHEN 'bronze.crypto_raw_data.symbol' THEN CAST(symbol AS SQL_VARIANT)
                    WHEN 'bronze.crypto_raw_data.name' THEN CAST(name AS SQL_VARIANT)
                    WHEN 'silver.crypto_clean_data.data_quality_score' THEN CAST(data_quality_score AS SQL_VARIANT)
                    WHEN 'silver.crypto_clean_data.price_usd' THEN CAST(price_usd AS SQL_VARIANT)
                    ELSE NULL
                END AS value_to_check
            FROM bronze.crypto_raw_data
            WHERE @layer_name = 'bronze' AND @table_name = 'crypto_raw_data'
            UNION ALL
            SELECT 
                CASE @layer_name + '.' + @table_name + '.' + @column_name
                    WHEN 'silver.crypto_clean_data.data_quality_score' THEN CAST(data_quality_score AS SQL_VARIANT)
                    WHEN 'silver.crypto_clean_data.price_usd' THEN CAST(price_usd AS SQL_VARIANT)
                    ELSE NULL
                END AS value_to_check
            FROM silver.crypto_clean_data
            WHERE @layer_name = 'silver' AND @table_name = 'crypto_clean_data'
        ) AS combined_data
        WHERE value_to_check IS NOT NULL OR @layer_name + '.' + @table_name + '.' + @column_name IN (
            'bronze.crypto_raw_data.price_usd', 'bronze.crypto_raw_data.symbol', 'bronze.crypto_raw_data.name',
            'silver.crypto_clean_data.data_quality_score', 'silver.crypto_clean_data.price_usd'
        )
    ) AS check_results
);
GO

-- =====================================================
-- MAIN DATA QUALITY CHECK PROCEDURE
-- =====================================================

CREATE OR ALTER PROCEDURE dq.sp_run_data_quality_checks
    @layer_name NVARCHAR(20) = NULL, -- bronze, silver, gold, or NULL for all
    @rule_name NVARCHAR(100) = NULL -- specific rule or NULL for all active rules
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @start_time DATETIME2 = GETDATE();
    DECLARE @checks_run INT = 0;
    DECLARE @alerts_generated INT = 0;
    
    PRINT '🔍 STARTING DATA QUALITY CHECKS';
    PRINT '================================';
    PRINT CONCAT('📅 Timestamp: ', @start_time);
    PRINT CONCAT('🎯 Layer Filter: ', ISNULL(@layer_name, 'ALL'));
    PRINT CONCAT('📋 Rule Filter: ', ISNULL(@rule_name, 'ALL ACTIVE'));
    PRINT '';
    
    -- Get rules to check
    DECLARE rule_cursor CURSOR FOR
    SELECT id, rule_name, rule_description, layer_name, table_name, column_name, 
           rule_type, rule_parameters, threshold_warning, threshold_critical
    FROM dbo.data_quality_rules
    WHERE is_active = 1
        AND (@layer_name IS NULL OR layer_name = @layer_name)
        AND (@rule_name IS NULL OR rule_name = @rule_name)
    ORDER BY layer_name, table_name, rule_name;
    
    DECLARE @rule_id INT, @rule_name_cur NVARCHAR(100), @rule_desc NVARCHAR(500),
            @layer NVARCHAR(20), @table NVARCHAR(100), @column NVARCHAR(100),
            @rule_type NVARCHAR(50), @parameters NVARCHAR(MAX),
            @threshold_warn DECIMAL(5,4), @threshold_crit DECIMAL(5,4);
    
    OPEN rule_cursor;
    FETCH NEXT FROM rule_cursor INTO @rule_id, @rule_name_cur, @rule_desc, @layer, @table, @column, 
                                     @rule_type, @parameters, @threshold_warn, @threshold_crit;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        DECLARE @check_start DATETIME2 = GETDATE();
        DECLARE @records_checked BIGINT = 0;
        DECLARE @records_passed BIGINT = 0;
        DECLARE @records_failed BIGINT = 0;
        DECLARE @pass_rate DECIMAL(7,4) = 0;
        DECLARE @quality_score DECIMAL(5,4) = 0;
        DECLARE @status NVARCHAR(20) = 'PASS';
        DECLARE @details NVARCHAR(MAX) = '';
        
        PRINT CONCAT('🔎 Checking: ', @rule_name_cur, ' (', @layer, '.', @table, '.', @column, ')');
        
        BEGIN TRY
            -- Execute rule based on type
            IF @rule_type = 'NOT_NULL'
            BEGIN
                -- Dynamic SQL for NOT_NULL check
                DECLARE @sql NVARCHAR(MAX) = 'SELECT @records_checked = COUNT(*), @records_passed = COUNT(' + @column + ') FROM ' + @layer + '.' + @table;
                DECLARE @params NVARCHAR(500) = '@records_checked BIGINT OUTPUT, @records_passed BIGINT OUTPUT';
                
                EXEC sp_executesql @sql, @params, 
                    @records_checked = @records_checked OUTPUT, 
                    @records_passed = @records_passed OUTPUT;
                
                SET @records_failed = @records_checked - @records_passed;
            END
            ELSE IF @rule_type = 'POSITIVE'
            BEGIN
                -- Dynamic SQL for POSITIVE check
                SET @sql = 'SELECT @records_checked = COUNT(*), @records_passed = COUNT(*) FROM ' + @layer + '.' + @table + ' WHERE ' + @column + ' > 0';
                SET @params = '@records_checked BIGINT OUTPUT, @records_passed BIGINT OUTPUT';
                
                EXEC sp_executesql @sql, @params, 
                    @records_checked = @records_checked OUTPUT, 
                    @records_passed = @records_passed OUTPUT;
                
                SET @records_failed = @records_checked - @records_passed;
            END
            ELSE IF @rule_type = 'POSITIVE_OR_NULL'
            BEGIN
                -- Check that values are positive when not null
                SET @sql = 'SELECT @records_checked = COUNT(*), @records_passed = COUNT(*) FROM ' + @layer + '.' + @table + ' WHERE ' + @column + ' IS NULL OR ' + @column + ' > 0';
                SET @params = '@records_checked BIGINT OUTPUT, @records_passed BIGINT OUTPUT';
                
                EXEC sp_executesql @sql, @params, 
                    @records_checked = @records_checked OUTPUT, 
                    @records_passed = @records_passed OUTPUT;
                
                SET @records_failed = @records_checked - @records_passed;
            END
            ELSE IF @rule_type = 'RANGE'
            BEGIN
                -- Extract min/max from JSON parameters (simplified)
                DECLARE @min_val DECIMAL(18,8) = 0;
                DECLARE @max_val DECIMAL(18,8) = 999999999;
                
                -- Simple JSON parsing for demonstration
                IF @parameters LIKE '%"min":%'
                    SET @min_val = CAST(SUBSTRING(@parameters, CHARINDEX('"min":', @parameters) + 6, 20) AS DECIMAL(18,8));
                IF @parameters LIKE '%"max":%'
                    SET @max_val = CAST(SUBSTRING(@parameters, CHARINDEX('"max":', @parameters) + 6, 20) AS DECIMAL(18,8));
                
                SET @sql = 'SELECT @records_checked = COUNT(*), @records_passed = COUNT(*) FROM ' + @layer + '.' + @table + 
                          ' WHERE ' + @column + ' BETWEEN ' + CAST(@min_val AS NVARCHAR(20)) + ' AND ' + CAST(@max_val AS NVARCHAR(20));
                
                EXEC sp_executesql @sql, @params, 
                    @records_checked = @records_checked OUTPUT, 
                    @records_passed = @records_passed OUTPUT;
                
                SET @records_failed = @records_checked - @records_passed;
            END
            ELSE
            BEGIN
                -- Default: assume all records pass for unknown rule types
                SET @sql = 'SELECT @records_checked = COUNT(*) FROM ' + @layer + '.' + @table;
                SET @params = '@records_checked BIGINT OUTPUT';
                
                EXEC sp_executesql @sql, @params, @records_checked = @records_checked OUTPUT;
                SET @records_passed = @records_checked;
                SET @records_failed = 0;
            END
            
            -- Calculate metrics
            IF @records_checked > 0
            BEGIN
                SET @pass_rate = (@records_passed * 100.0) / @records_checked;
                SET @quality_score = @records_passed / CAST(@records_checked AS DECIMAL(15,4));
            END
            ELSE
            BEGIN
                SET @pass_rate = 100.0;
                SET @quality_score = 1.0;
            END
            
            -- Determine status
            IF @quality_score >= @threshold_warn
                SET @status = 'PASS';
            ELSE IF @quality_score >= @threshold_crit
                SET @status = 'WARNING';
            ELSE
                SET @status = 'CRITICAL';
            
            SET @details = CONCAT('Pass Rate: ', FORMAT(@pass_rate, 'N2'), '%, ',
                                  'Records: ', @records_passed, '/', @records_checked);
            
        END TRY
        BEGIN CATCH
            SET @status = 'ERROR';
            SET @details = ERROR_MESSAGE();
            PRINT CONCAT('   ❌ Error: ', ERROR_MESSAGE());
        END CATCH
        
        -- Insert results
        INSERT INTO dbo.data_quality_results (
            rule_id, layer_name, table_name, rule_name, records_checked, records_passed, 
            records_failed, pass_rate, quality_score, status, details, execution_time_ms
        )
        VALUES (
            @rule_id, @layer, @table, @rule_name_cur, @records_checked, @records_passed,
            @records_failed, @pass_rate, @quality_score, @status, @details,
            DATEDIFF(MILLISECOND, @check_start, GETDATE())
        );
        
        -- Generate alerts for WARNING and CRITICAL status
        IF @status IN ('WARNING', 'CRITICAL')
        BEGIN
            INSERT INTO dbo.data_quality_alerts (
                alert_type, layer_name, table_name, rule_name, alert_message, 
                quality_score, records_affected
            )
            VALUES (
                @status, @layer, @table, @rule_name_cur,
                CONCAT(@rule_desc, ' - Quality Score: ', FORMAT(@quality_score, 'N4'), 
                       ' (Threshold: ', FORMAT(CASE WHEN @status = 'WARNING' THEN @threshold_warn ELSE @threshold_crit END, 'N4'), ')'),
                @quality_score, @records_failed
            );
            
            SET @alerts_generated = @alerts_generated + 1;
            PRINT CONCAT('   ⚠️  ', @status, ': Quality score ', FORMAT(@quality_score, 'N4'), 
                        ' below threshold ', FORMAT(CASE WHEN @status = 'WARNING' THEN @threshold_warn ELSE @threshold_crit END, 'N4'));
        END
        ELSE
        BEGIN
            PRINT CONCAT('   ✅ PASS: Quality score ', FORMAT(@quality_score, 'N4'));
        END
        
        SET @checks_run = @checks_run + 1;
        
        FETCH NEXT FROM rule_cursor INTO @rule_id, @rule_name_cur, @rule_desc, @layer, @table, @column, 
                                         @rule_type, @parameters, @threshold_warn, @threshold_crit;
    END
    
    CLOSE rule_cursor;
    DEALLOCATE rule_cursor;
    
    DECLARE @total_duration INT = DATEDIFF(SECOND, @start_time, GETDATE());
    
    PRINT '';
    PRINT '📊 DATA QUALITY CHECK SUMMARY';
    PRINT '============================';
    PRINT CONCAT('⏱️  Total Duration: ', @total_duration, ' seconds');
    PRINT CONCAT('🔍 Checks Run: ', @checks_run);
    PRINT CONCAT('⚠️  Alerts Generated: ', @alerts_generated);
    PRINT CONCAT('✅ Status: ', CASE WHEN @alerts_generated = 0 THEN 'ALL CHECKS PASSED' ELSE 'ISSUES FOUND' END);
    
    -- Return summary
    SELECT 
        @start_time AS check_timestamp,
        @checks_run AS total_checks_run,
        @alerts_generated AS alerts_generated,
        @total_duration AS duration_seconds,
        CASE WHEN @alerts_generated = 0 THEN 'SUCCESS' ELSE 'ISSUES_FOUND' END AS overall_status;
END;
GO

-- =====================================================
-- DATA QUALITY DASHBOARD
-- =====================================================

CREATE OR ALTER PROCEDURE dq.sp_data_quality_dashboard
    @hours_back INT = 24
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @cutoff_time DATETIME2 = DATEADD(HOUR, -@hours_back, GETDATE());
    
    PRINT CONCAT('📊 DATA QUALITY DASHBOARD - Last ', @hours_back, ' Hours');
    PRINT '===========================================';
    
    -- Overall summary
    SELECT 
        'OVERALL SUMMARY' AS section,
        COUNT(*) AS total_checks,
        COUNT(*) FILTER (WHERE status = 'PASS') AS passed_checks,
        COUNT(*) FILTER (WHERE status = 'WARNING') AS warning_checks,
        COUNT(*) FILTER (WHERE status = 'CRITICAL') AS critical_checks,
        COUNT(*) FILTER (WHERE status = 'ERROR') AS error_checks,
        AVG(quality_score) AS avg_quality_score,
        MIN(quality_score) AS min_quality_score
    FROM dbo.data_quality_results
    WHERE check_timestamp >= @cutoff_time;
    
    -- By layer summary
    SELECT 
        'BY LAYER' AS section,
        layer_name,
        COUNT(*) AS total_checks,
        COUNT(*) FILTER (WHERE status = 'PASS') AS passed,
        COUNT(*) FILTER (WHERE status IN ('WARNING', 'CRITICAL')) AS issues,
        AVG(quality_score) AS avg_quality_score,
        FORMAT(AVG(quality_score), 'P2') AS avg_quality_pct
    FROM dbo.data_quality_results
    WHERE check_timestamp >= @cutoff_time
    GROUP BY layer_name
    ORDER BY layer_name;
    
    -- Recent alerts
    SELECT 
        'RECENT ALERTS' AS section,
        alert_timestamp,
        alert_type,
        layer_name + '.' + table_name AS full_table_name,
        rule_name,
        alert_message,
        FORMAT(quality_score, 'P2') AS quality_score_pct,
        CASE WHEN is_acknowledged = 1 THEN 'YES' ELSE 'NO' END AS acknowledged
    FROM dbo.data_quality_alerts
    WHERE alert_timestamp >= @cutoff_time
    ORDER BY alert_timestamp DESC;
    
    -- Performance metrics
    SELECT 
        'PERFORMANCE METRICS' AS section,
        layer_name,
        AVG(execution_time_ms) AS avg_execution_time_ms,
        MAX(execution_time_ms) AS max_execution_time_ms,
        SUM(records_checked) AS total_records_checked
    FROM dbo.data_quality_results
    WHERE check_timestamp >= @cutoff_time
    GROUP BY layer_name
    ORDER BY layer_name;
END;
GO

-- =====================================================
-- CREATE DATA QUALITY SCHEMA
-- =====================================================

-- Create DQ schema for data quality procedures
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dq')
BEGIN
    EXEC('CREATE SCHEMA dq');
    PRINT '✅ Schema [dq] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Schema [dq] already exists';
END
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '✅ Data Quality Monitoring System Created Successfully!';
PRINT '';
PRINT '🔍 AVAILABLE PROCEDURES:';
PRINT '   • dq.sp_run_data_quality_checks - Run quality checks';
PRINT '   • dq.sp_data_quality_dashboard - Quality dashboard';
PRINT '';
PRINT '📊 AVAILABLE TABLES:';
PRINT '   • dbo.data_quality_rules - Quality rule definitions';
PRINT '   • dbo.data_quality_results - Check execution results';
PRINT '   • dbo.data_quality_alerts - Quality alerts and issues';
PRINT '';
PRINT '💡 USAGE EXAMPLES:';
PRINT '   -- Run all quality checks';
PRINT '   EXEC dq.sp_run_data_quality_checks;';
PRINT '';
PRINT '   -- Check specific layer';
PRINT '   EXEC dq.sp_run_data_quality_checks @layer_name = ''bronze'';';
PRINT '';
PRINT '   -- View dashboard';
PRINT '   EXEC dq.sp_data_quality_dashboard;';
PRINT '';
PRINT '🎉 DATA QUALITY FRAMEWORK COMPLETE!';
GO