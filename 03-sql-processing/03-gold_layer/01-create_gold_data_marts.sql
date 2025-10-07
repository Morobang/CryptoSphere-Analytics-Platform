-- ================================================================================================
-- CryptoSphere Analytics Platform - Gold Layer Data Marts
-- ================================================================================================
-- Purpose: Business-ready data marts for analytics, reporting, and machine learning
-- Layer: Gold (Business Data)
-- Author: CryptoSphere Analytics Team
-- Created: 2025-10-07
-- ================================================================================================

-- Create gold schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS gold;
SET search_path TO gold, silver, bronze, metadata, public;

-- ================================================================================================
-- 1. MARKET OVERVIEW DATA MART
-- ================================================================================================

CREATE TABLE market_overview_daily (
    id SERIAL PRIMARY KEY,
    
    -- Date dimension
    date_key DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    
    -- Market aggregations
    total_market_cap_usd NUMERIC(25,8),
    total_volume_24h_usd NUMERIC(25,8),
    
    -- Market statistics
    active_cryptocurrencies_count INTEGER,
    cryptocurrencies_with_volume_count INTEGER,
    
    -- Top performers
    best_performer_symbol crypto_symbol,
    best_performer_change_pct NUMERIC(10,4),
    worst_performer_symbol crypto_symbol,
    worst_performer_change_pct NUMERIC(10,4),
    
    -- Market concentration
    top_10_market_cap_dominance NUMERIC(8,4),
    bitcoin_dominance NUMERIC(8,4),
    ethereum_dominance NUMERIC(8,4),
    altcoin_dominance NUMERIC(8,4),
    
    -- Volatility measures
    market_volatility_index NUMERIC(10,6),
    avg_price_change_24h NUMERIC(10,4),
    median_price_change_24h NUMERIC(10,4),
    
    -- Fear & Greed indicators (calculated)
    market_momentum_score NUMERIC(5,2), -- -100 to +100
    volume_strength_score NUMERIC(5,2),
    
    -- Data quality
    data_completeness_pct NUMERIC(5,2),
    quality_score NUMERIC(3,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT uq_gold_market_overview_date UNIQUE (date_key)
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('market_overview_daily', 'date_key', chunk_time_interval => INTERVAL '1 month');

-- Create indexes
CREATE INDEX idx_market_overview_year_month ON market_overview_daily(year, month);
CREATE INDEX idx_market_overview_quarter ON market_overview_daily(quarter, year);
CREATE INDEX idx_market_overview_market_cap ON market_overview_daily(total_market_cap_usd);

-- ================================================================================================
-- 2. CRYPTOCURRENCY PERFORMANCE DATA MART
-- ================================================================================================

CREATE TABLE crypto_performance_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Cryptocurrency identification
    cmc_id INTEGER NOT NULL,
    symbol crypto_symbol NOT NULL,
    name VARCHAR(100) NOT NULL,
    
    -- Date dimension
    date_key DATE NOT NULL,
    
    -- Price metrics
    open_price_usd NUMERIC(20,8) NOT NULL,
    high_price_usd NUMERIC(20,8) NOT NULL,
    low_price_usd NUMERIC(20,8) NOT NULL,
    close_price_usd NUMERIC(20,8) NOT NULL,
    volume_usd NUMERIC(25,8),
    
    -- Performance calculations
    daily_return_pct NUMERIC(10,4),
    volatility_daily NUMERIC(10,6),
    
    -- Moving averages
    sma_7_days NUMERIC(20,8),
    sma_30_days NUMERIC(20,8),
    sma_90_days NUMERIC(20,8),
    
    -- Exponential moving averages
    ema_12_days NUMERIC(20,8),
    ema_26_days NUMERIC(20,8),
    
    -- Technical indicators
    rsi_14_days NUMERIC(5,2), -- Relative Strength Index (0-100)
    macd_line NUMERIC(15,8), -- MACD Line
    macd_signal NUMERIC(15,8), -- MACD Signal Line
    macd_histogram NUMERIC(15,8), -- MACD Histogram
    
    -- Bollinger Bands
    bb_upper NUMERIC(20,8),
    bb_middle NUMERIC(20,8),
    bb_lower NUMERIC(20,8),
    bb_width NUMERIC(15,8),
    bb_position NUMERIC(5,4), -- Position within bands (0-1)
    
    -- Volume indicators
    volume_sma_20 NUMERIC(25,8),
    volume_ratio NUMERIC(8,4), -- Current volume / Average volume
    
    -- Market metrics
    market_cap_usd NUMERIC(25,8),
    market_cap_rank INTEGER,
    market_cap_dominance NUMERIC(8,4),
    
    -- Risk metrics
    drawdown_from_ath NUMERIC(10,4), -- % down from all-time high
    days_since_ath INTEGER,
    sharpe_ratio_30d NUMERIC(8,4),
    sortino_ratio_30d NUMERIC(8,4),
    
    -- Correlation with major assets
    correlation_btc_30d NUMERIC(6,4),
    correlation_eth_30d NUMERIC(6,4),
    correlation_spy_30d NUMERIC(6,4), -- S&P 500 correlation
    
    -- Data quality
    data_completeness_pct NUMERIC(5,2),
    quality_score NUMERIC(3,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT uq_gold_crypto_performance_symbol_date UNIQUE (symbol, date_key)
);

-- Create hypertable
SELECT create_hypertable('crypto_performance_metrics', 'date_key', chunk_time_interval => INTERVAL '1 month');

-- Create indexes
CREATE INDEX idx_crypto_performance_symbol_date ON crypto_performance_metrics(symbol, date_key DESC);
CREATE INDEX idx_crypto_performance_cmc_id_date ON crypto_performance_metrics(cmc_id, date_key DESC);
CREATE INDEX idx_crypto_performance_rank ON crypto_performance_metrics(market_cap_rank, date_key DESC) WHERE market_cap_rank IS NOT NULL;
CREATE INDEX idx_crypto_performance_volume ON crypto_performance_metrics(volume_usd DESC, date_key DESC) WHERE volume_usd IS NOT NULL;

-- ================================================================================================
-- 3. TRADING SIGNALS DATA MART
-- ================================================================================================

CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    
    -- Cryptocurrency identification
    cmc_id INTEGER NOT NULL,
    symbol crypto_symbol NOT NULL,
    
    -- Signal information
    signal_timestamp TIMESTAMP NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL'
    signal_strength NUMERIC(3,2) NOT NULL, -- 0.00 to 1.00
    confidence_level NUMERIC(3,2) NOT NULL, -- 0.00 to 1.00
    
    -- Signal sources and weights
    technical_analysis_score NUMERIC(5,2), -- -100 to +100
    momentum_score NUMERIC(5,2),
    volume_analysis_score NUMERIC(5,2),
    trend_analysis_score NUMERIC(5,2),
    
    -- Price context
    price_at_signal NUMERIC(20,8) NOT NULL,
    
    -- Signal details
    signal_reason TEXT,
    supporting_indicators TEXT[],
    conflicting_indicators TEXT[],
    
    -- Risk assessment
    risk_level VARCHAR(10), -- 'LOW', 'MEDIUM', 'HIGH'
    stop_loss_suggestion NUMERIC(20,8),
    take_profit_suggestion NUMERIC(20,8),
    position_size_suggestion NUMERIC(5,2), -- 0-100% of portfolio
    
    -- Signal validity
    signal_duration_hours INTEGER, -- Expected signal validity
    invalidation_price NUMERIC(20,8),
    
    -- Performance tracking (updated post-signal)
    actual_return_1h NUMERIC(10,4),
    actual_return_24h NUMERIC(10,4),
    actual_return_7d NUMERIC(10,4),
    signal_accuracy_score NUMERIC(3,2),
    
    -- Metadata
    signal_version VARCHAR(10) DEFAULT '1.0',
    model_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT chk_trading_signals_strength CHECK (signal_strength >= 0 AND signal_strength <= 1),
    CONSTRAINT chk_trading_signals_confidence CHECK (confidence_level >= 0 AND confidence_level <= 1),
    CONSTRAINT chk_trading_signals_type CHECK (signal_type IN ('BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL'))
);

-- Create hypertable
SELECT create_hypertable('trading_signals', 'signal_timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes
CREATE INDEX idx_trading_signals_symbol_time ON trading_signals(symbol, signal_timestamp DESC);
CREATE INDEX idx_trading_signals_type_strength ON trading_signals(signal_type, signal_strength DESC, signal_timestamp DESC);
CREATE INDEX idx_trading_signals_confidence ON trading_signals(confidence_level DESC, signal_timestamp DESC);

-- ================================================================================================
-- 4. PORTFOLIO ANALYSIS DATA MART
-- ================================================================================================

CREATE TABLE portfolio_analysis_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Portfolio identification (for multi-portfolio support)
    portfolio_id VARCHAR(50) DEFAULT 'default',
    
    -- Date dimension
    date_key DATE NOT NULL,
    
    -- Portfolio composition
    total_value_usd NUMERIC(25,8) NOT NULL,
    total_cost_basis_usd NUMERIC(25,8),
    unrealized_pnl_usd NUMERIC(25,8),
    unrealized_pnl_pct NUMERIC(10,4),
    
    -- Asset allocation
    crypto_allocation_pct NUMERIC(5,2),
    stable_coin_allocation_pct NUMERIC(5,2),
    cash_allocation_pct NUMERIC(5,2),
    
    -- Top holdings
    top_holding_symbol crypto_symbol,
    top_holding_pct NUMERIC(5,2),
    concentration_risk_score NUMERIC(3,2), -- 0-1 (1 = very concentrated)
    
    -- Performance metrics
    daily_return_pct NUMERIC(10,4),
    total_return_pct NUMERIC(10,4),
    annualized_return_pct NUMERIC(10,4),
    
    -- Risk metrics
    portfolio_volatility NUMERIC(10,6),
    max_drawdown_pct NUMERIC(10,4),
    value_at_risk_95 NUMERIC(25,8), -- 95% VaR
    sharpe_ratio NUMERIC(8,4),
    sortino_ratio NUMERIC(8,4),
    
    -- Correlation analysis
    correlation_with_btc NUMERIC(6,4),
    correlation_with_market NUMERIC(6,4),
    beta_to_market NUMERIC(8,4),
    
    -- Diversification metrics
    number_of_holdings INTEGER,
    effective_holdings NUMERIC(8,2), -- 1/sum(weight^2)
    herfindahl_index NUMERIC(6,4), -- Concentration measure
    
    -- Trading activity
    turnover_rate_pct NUMERIC(8,4),
    transaction_costs_usd NUMERIC(15,8),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT uq_gold_portfolio_date UNIQUE (portfolio_id, date_key)
);

-- Create hypertable
SELECT create_hypertable('portfolio_analysis_metrics', 'date_key', chunk_time_interval => INTERVAL '1 month');

-- Create indexes
CREATE INDEX idx_portfolio_analysis_portfolio_date ON portfolio_analysis_metrics(portfolio_id, date_key DESC);
CREATE INDEX idx_portfolio_analysis_performance ON portfolio_analysis_metrics(total_return_pct DESC, date_key DESC);

-- ================================================================================================
-- 5. MARKET CORRELATION MATRIX DATA MART
-- ================================================================================================

CREATE TABLE correlation_matrix (
    id SERIAL PRIMARY KEY,
    
    -- Date dimension
    date_key DATE NOT NULL,
    analysis_period_days INTEGER NOT NULL, -- 7, 30, 90 days
    
    -- Asset pair
    symbol_a crypto_symbol NOT NULL,
    symbol_b crypto_symbol NOT NULL,
    
    -- Correlation metrics
    correlation_coefficient NUMERIC(6,4) NOT NULL, -- -1.0 to 1.0
    correlation_strength VARCHAR(20), -- 'VERY_WEAK', 'WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG'
    correlation_direction VARCHAR(10), -- 'POSITIVE', 'NEGATIVE'
    
    -- Statistical significance
    p_value NUMERIC(10,8),
    is_significant BOOLEAN,
    
    -- Supporting statistics
    covariance NUMERIC(15,8),
    observations_count INTEGER,
    avg_return_a NUMERIC(10,4),
    avg_return_b NUMERIC(10,4),
    volatility_a NUMERIC(10,6),
    volatility_b NUMERIC(10,6),
    
    -- Rolling correlation trend
    correlation_trend VARCHAR(20), -- 'INCREASING', 'DECREASING', 'STABLE'
    correlation_stability_score NUMERIC(3,2), -- 0-1 (1 = very stable)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT chk_correlation_coefficient CHECK (correlation_coefficient >= -1.0 AND correlation_coefficient <= 1.0),
    CONSTRAINT chk_correlation_p_value CHECK (p_value >= 0 AND p_value <= 1),
    CONSTRAINT uq_correlation_symbols_date_period UNIQUE (symbol_a, symbol_b, date_key, analysis_period_days)
);

-- Create indexes
CREATE INDEX idx_correlation_date_period ON correlation_matrix(date_key DESC, analysis_period_days);
CREATE INDEX idx_correlation_symbols ON correlation_matrix(symbol_a, symbol_b, date_key DESC);
CREATE INDEX idx_correlation_strength ON correlation_matrix(correlation_strength, ABS(correlation_coefficient) DESC);

-- ================================================================================================
-- 6. MACHINE LEARNING FEATURES DATA MART
-- ================================================================================================

CREATE TABLE ml_features_dataset (
    id BIGSERIAL PRIMARY KEY,
    
    -- Cryptocurrency identification
    cmc_id INTEGER NOT NULL,
    symbol crypto_symbol NOT NULL,
    
    -- Feature timestamp
    feature_timestamp TIMESTAMP NOT NULL,
    
    -- Price features
    price_usd NUMERIC(20,8) NOT NULL,
    price_sma_7 NUMERIC(20,8),
    price_sma_30 NUMERIC(20,8),
    price_ema_12 NUMERIC(20,8),
    price_ema_26 NUMERIC(20,8),
    price_rsi_14 NUMERIC(5,2),
    
    -- Volume features
    volume_usd NUMERIC(25,8),
    volume_sma_20 NUMERIC(25,8),
    volume_ratio NUMERIC(8,4),
    
    -- Volatility features
    volatility_1d NUMERIC(10,6),
    volatility_7d NUMERIC(10,6),
    volatility_30d NUMERIC(10,6),
    
    -- Momentum features
    momentum_1d NUMERIC(10,4),
    momentum_7d NUMERIC(10,4),
    momentum_30d NUMERIC(10,4),
    
    -- Market structure features
    market_cap_usd NUMERIC(25,8),
    market_cap_rank INTEGER,
    market_dominance NUMERIC(8,4),
    
    -- Correlation features
    correlation_btc_30d NUMERIC(6,4),
    correlation_eth_30d NUMERIC(6,4),
    correlation_market_30d NUMERIC(6,4),
    
    -- Technical indicator features
    bb_position NUMERIC(5,4),
    macd_signal NUMERIC(15,8),
    support_level NUMERIC(20,8),
    resistance_level NUMERIC(20,8),
    
    -- Market sentiment features (external data when available)
    social_sentiment_score NUMERIC(5,2),
    news_sentiment_score NUMERIC(5,2),
    fear_greed_index NUMERIC(3,0),
    
    -- Target variables (for supervised learning)
    price_change_1h NUMERIC(10,4),
    price_change_24h NUMERIC(10,4),
    price_change_7d NUMERIC(10,4),
    
    -- Classification targets
    direction_1h VARCHAR(10), -- 'UP', 'DOWN', 'STABLE'
    direction_24h VARCHAR(10),
    direction_7d VARCHAR(10),
    volatility_class VARCHAR(10), -- 'LOW', 'MEDIUM', 'HIGH'
    
    -- Feature quality
    feature_completeness_pct NUMERIC(5,2),
    quality_score NUMERIC(3,2),
    
    -- Metadata
    feature_set_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID
);

-- Create hypertable
SELECT create_hypertable('ml_features_dataset', 'feature_timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for ML model training
CREATE INDEX idx_ml_features_symbol_time ON ml_features_dataset(symbol, feature_timestamp DESC);
CREATE INDEX idx_ml_features_quality ON ml_features_dataset(quality_score DESC, feature_completeness_pct DESC);
CREATE INDEX idx_ml_features_targets ON ml_features_dataset(direction_24h, volatility_class, feature_timestamp DESC);

-- ================================================================================================
-- 7. BUSINESS KPIS DATA MART
-- ================================================================================================

CREATE TABLE business_kpis (
    id SERIAL PRIMARY KEY,
    
    -- Date dimension
    date_key DATE NOT NULL,
    kpi_category VARCHAR(50) NOT NULL,
    kpi_name VARCHAR(100) NOT NULL,
    
    -- KPI values
    kpi_value NUMERIC(20,8),
    kpi_target NUMERIC(20,8),
    kpi_threshold_lower NUMERIC(20,8),
    kpi_threshold_upper NUMERIC(20,8),
    
    -- Performance indicators
    vs_target_pct NUMERIC(10,4),
    vs_previous_day_pct NUMERIC(10,4),
    vs_previous_week_pct NUMERIC(10,4),
    
    -- Status
    kpi_status VARCHAR(20), -- 'EXCELLENT', 'GOOD', 'WARNING', 'CRITICAL'
    
    -- Context
    kpi_description TEXT,
    calculation_formula TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id UUID,
    
    CONSTRAINT uq_business_kpi_date_name UNIQUE (date_key, kpi_category, kpi_name)
);

-- Create indexes
CREATE INDEX idx_business_kpis_category_date ON business_kpis(kpi_category, date_key DESC);
CREATE INDEX idx_business_kpis_status ON business_kpis(kpi_status, date_key DESC);

-- ================================================================================================
-- 8. DATA RETENTION POLICIES
-- ================================================================================================

-- Retention policies for gold layer tables
SELECT add_retention_policy('market_overview_daily', INTERVAL '5 years');
SELECT add_retention_policy('crypto_performance_metrics', INTERVAL '3 years');
SELECT add_retention_policy('trading_signals', INTERVAL '2 years');
SELECT add_retention_policy('portfolio_analysis_metrics', INTERVAL '10 years');
SELECT add_retention_policy('ml_features_dataset', INTERVAL '2 years');

-- ================================================================================================
-- TABLE COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON SCHEMA gold IS 'Gold layer containing business-ready data marts for analytics and reporting';

COMMENT ON TABLE market_overview_daily IS 'Daily market overview with aggregated statistics and key performance indicators';
COMMENT ON TABLE crypto_performance_metrics IS 'Comprehensive cryptocurrency performance metrics with technical indicators';
COMMENT ON TABLE trading_signals IS 'Machine learning generated trading signals with confidence scores and risk assessment';
COMMENT ON TABLE portfolio_analysis_metrics IS 'Portfolio performance tracking and risk analysis metrics';
COMMENT ON TABLE correlation_matrix IS 'Correlation analysis between cryptocurrency pairs over different time periods';
COMMENT ON TABLE ml_features_dataset IS 'Feature engineered dataset optimized for machine learning model training';
COMMENT ON TABLE business_kpis IS 'Key performance indicators for business monitoring and reporting';

-- ================================================================================================
-- GRANT PERMISSIONS
-- ================================================================================================

-- Grant permissions to application roles
-- GRANT SELECT ON ALL TABLES IN SCHEMA gold TO crypto_readonly;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gold TO crypto_readwrite;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA gold TO crypto_readwrite;

-- ================================================================================================
-- USAGE EXAMPLES
-- ================================================================================================

/*
-- Example: Get latest market overview
SELECT * FROM market_overview_daily
ORDER BY date_key DESC
LIMIT 7;

-- Example: Top performing cryptocurrencies this week
SELECT 
    symbol,
    name,
    close_price_usd,
    daily_return_pct,
    volume_usd,
    market_cap_rank
FROM crypto_performance_metrics
WHERE date_key >= CURRENT_DATE - INTERVAL '7 days'
  AND market_cap_rank <= 100
ORDER BY daily_return_pct DESC
LIMIT 10;

-- Example: Latest trading signals
SELECT 
    symbol,
    signal_type,
    signal_strength,
    confidence_level,
    price_at_signal,
    signal_reason
FROM trading_signals
WHERE signal_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
  AND confidence_level >= 0.7
ORDER BY signal_strength DESC;

-- Example: Portfolio performance over time
SELECT 
    date_key,
    total_value_usd,
    daily_return_pct,
    total_return_pct,
    sharpe_ratio,
    max_drawdown_pct
FROM portfolio_analysis_metrics
WHERE portfolio_id = 'default'
  AND date_key >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date_key DESC;

-- Example: High correlation pairs
SELECT 
    symbol_a,
    symbol_b,
    correlation_coefficient,
    correlation_strength,
    analysis_period_days
FROM correlation_matrix
WHERE date_key = CURRENT_DATE - INTERVAL '1 day'
  AND analysis_period_days = 30
  AND ABS(correlation_coefficient) > 0.7
ORDER BY ABS(correlation_coefficient) DESC;
*/
