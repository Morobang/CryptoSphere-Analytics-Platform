-- =====================================================
-- GOLD LAYER - SCHEMA AND DATA MARTS CREATION
-- =====================================================
-- Purpose: Create Gold layer schema and all related data marts
-- Layer: Gold (Analytics & Business Intelligence)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Usage: Business-ready analytics, ML features, and reporting
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- GOLD SCHEMA CREATION
-- =====================================================

-- Gold Layer Schema (Analytics Data)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold')
BEGIN
    EXEC('CREATE SCHEMA gold');
    PRINT '✅ Schema [gold] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Schema [gold] already exists';
END
GO

-- =====================================================
-- GOLD LAYER DATA MARTS
-- =====================================================

-- Gold Layer: Market Overview Daily
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'market_overview_daily' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.market_overview_daily (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        report_date DATE NOT NULL,
        total_cryptocurrencies INT,
        total_market_cap_usd DECIMAL(30,2),
        total_volume_24h_usd DECIMAL(30,2),
        bitcoin_dominance_pct DECIMAL(5,2),
        ethereum_dominance_pct DECIMAL(5,2),
        top_gainer_symbol NVARCHAR(20),
        top_gainer_change_pct DECIMAL(10,4),
        top_loser_symbol NVARCHAR(20),
        top_loser_change_pct DECIMAL(10,4),
        avg_market_cap DECIMAL(25,2),
        median_price_usd DECIMAL(18,8),
        high_quality_coins_count INT, -- Quality score > 0.8
        market_fear_greed_index DECIMAL(3,1), -- 0.0 to 100.0
        volatility_index DECIMAL(8,4),
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (report_date)
    );
    
    CREATE INDEX IX_gold_market_overview_date ON gold.market_overview_daily(report_date);
    
    PRINT '✅ Table [gold.market_overview_daily] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.market_overview_daily] already exists';
END
GO

-- Gold Layer: Crypto Performance Metrics (Technical Analysis)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'crypto_performance_metrics' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.crypto_performance_metrics (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        symbol NVARCHAR(20) NOT NULL,
        analysis_date DATE NOT NULL,
        
        -- Moving Averages
        sma_7d DECIMAL(18,8),
        sma_30d DECIMAL(18,8),
        sma_90d DECIMAL(18,8),
        ema_12d DECIMAL(18,8),
        ema_26d DECIMAL(18,8),
        
        -- Technical Indicators
        rsi_14d DECIMAL(5,2), -- Relative Strength Index
        macd_line DECIMAL(18,8), -- MACD Line
        macd_signal DECIMAL(18,8), -- MACD Signal Line
        macd_histogram DECIMAL(18,8), -- MACD Histogram
        
        -- Bollinger Bands
        bb_upper DECIMAL(18,8),
        bb_middle DECIMAL(18,8),
        bb_lower DECIMAL(18,8),
        bb_width DECIMAL(10,6),
        bb_position DECIMAL(5,4), -- Price position within bands (0-1)
        
        -- Volatility Metrics
        volatility_7d DECIMAL(10,6),
        volatility_30d DECIMAL(10,6),
        price_range_24h DECIMAL(10,4), -- (High-Low)/Close
        
        -- Performance Metrics
        return_7d DECIMAL(10,4),
        return_30d DECIMAL(10,4),
        return_90d DECIMAL(10,4),
        max_drawdown_30d DECIMAL(10,4),
        sharpe_ratio_30d DECIMAL(8,4),
        
        -- Volume Analysis
        volume_sma_7d DECIMAL(25,2),
        volume_ratio_24h DECIMAL(6,3), -- Current volume / Average volume
        volume_trend NVARCHAR(20), -- INCREASING, DECREASING, STABLE
        
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (symbol, analysis_date)
    );
    
    CREATE INDEX IX_gold_performance_symbol_date ON gold.crypto_performance_metrics(symbol, analysis_date);
    CREATE INDEX IX_gold_performance_date ON gold.crypto_performance_metrics(analysis_date);
    
    PRINT '✅ Table [gold.crypto_performance_metrics] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.crypto_performance_metrics] already exists';
END
GO

