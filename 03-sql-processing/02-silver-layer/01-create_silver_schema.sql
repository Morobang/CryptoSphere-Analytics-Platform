USE cryptosphere_analytics;
GO

-- =====================================================
-- SILVER SCHEMA CREATION
-- =====================================================

-- Silver Layer Schema (Clean Data)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'silver')
BEGIN
    EXEC('CREATE SCHEMA silver');
    PRINT '✅ Schema [silver] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Schema [silver] already exists';
END
GO

-- =====================================================
-- SILVER LAYER TABLES
-- =====================================================

-- Silver Layer: Clean Cryptocurrency Data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'crypto_clean_data' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.crypto_clean_data (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        crypto_id INT NOT NULL,
        name NVARCHAR(100) NOT NULL,
        symbol NVARCHAR(20) NOT NULL,
        slug NVARCHAR(100),
        cmc_rank INT,
        circulating_supply DECIMAL(30,8),
        total_supply DECIMAL(30,8),
        max_supply DECIMAL(30,8),
        price_usd DECIMAL(18,8) NOT NULL,
        volume_24h_usd DECIMAL(25,2),
        market_cap_usd DECIMAL(25,2),
        percent_change_1h DECIMAL(10,4),
        percent_change_24h DECIMAL(10,4),
        percent_change_7d DECIMAL(10,4),
        percent_change_30d DECIMAL(10,4),
        percent_change_60d DECIMAL(10,4),
        percent_change_90d DECIMAL(10,4),
        volume_change_24h DECIMAL(10,4),
        market_cap_dominance DECIMAL(8,4),
        fully_diluted_market_cap DECIMAL(25,2),
        tvl DECIMAL(25,2),
        last_updated DATETIME2,
        processed_timestamp DATETIME2 DEFAULT GETDATE(),
        data_quality_score DECIMAL(3,2), -- 0.00 to 1.00
        bronze_source_id BIGINT,
        is_active BIT DEFAULT 1,
        FOREIGN KEY (bronze_source_id) REFERENCES bronze.crypto_raw_data(id)
    );
    
    -- Create indexes
    CREATE INDEX IX_silver_crypto_clean_symbol ON silver.crypto_clean_data(symbol);
    CREATE INDEX IX_silver_crypto_clean_timestamp ON silver.crypto_clean_data(processed_timestamp);
    CREATE INDEX IX_silver_crypto_clean_quality ON silver.crypto_clean_data(data_quality_score);
    CREATE INDEX IX_silver_crypto_clean_crypto_id ON silver.crypto_clean_data(crypto_id);
    CREATE INDEX IX_silver_crypto_clean_active ON silver.crypto_clean_data(is_active);
    
    PRINT '✅ Table [silver.crypto_clean_data] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [silver.crypto_clean_data] already exists';
END
GO

-- Silver Layer: Data Quality Metrics
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'data_quality_metrics' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.data_quality_metrics (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        silver_record_id BIGINT,
        metric_name NVARCHAR(100),
        metric_value DECIMAL(5,4), -- 0.0000 to 1.0000
        threshold_passed BIT,
        validation_timestamp DATETIME2 DEFAULT GETDATE(),
        notes NVARCHAR(500),
        FOREIGN KEY (silver_record_id) REFERENCES silver.crypto_clean_data(id)
    );
    
    CREATE INDEX IX_silver_quality_metrics_record ON silver.data_quality_metrics(silver_record_id);
    CREATE INDEX IX_silver_quality_metrics_name ON silver.data_quality_metrics(metric_name);
    CREATE INDEX IX_silver_quality_metrics_timestamp ON silver.data_quality_metrics(validation_timestamp);
    
    PRINT '✅ Table [silver.data_quality_metrics] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [silver.data_quality_metrics] already exists';
END
GO

-- Silver Layer: Daily snapshots for historical analysis
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'crypto_daily_snapshots' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.crypto_daily_snapshots (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        symbol NVARCHAR(20) NOT NULL,
        snapshot_date DATE NOT NULL,
        opening_price DECIMAL(18,8),
        closing_price DECIMAL(18,8),
        high_price DECIMAL(18,8),
        low_price DECIMAL(18,8),
        avg_price DECIMAL(18,8),
        total_volume_24h DECIMAL(25,2),
        market_cap_close DECIMAL(25,2),
        price_change_24h DECIMAL(10,4),
        volume_change_24h DECIMAL(10,4),
        records_processed INT,
        quality_score_avg DECIMAL(3,2),
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (symbol, snapshot_date)
    );
    
    CREATE INDEX IX_silver_snapshots_symbol_date ON silver.crypto_daily_snapshots(symbol, snapshot_date);
    CREATE INDEX IX_silver_snapshots_date ON silver.crypto_daily_snapshots(snapshot_date);
    CREATE INDEX IX_silver_snapshots_quality ON silver.crypto_daily_snapshots(quality_score_avg);
    
    PRINT '✅ Table [silver.crypto_daily_snapshots] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [silver.crypto_daily_snapshots] already exists';
