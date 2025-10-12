USE cryptosphere_analytics;
GO

-- =====================================================
-- BRONZE LAYER SCHEMA FOR COINMARKETCAP API
-- =====================================================
-- 
-- PURPOSE: Create Bronze Layer schema matching CoinMarketCap API structure
-- DESIGNED FOR: CoinMarketCap /v1/cryptocurrency/listings/latest endpoint
-- 
-- STRUCTURE:
-- Table 1: api_response_status (stores "status" object from API)
-- Table 2: cryptocurrency_data (stores "data" array objects from API)  
-- 

-- =====================================================
-- TABLE 1: API RESPONSE STATUS
-- =====================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'api_response_status' AND schema_id = SCHEMA_ID('bronze'))
BEGIN
    CREATE TABLE bronze.api_response_status (
        -- Primary Key
        status_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        
        -- Batch Identification (UUID for linking status to data records)
        batch_id UNIQUEIDENTIFIER DEFAULT NEWID(),
        
        -- API Status Data (from "status" object in JSON response)
        timestamp DATETIME2,               -- status.timestamp
        error_code INT,                    -- status.error_code
        error_message NVARCHAR(500),       -- status.error_message
        elapsed INT,                       -- status.elapsed (response time in ms)
        credit_count INT,                  -- status.credit_count (API credits used)
        notice NVARCHAR(500),              -- status.notice
        total_count INT,                   -- status.total_count (total cryptos available)
        
        -- Collection Metadata (our tracking fields)
        collection_timestamp DATETIME2 DEFAULT GETDATE(),
        api_endpoint NVARCHAR(500),        -- Which API endpoint was called
        request_parameters NVARCHAR(1000), -- Parameters sent to API
        
        -- Data Quality Flags
        response_size_bytes INT,           -- Size of JSON response
        records_processed INT              -- How many data records were processed
    );

    PRINT 'Table [bronze.api_response_status] created successfully';
END
ELSE
BEGIN
    PRINT 'Table [bronze.api_response_status] already exists';
END
GO

-- =====================================================
-- TABLE 2: CRYPTOCURRENCY DATA
-- =====================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'cryptocurrency_data' AND schema_id = SCHEMA_ID('bronze'))
BEGIN
    CREATE TABLE bronze.cryptocurrency_data (
        -- Primary Key
        data_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        
        -- Batch Identification (links to api_response_status table)
        batch_id UNIQUEIDENTIFIER NOT NULL,
        
        -- Core Cryptocurrency Data (from each object in "data" array)
        id INT NOT NULL,                   -- Crypto ID from CoinMarketCap
        name NVARCHAR(100),                -- Full name (e.g., "Bitcoin")
        symbol NVARCHAR(20),               -- Trading symbol (e.g., "BTC")
        slug NVARCHAR(100),                -- URL slug (e.g., "bitcoin")
        num_market_pairs INT,              -- Number of trading pairs
        date_added DATETIME2,              -- When crypto was added to CMC
        max_supply DECIMAL(30,8),          -- Maximum possible supply
        circulating_supply DECIMAL(30,8),  -- Current circulating supply
        total_supply DECIMAL(30,8),        -- Total supply issued
        infinite_supply BIT,               -- Whether supply is infinite
        
        -- Platform Information (for ERC-20 tokens, etc.) - Column names match DataFrame
        platform NVARCHAR(MAX),            -- Store complete platform object as JSON
        platform_id INT,                   -- Platform ID (e.g., 1027 for Ethereum)
        platform_name NVARCHAR(100),       -- Platform name (e.g., "Ethereum")
        platform_symbol NVARCHAR(20),      -- Platform symbol (e.g., "ETH")
        platform_slug NVARCHAR(100),       -- Platform slug (e.g., "ethereum")
        platform_token_address NVARCHAR(255), -- Token contract address
        
        -- Ranking & Self-Reported Metrics
        cmc_rank INT,                      -- CoinMarketCap ranking
        self_reported_circulating_supply DECIMAL(30,8),
        self_reported_market_cap DECIMAL(25,2),
        tvl_ratio DECIMAL(10,6),           -- Total Value Locked ratio
        last_updated DATETIME2,            -- When crypto data was last updated
        
        -- Quote Data - USD (from "quote.USD" object) - Column names match DataFrame
        quote_USD_price DECIMAL(18,8),               -- Current price in USD
        quote_USD_volume_24h DECIMAL(25,2),          -- 24-hour trading volume
        quote_USD_volume_change_24h DECIMAL(10,4),   -- 24-hour volume change %
        quote_USD_percent_change_1h DECIMAL(10,4),   -- 1-hour price change %
        quote_USD_percent_change_24h DECIMAL(10,4),  -- 24-hour price change %
        quote_USD_percent_change_7d DECIMAL(10,4),   -- 7-day price change %
        quote_USD_percent_change_30d DECIMAL(10,4),  -- 30-day price change %
        quote_USD_percent_change_60d DECIMAL(10,4),  -- 60-day price change %
        quote_USD_percent_change_90d DECIMAL(10,4),  -- 90-day price change %
        quote_USD_market_cap DECIMAL(25,2),          -- Market capitalization
        quote_USD_market_cap_dominance DECIMAL(8,4), -- Market cap dominance %
        quote_USD_fully_diluted_market_cap DECIMAL(25,2), -- Fully diluted market cap
        quote_USD_tvl DECIMAL(25,2),                 -- Total Value Locked
        quote_USD_last_updated DATETIME2,            -- When quote data was last updated
        
        -- Complex Data as JSON (for arrays and nested objects)
        tags NVARCHAR(MAX),                -- Store tags array as JSON string (matches DataFrame)
        
        -- Collection Metadata (our tracking fields)
        collection_timestamp DATETIME2 DEFAULT GETDATE(),
        
        -- Data Quality Flags
        data_quality_flag NVARCHAR(20) DEFAULT 'VALID' -- VALID, WARNING, ERROR
    );

    
    -- Create foreign key relationship
    ALTER TABLE bronze.cryptocurrency_data 
    ADD CONSTRAINT FK_bronze_crypto_batch 
    FOREIGN KEY (batch_id) REFERENCES bronze.api_response_status(batch_id);

    PRINT 'Table [bronze.cryptocurrency_data] created successfully';
    PRINT 'Indexes and foreign keys created for optimal performance';
END
ELSE
BEGIN
    PRINT 'Table [bronze.cryptocurrency_data] already exists';
END
GO