-- Gold Layer: Trading Signals
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'trading_signals' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.trading_signals (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        symbol NVARCHAR(20) NOT NULL,
        signal_date DATETIME2 NOT NULL,
        signal_type NVARCHAR(20), -- BUY, SELL, HOLD
        confidence_score DECIMAL(3,2), -- 0.00 to 1.00
        signal_strength NVARCHAR(20), -- WEAK, MODERATE, STRONG
        
        -- Signal Components
        price_trend_signal NVARCHAR(20), -- BULLISH, BEARISH, NEUTRAL
        volume_signal NVARCHAR(20),
        momentum_signal NVARCHAR(20),
        mean_reversion_signal NVARCHAR(20),
        
        -- Supporting Data
        current_price DECIMAL(18,8),
        target_price DECIMAL(18,8),
        stop_loss_price DECIMAL(18,8),
        risk_reward_ratio DECIMAL(5,2),
        
        -- Signal Metadata
        signal_algorithm NVARCHAR(100), -- Which algorithm generated this
        backtest_accuracy DECIMAL(5,2), -- Historical accuracy %
        market_condition NVARCHAR(50), -- BULL, BEAR, SIDEWAYS, VOLATILE
        time_horizon NVARCHAR(20), -- SHORT, MEDIUM, LONG
        
        created_timestamp DATETIME2 DEFAULT GETDATE()
    );
    
    CREATE INDEX IX_gold_signals_symbol_date ON gold.trading_signals(symbol, signal_date);
    CREATE INDEX IX_gold_signals_confidence ON gold.trading_signals(confidence_score);
    CREATE INDEX IX_gold_signals_type ON gold.trading_signals(signal_type);
    CREATE INDEX IX_gold_signals_date ON gold.trading_signals(signal_date);
    
    PRINT '✅ Table [gold.trading_signals] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.trading_signals] already exists';
END
GO

-- Gold Layer: ML Features for Machine Learning
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ml_features' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.ml_features (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        symbol NVARCHAR(20) NOT NULL,
        feature_date DATE NOT NULL,
        
        -- Price Features
        price_current DECIMAL(18,8),
        price_change_1h DECIMAL(10,4),
        price_change_24h DECIMAL(10,4),
        price_change_7d DECIMAL(10,4),
        price_volatility_7d DECIMAL(10,6),
        price_volatility_30d DECIMAL(10,6),
        
        -- Market Features
        market_cap_rank INT,
        market_cap_usd DECIMAL(25,2),
        volume_24h_usd DECIMAL(25,2),
        volume_rank INT,
        market_dominance DECIMAL(8,4),
        
        -- Technical Features
        rsi_14 DECIMAL(5,2),
        macd_signal DECIMAL(5,4),
        bb_position DECIMAL(5,4),
        sma_trend_7d DECIMAL(5,4), -- (Current - SMA) / SMA
        volume_ratio DECIMAL(6,3),
        
        -- Momentum Features
        momentum_1d DECIMAL(10,4),
        momentum_7d DECIMAL(10,4),
        momentum_30d DECIMAL(10,4),
        acceleration_7d DECIMAL(10,6),
        
        -- Volatility Features
        volatility_regime NVARCHAR(20), -- LOW, MEDIUM, HIGH
        volatility_percentile DECIMAL(5,2), -- Percentile rank of current volatility
        
        -- Volume Features
        volume_trend_7d NVARCHAR(20), -- INCREASING, DECREASING, STABLE
        volume_spike_indicator BIT, -- 1 if volume > 2x average
        
        -- Target Variables (for supervised learning)
        target_price_change_24h DECIMAL(10,4), -- Future 24h price change
        target_direction_24h INT, -- 1 for up, 0 for down
        target_volatility_24h DECIMAL(10,6), -- Future 24h volatility
        target_volume_change_24h DECIMAL(10,4), -- Future 24h volume change
        
        -- Data Quality
        feature_completeness DECIMAL(3,2), -- % of features populated
        data_quality_score DECIMAL(3,2),
        
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (symbol, feature_date)
    );
    
    CREATE INDEX IX_gold_ml_features_symbol_date ON gold.ml_features(symbol, feature_date);
    CREATE INDEX IX_gold_ml_features_quality ON gold.ml_features(data_quality_score);
    CREATE INDEX IX_gold_ml_features_date ON gold.ml_features(feature_date);
    
    PRINT '✅ Table [gold.ml_features] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.ml_features] already exists';
END
GO

-- Gold Layer: Risk Metrics
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'risk_metrics' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.risk_metrics (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        symbol NVARCHAR(20) NOT NULL,
        calculation_date DATE NOT NULL,
        
        -- Value at Risk (VaR)
        var_95_1d DECIMAL(10,4), -- 95% VaR for 1 day
        var_99_1d DECIMAL(10,4), -- 99% VaR for 1 day
        var_95_7d DECIMAL(10,4), -- 95% VaR for 7 days
        
        -- Risk Ratios
        sharpe_ratio_30d DECIMAL(8,4),
        sortino_ratio_30d DECIMAL(8,4),
        calmar_ratio_30d DECIMAL(8,4),
        
        -- Drawdown Metrics
        max_drawdown_30d DECIMAL(10,4),
        current_drawdown DECIMAL(10,4),
        drawdown_duration_days INT,
        
        -- Correlation Metrics
        correlation_to_btc DECIMAL(6,4),
        correlation_to_eth DECIMAL(6,4),
        correlation_to_market DECIMAL(6,4),
        
        -- Liquidity Metrics
        bid_ask_spread_pct DECIMAL(8,4),
        market_impact_score DECIMAL(3,2),
        liquidity_score DECIMAL(3,2),
        
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (symbol, calculation_date)
    );
    
    CREATE INDEX IX_gold_risk_metrics_symbol_date ON gold.risk_metrics(symbol, calculation_date);
    CREATE INDEX IX_gold_risk_metrics_date ON gold.risk_metrics(calculation_date);
    
    PRINT '✅ Table [gold.risk_metrics] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.risk_metrics] already exists';
