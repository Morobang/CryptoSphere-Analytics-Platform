USE cryptosphere_analytics;
GO

-- =====================================================
-- INSERT API STATUS DATA 
-- =====================================================

CREATE OR ALTER PROCEDURE bronze.sp_insert_api_status
    @timestamp DATETIME2,
    @error_code INT = 0,
    @error_message NVARCHAR(500) = NULL,
    @elapsed INT,
    @credit_count INT,
    @notice NVARCHAR(500) = NULL,
    @total_count INT,
    @api_endpoint NVARCHAR(500),
    @request_parameters NVARCHAR(1000) = NULL,
    @response_size_bytes INT = NULL,
    @records_processed INT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @batch_id UNIQUEIDENTIFIER = NEWID();
    
    BEGIN TRY
        INSERT INTO bronze.api_response_status (
            batch_id,
            timestamp,
            error_code,
            error_message,
            elapsed,
            credit_count,
            notice,
            total_count,
            collection_timestamp,
            api_endpoint,
            request_parameters,
            response_size_bytes,
            records_processed
        )
        VALUES (
            @batch_id,
            @timestamp,
            @error_code,
            @error_message,
            @elapsed,
            @credit_count,
            @notice,
            @total_count,
            GETDATE(),
            @api_endpoint,
            @request_parameters,
            @response_size_bytes,
            @records_processed
        );
        
        -- Return success information with batch_id for linking crypto data
        SELECT 
            SCOPE_IDENTITY() AS status_id,
            @batch_id AS batch_id,
            'SUCCESS' AS status,
            'API status inserted successfully into Bronze layer' AS message,
            @total_count AS total_cryptocurrencies,
            @credit_count AS credits_used;
        
    END TRY
    BEGIN CATCH
        -- Return error information
        SELECT 
            NULL AS status_id,
            @batch_id AS batch_id,
            'ERROR' AS status,
            ERROR_MESSAGE() AS message,
            NULL AS total_cryptocurrencies,
            NULL AS credits_used;
    END CATCH
END;
GO

-- =====================================================
-- INSERT CRYPTOCURRENCY DATA (MATCHES DATAFRAME COLUMNS)
-- =====================================================

CREATE OR ALTER PROCEDURE bronze.sp_insert_cryptocurrency_data
    @batch_id UNIQUEIDENTIFIER,  -- Links to api_response_status table
    -- Core cryptocurrency data
    @id INT,
    @name NVARCHAR(100),
    @symbol NVARCHAR(20),
    @slug NVARCHAR(100) = NULL,
    @num_market_pairs INT = NULL,
    @date_added DATETIME2 = NULL,
    @max_supply DECIMAL(30,8) = NULL,
    @circulating_supply DECIMAL(30,8) = NULL,
    @total_supply DECIMAL(30,8) = NULL,
    @infinite_supply BIT = NULL,
    -- Platform data
    @platform NVARCHAR(MAX) = NULL,
    @platform_id INT = NULL,
    @platform_name NVARCHAR(100) = NULL,
    @platform_symbol NVARCHAR(20) = NULL,
    @platform_slug NVARCHAR(100) = NULL,
    @platform_token_address NVARCHAR(255) = NULL,
    -- Ranking & metrics
    @cmc_rank INT = NULL,
    @self_reported_circulating_supply DECIMAL(30,8) = NULL,
    @self_reported_market_cap DECIMAL(25,2) = NULL,
    @tvl_ratio DECIMAL(10,6) = NULL,
    @last_updated DATETIME2 = NULL,
    -- Quote USD data (matches DataFrame column names exactly)
    @quote_USD_price DECIMAL(18,8),
    @quote_USD_volume_24h DECIMAL(25,2) = NULL,
    @quote_USD_volume_change_24h DECIMAL(10,4) = NULL,
    @quote_USD_percent_change_1h DECIMAL(10,4) = NULL,
    @quote_USD_percent_change_24h DECIMAL(10,4) = NULL,
    @quote_USD_percent_change_7d DECIMAL(10,4) = NULL,
    @quote_USD_percent_change_30d DECIMAL(10,4) = NULL,
    @quote_USD_percent_change_60d DECIMAL(10,4) = NULL,
    @quote_USD_percent_change_90d DECIMAL(10,4) = NULL,
    @quote_USD_market_cap DECIMAL(25,2) = NULL,
    @quote_USD_market_cap_dominance DECIMAL(8,4) = NULL,
    @quote_USD_fully_diluted_market_cap DECIMAL(25,2) = NULL,
    @quote_USD_tvl DECIMAL(25,2) = NULL,
    @quote_USD_last_updated DATETIME2 = NULL,
    -- Complex data
    @tags NVARCHAR(MAX) = NULL,
    @data_quality_flag NVARCHAR(20) = 'VALID'
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        INSERT INTO bronze.cryptocurrency_data (
            batch_id,
            id, name, symbol, slug, num_market_pairs, date_added,
            max_supply, circulating_supply, total_supply, infinite_supply,
            platform, platform_id, platform_name, platform_symbol, platform_slug, platform_token_address,
            cmc_rank, self_reported_circulating_supply, self_reported_market_cap, tvl_ratio, last_updated,
            quote_USD_price, quote_USD_volume_24h, quote_USD_volume_change_24h,
            quote_USD_percent_change_1h, quote_USD_percent_change_24h, quote_USD_percent_change_7d,
            quote_USD_percent_change_30d, quote_USD_percent_change_60d, quote_USD_percent_change_90d,
            quote_USD_market_cap, quote_USD_market_cap_dominance, quote_USD_fully_diluted_market_cap,
            quote_USD_tvl, quote_USD_last_updated,
            tags, collection_timestamp, data_quality_flag
        )
        VALUES (
            @batch_id,
            @id, @name, @symbol, @slug, @num_market_pairs, @date_added,
            @max_supply, @circulating_supply, @total_supply, @infinite_supply,
            @platform, @platform_id, @platform_name, @platform_symbol, @platform_slug, @platform_token_address,
            @cmc_rank, @self_reported_circulating_supply, @self_reported_market_cap, @tvl_ratio, @last_updated,
            @quote_USD_price, @quote_USD_volume_24h, @quote_USD_volume_change_24h,
            @quote_USD_percent_change_1h, @quote_USD_percent_change_24h, @quote_USD_percent_change_7d,
            @quote_USD_percent_change_30d, @quote_USD_percent_change_60d, @quote_USD_percent_change_90d,
            @quote_USD_market_cap, @quote_USD_market_cap_dominance, @quote_USD_fully_diluted_market_cap,
            @quote_USD_tvl, @quote_USD_last_updated,
            @tags, GETDATE(), @data_quality_flag
        );
        
        -- Return success information
        SELECT 
            SCOPE_IDENTITY() AS crypto_data_id,
            @batch_id AS batch_id,
            'SUCCESS' AS status,
            'Cryptocurrency data inserted successfully into Bronze layer' AS message,
            @symbol AS symbol,
            @quote_USD_price AS price_inserted;
        
    END TRY
    BEGIN CATCH
        -- Return error information
        SELECT 
            NULL AS crypto_data_id,
            @batch_id AS batch_id,
            'ERROR' AS status,
            ERROR_MESSAGE() AS message,
            @symbol AS symbol,
            NULL AS price_inserted;
    END CATCH