END
GO

-- Silver Layer: Data Validation Rules
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'validation_rules' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.validation_rules (
        id INT IDENTITY(1,1) PRIMARY KEY,
        rule_name NVARCHAR(100) NOT NULL,
        rule_description NVARCHAR(500),
        column_name NVARCHAR(100),
        rule_type NVARCHAR(50), -- NOT_NULL, POSITIVE, RANGE, PATTERN
        rule_parameters NVARCHAR(MAX), -- JSON configuration
        weight DECIMAL(3,2) DEFAULT 1.00, -- Importance weight in quality score
        is_active BIT DEFAULT 1,
        created_date DATETIME2 DEFAULT GETDATE(),
        UNIQUE (rule_name)
    );
    
    CREATE INDEX IX_silver_validation_rules_active ON silver.validation_rules(is_active);
    CREATE INDEX IX_silver_validation_rules_type ON silver.validation_rules(rule_type);
    
    PRINT '✅ Table [silver.validation_rules] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [silver.validation_rules] already exists';
END
GO

-- Silver Layer: Processing Audit Log
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'processing_audit_log' AND schema_id = SCHEMA_ID('silver'))
BEGIN
    CREATE TABLE silver.processing_audit_log (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        process_name NVARCHAR(100),
        bronze_batch_id UNIQUEIDENTIFIER,
        start_timestamp DATETIME2 DEFAULT GETDATE(),
        end_timestamp DATETIME2,
        records_input INT,
        records_output INT,
        records_rejected INT,
        avg_quality_score DECIMAL(3,2),
        process_status NVARCHAR(20), -- RUNNING, SUCCESS, FAILED
        error_details NVARCHAR(MAX),
        execution_duration_seconds AS DATEDIFF(SECOND, start_timestamp, end_timestamp)
    );
    
    CREATE INDEX IX_silver_audit_log_timestamp ON silver.processing_audit_log(start_timestamp);
    CREATE INDEX IX_silver_audit_log_batch ON silver.processing_audit_log(bronze_batch_id);
    CREATE INDEX IX_silver_audit_log_status ON silver.processing_audit_log(process_status);
    
    PRINT '✅ Table [silver.processing_audit_log] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [silver.processing_audit_log] already exists';
END
GO

-- =====================================================
-- INSERT DEFAULT VALIDATION RULES
-- =====================================================

-- Insert default validation rules if table is empty
IF NOT EXISTS (SELECT 1 FROM silver.validation_rules)
BEGIN
    PRINT '📋 Inserting default Silver layer validation rules...';
    
    INSERT INTO silver.validation_rules (rule_name, rule_description, column_name, rule_type, rule_parameters, weight) VALUES
    ('price_not_null', 'Price must not be null', 'price_usd', 'NOT_NULL', '{}', 1.00),
    ('price_positive', 'Price must be positive', 'price_usd', 'POSITIVE', '{}', 1.00),
    ('price_reasonable', 'Price must be within reasonable range', 'price_usd', 'RANGE', '{"min": 0.000001, "max": 10000000}', 0.80),
    ('symbol_not_null', 'Symbol must not be null', 'symbol', 'NOT_NULL', '{}', 1.00),
    ('symbol_format', 'Symbol must be valid format', 'symbol', 'PATTERN', '{"pattern": "^[A-Z0-9]{1,10}$"}', 0.70),
    ('name_not_null', 'Name must not be null', 'name', 'NOT_NULL', '{}', 0.90),
    ('market_cap_positive', 'Market cap must be positive if provided', 'market_cap_usd', 'POSITIVE_OR_NULL', '{}', 0.60),
    ('volume_non_negative', 'Volume must be non-negative if provided', 'volume_24h_usd', 'NON_NEGATIVE_OR_NULL', '{}', 0.60),
    ('change_24h_reasonable', '24h change must be within reasonable bounds', 'percent_change_24h', 'RANGE', '{"min": -99.99, "max": 10000}', 0.50),
    ('supply_consistency', 'Circulating supply should not exceed total supply', 'circulating_supply', 'SUPPLY_CONSISTENCY', '{}', 0.40);
    
    PRINT '✅ Default Silver layer validation rules inserted successfully';
END
GO