END
GO

-- Gold Layer: Portfolio Analytics
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'portfolio_analytics' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.portfolio_analytics (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        portfolio_name NVARCHAR(100) DEFAULT 'DEFAULT',
        analysis_date DATE NOT NULL,
        
        -- Portfolio Composition
        total_value_usd DECIMAL(30,2),
        number_of_assets INT,
        largest_position_pct DECIMAL(5,2),
        smallest_position_pct DECIMAL(5,2),
        
        -- Performance Metrics
        portfolio_return_1d DECIMAL(10,4),
        portfolio_return_7d DECIMAL(10,4),
        portfolio_return_30d DECIMAL(10,4),
        portfolio_volatility_30d DECIMAL(10,4),
        
        -- Risk Metrics
        portfolio_var_95_1d DECIMAL(10,4),
        portfolio_beta DECIMAL(8,4), -- Beta to overall crypto market
        portfolio_alpha DECIMAL(8,4), -- Alpha vs market
        
        -- Diversification Metrics
        diversification_ratio DECIMAL(6,4),
        concentration_risk_score DECIMAL(3,2),
        sector_diversification_score DECIMAL(3,2),
        
        -- Rebalancing Recommendations
        needs_rebalancing BIT,
        rebalancing_score DECIMAL(3,2),
        suggested_actions NVARCHAR(MAX),
        
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (portfolio_name, analysis_date)
    );
    
    CREATE INDEX IX_gold_portfolio_name_date ON gold.portfolio_analytics(portfolio_name, analysis_date);
    CREATE INDEX IX_gold_portfolio_date ON gold.portfolio_analytics(analysis_date);
    
    PRINT '✅ Table [gold.portfolio_analytics] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.portfolio_analytics] already exists';
END
GO

-- Gold Layer: Market Regime Analysis
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'market_regime_analysis' AND schema_id = SCHEMA_ID('gold'))
BEGIN
    CREATE TABLE gold.market_regime_analysis (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        analysis_date DATE NOT NULL,
        
        -- Current Market Regime
        current_regime NVARCHAR(20), -- BULL, BEAR, SIDEWAYS, TRANSITION
        regime_strength DECIMAL(3,2), -- 0.00 to 1.00
        regime_duration_days INT,
        
        -- Market Sentiment Indicators
        fear_greed_index DECIMAL(3,1), -- 0.0 to 100.0
        volatility_regime NVARCHAR(20), -- LOW, NORMAL, HIGH, EXTREME
        correlation_regime NVARCHAR(20), -- LOW, NORMAL, HIGH
        
        -- Trend Analysis
        overall_trend NVARCHAR(20), -- STRONG_UP, UP, NEUTRAL, DOWN, STRONG_DOWN
        trend_strength DECIMAL(3,2),
        trend_consistency DECIMAL(3,2),
        
        -- Support/Resistance Levels
        market_support_level DECIMAL(30,2),
        market_resistance_level DECIMAL(30,2),
        current_position_pct DECIMAL(5,2), -- Position between support/resistance
        
        -- Predictions
        regime_change_probability DECIMAL(3,2),
        predicted_next_regime NVARCHAR(20),
        confidence_level DECIMAL(3,2),
        
        created_timestamp DATETIME2 DEFAULT GETDATE(),
        UNIQUE (analysis_date)
    );
    
    CREATE INDEX IX_gold_regime_analysis_date ON gold.market_regime_analysis(analysis_date);
    CREATE INDEX IX_gold_regime_current ON gold.market_regime_analysis(current_regime);
    
    PRINT '✅ Table [gold.market_regime_analysis] created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️  Table [gold.market_regime_analysis] already exists';
END
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '';
PRINT '🥇 =====================================================';
PRINT '   GOLD LAYER SCHEMA & DATA MARTS SETUP COMPLETE';
PRINT '=====================================================';
PRINT '';
PRINT '✅ Schema: gold';
PRINT '✅ Data Marts Created:';
PRINT '   • gold.market_overview_daily - Daily market summaries';
PRINT '   • gold.crypto_performance_metrics - Technical indicators';
PRINT '   • gold.trading_signals - ML-generated trading signals';
PRINT '   • gold.ml_features - Machine learning features';
PRINT '   • gold.risk_metrics - Risk analysis and VaR calculations';
PRINT '   • gold.portfolio_analytics - Portfolio performance analysis';
PRINT '   • gold.market_regime_analysis - Market regime detection';
PRINT '';
PRINT '📊 Indexes Created: 21 performance indexes';
PRINT '🎯 Purpose: Business-ready analytics, ML, and reporting';
PRINT '📈 Ready for: Silver → Gold ETL processing';
PRINT '';
PRINT '💡 Next Step: Create Gold layer ETL procedures';
PRINT '=====================================================';
GO