END;
GO

-- =====================================================
-- UTILITY PROCEDURES FOR NEW SCHEMA
-- =====================================================

-- =====================================================
-- DATA MONITORING & UTILITIES (UPDATED FOR NEW SCHEMA)
-- =====================================================

CREATE OR ALTER PROCEDURE bronze.sp_get_latest_data
    @symbol NVARCHAR(20) = NULL,
    @limit INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @symbol IS NULL
    BEGIN
        -- Get latest data for all symbols
        SELECT TOP (@limit)
            c.crypto_data_id,
            c.id,
            c.name,
            c.symbol,
            c.quote_USD_price,
            c.quote_USD_market_cap,
            c.quote_USD_percent_change_24h,
            c.cmc_rank,
            c.collection_timestamp,
            c.batch_id,
            s.credit_count,
            s.total_count
        FROM bronze.cryptocurrency_data c
        LEFT JOIN bronze.api_response_status s ON c.batch_id = s.batch_id
        ORDER BY c.collection_timestamp DESC;
    END
    ELSE
    BEGIN
        -- Get latest data for specific symbol
        SELECT TOP (@limit)
            c.crypto_data_id,
            c.id,
            c.name,
            c.symbol,
            c.quote_USD_price,
            c.quote_USD_market_cap,
            c.quote_USD_percent_change_24h,
            c.cmc_rank,
            c.collection_timestamp,
            c.batch_id,
            s.credit_count,
            s.total_count
        FROM bronze.cryptocurrency_data c
        LEFT JOIN bronze.api_response_status s ON c.batch_id = s.batch_id
        WHERE c.symbol = @symbol
        ORDER BY c.collection_timestamp DESC;
    END
END;
GO

CREATE OR ALTER PROCEDURE bronze.sp_data_quality_check
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        'Bronze Layer Data Quality Report' AS report_type,
        COUNT(*) AS total_records,
        COUNT(DISTINCT symbol) AS unique_symbols,
        COUNT(CASE WHEN quote_USD_price IS NULL THEN 1 END) AS missing_price_count,
        COUNT(CASE WHEN quote_USD_market_cap IS NULL THEN 1 END) AS missing_market_cap_count,
        COUNT(CASE WHEN quote_USD_volume_24h IS NULL THEN 1 END) AS missing_volume_count,
        COUNT(CASE WHEN cmc_rank IS NULL THEN 1 END) AS missing_rank_count,
        MIN(collection_timestamp) AS oldest_record,
        MAX(collection_timestamp) AS newest_record,
        DATEDIFF(HOUR, MIN(collection_timestamp), MAX(collection_timestamp)) AS data_span_hours,
        COUNT(*)/(COUNT(DISTINCT symbol) + 0.001) AS avg_records_per_symbol
    FROM bronze.cryptocurrency_data;
    
    -- Also show top symbols by record count
    SELECT 
        'Top Symbols by Record Count' AS report_section,
        symbol,
        COUNT(*) AS record_count,
        MIN(collection_timestamp) AS first_record,
        MAX(collection_timestamp) AS latest_record,
        AVG(quote_USD_price) AS avg_price_usd
    FROM bronze.cryptocurrency_data
    GROUP BY symbol
    ORDER BY COUNT(*) DESC;
END;
GO

