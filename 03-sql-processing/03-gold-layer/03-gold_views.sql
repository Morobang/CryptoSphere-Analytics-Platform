-- =====================================================
-- GOLD LAYER - ANALYTICS VIEWS
-- =====================================================
-- Purpose: Create analytical views for Gold layer data marts
-- Layer: Gold (Analytics & Business Intelligence)
-- Server: SQL Server (DESKTOP-939GPCA)
-- Usage: Executive dashboards, reporting, and business intelligence
-- Date: 2025-01-26
-- =====================================================

USE cryptosphere_analytics;
GO

-- =====================================================
-- GOLD LAYER ANALYTICS VIEWS
-- =====================================================

-- View: Executive Market Dashboard
CREATE OR ALTER VIEW gold.v_executive_dashboard
AS
SELECT TOP 1
    mo.report_date,
    mo.total_cryptocurrencies,
    FORMAT(mo.total_market_cap_usd, 'C', 'en-US') AS total_market_cap_formatted,
    FORMAT(mo.total_volume_24h_usd, 'C', 'en-US') AS total_volume_24h_formatted,
    mo.bitcoin_dominance_pct,
    mo.ethereum_dominance_pct,
    mo.top_gainer_symbol,
    CONCAT('+', FORMAT(mo.top_gainer_change_pct, 'N2'), '%') AS top_gainer_change,
    mo.top_loser_symbol,
    CONCAT(FORMAT(mo.top_loser_change_pct, 'N2'), '%') AS top_loser_change,
    mo.high_quality_coins_count,
    
    -- Market Health Indicators
    CASE 
        WHEN mo.market_fear_greed_index >= 75 THEN 'EXTREME_GREED'
        WHEN mo.market_fear_greed_index >= 55 THEN 'GREED'
        WHEN mo.market_fear_greed_index >= 45 THEN 'NEUTRAL'
        WHEN mo.market_fear_greed_index >= 25 THEN 'FEAR'
        ELSE 'EXTREME_FEAR'
    END AS market_sentiment,
    
    CASE 
        WHEN mo.volatility_index <= 0.02 THEN 'LOW'
        WHEN mo.volatility_index <= 0.05 THEN 'MODERATE'
        WHEN mo.volatility_index <= 0.10 THEN 'HIGH'
        ELSE 'EXTREME'
    END AS market_volatility_level,
    
    -- Performance vs Previous Day
    LAG(mo.total_market_cap_usd) OVER (ORDER BY mo.report_date) AS prev_market_cap,
    ((mo.total_market_cap_usd - LAG(mo.total_market_cap_usd) OVER (ORDER BY mo.report_date)) / 
     LAG(mo.total_market_cap_usd) OVER (ORDER BY mo.report_date)) * 100 AS market_cap_change_pct

FROM gold.market_overview_daily mo
ORDER BY mo.report_date DESC;
GO

-- View: Trading Signals Dashboard
CREATE OR ALTER VIEW gold.v_trading_signals_dashboard
AS
SELECT 
    symbol,
    signal_type,
    confidence_score,
    signal_strength,
    current_price,
    target_price,
    CASE 
        WHEN target_price > current_price THEN ((target_price - current_price) / current_price) * 100
        ELSE ((current_price - target_price) / current_price) * 100
    END AS potential_return_pct,
    stop_loss_price,
    risk_reward_ratio,
    signal_algorithm,
    backtest_accuracy,
    market_condition,
    signal_date,
    
    -- Signal Quality Classification
    CASE 
        WHEN confidence_score >= 0.8 AND signal_strength = 'STRONG' THEN 'HIGH_CONVICTION'
        WHEN confidence_score >= 0.6 AND signal_strength IN ('STRONG', 'MODERATE') THEN 'MEDIUM_CONVICTION'
        ELSE 'LOW_CONVICTION'
    END AS conviction_level,
    
    -- Time since signal
    DATEDIFF(HOUR, signal_date, GETDATE()) AS hours_since_signal

FROM gold.trading_signals
WHERE signal_date >= DATEADD(DAY, -7, GETDATE())
    AND signal_type IN ('BUY', 'SELL');
GO

-- View: Technical Analysis Summary
CREATE OR ALTER VIEW gold.v_technical_analysis_summary
AS
SELECT 
    pm.symbol,
    pm.analysis_date,
    pm.sma_7d,
    pm.sma_30d,
    pm.rsi_14d,
    pm.volatility_7d,
    pm.return_7d,
    pm.volume_ratio_24h,
    
    -- Technical Indicators Summary
    CASE 
        WHEN pm.rsi_14d > 70 THEN 'OVERBOUGHT'
        WHEN pm.rsi_14d < 30 THEN 'OVERSOLD'
        ELSE 'NEUTRAL'
    END AS rsi_signal,
    
    CASE 
        WHEN pm.sma_7d > pm.sma_30d THEN 'BULLISH'
        WHEN pm.sma_7d < pm.sma_30d THEN 'BEARISH'
        ELSE 'NEUTRAL'
    END AS trend_signal,
    
    CASE 
        WHEN pm.volume_ratio_24h > 2.0 THEN 'HIGH_VOLUME'
        WHEN pm.volume_ratio_24h > 1.5 THEN 'ELEVATED_VOLUME'
        WHEN pm.volume_ratio_24h < 0.5 THEN 'LOW_VOLUME'
        ELSE 'NORMAL_VOLUME'
    END AS volume_signal,
    
    CASE 
        WHEN pm.volatility_7d > 0.10 THEN 'HIGH_VOLATILITY'
        WHEN pm.volatility_7d > 0.05 THEN 'MODERATE_VOLATILITY'
        ELSE 'LOW_VOLATILITY'
    END AS volatility_classification,
    
    -- Overall Technical Score (0-100)
    (
        CASE WHEN pm.rsi_14d BETWEEN 30 AND 70 THEN 25 ELSE 0 END +
        CASE WHEN pm.sma_7d > pm.sma_30d THEN 25 ELSE 0 END +
        CASE WHEN pm.volume_ratio_24h > 1.0 THEN 25 ELSE 0 END +
        CASE WHEN pm.return_7d > 0 THEN 25 ELSE 0 END
    ) AS technical_score

FROM gold.crypto_performance_metrics pm
WHERE pm.analysis_date >= DATEADD(DAY, -7, GETDATE());
GO

-- View: ML Features Summary
CREATE OR ALTER VIEW gold.v_ml_features_summary
AS
SELECT 
    symbol,
    feature_date,
    feature_completeness,
    data_quality_score,
    
    -- Price Features
    price_current,
    price_change_24h,
    price_volatility_7d,
    
    -- Technical Features
    rsi_14,
    bb_position,
    sma_trend_7d,
    
    -- Market Features
    market_cap_rank,
    volume_rank,
    market_dominance,
    
    -- Target Variables
    target_price_change_24h,
    target_direction_24h,
    
    -- Feature Quality Assessment
    CASE 
        WHEN feature_completeness >= 0.90 AND data_quality_score >= 0.80 THEN 'EXCELLENT'
        WHEN feature_completeness >= 0.70 AND data_quality_score >= 0.60 THEN 'GOOD'
        WHEN feature_completeness >= 0.50 AND data_quality_score >= 0.40 THEN 'FAIR'
        ELSE 'POOR'
    END AS feature_quality_tier,
    
    -- ML Readiness Score
    (feature_completeness * 0.6 + data_quality_score * 0.4) AS ml_readiness_score

FROM gold.ml_features
WHERE feature_date >= DATEADD(DAY, -30, GETDATE());
GO

-- View: Risk Dashboard
CREATE OR ALTER VIEW gold.v_risk_dashboard
AS
SELECT 
    rm.symbol,
    rm.calculation_date,
    rm.var_95_1d,
    rm.var_99_1d,
    rm.sharpe_ratio_30d,
    rm.max_drawdown_30d,
    rm.current_drawdown,
    rm.correlation_to_btc,
    rm.liquidity_score,
    
    -- Risk Classification
    CASE 
        WHEN ABS(rm.var_95_1d) > 20 THEN 'HIGH_RISK'
        WHEN ABS(rm.var_95_1d) > 10 THEN 'MEDIUM_RISK'
        ELSE 'LOW_RISK'
    END AS risk_category,
    
    CASE 
        WHEN rm.sharpe_ratio_30d > 2.0 THEN 'EXCELLENT'
        WHEN rm.sharpe_ratio_30d > 1.0 THEN 'GOOD'
        WHEN rm.sharpe_ratio_30d > 0.5 THEN 'FAIR'
        ELSE 'POOR'
    END AS risk_adjusted_performance,
    
    CASE 
        WHEN rm.liquidity_score >= 0.8 THEN 'HIGHLY_LIQUID'
        WHEN rm.liquidity_score >= 0.6 THEN 'LIQUID'
        WHEN rm.liquidity_score >= 0.4 THEN 'MODERATELY_LIQUID'
        ELSE 'ILLIQUID'
    END AS liquidity_tier,
    
    -- Risk Score (0-100, lower is better)
    LEAST(100, 
        ABS(rm.var_95_1d) * 2 + 
        ABS(rm.max_drawdown_30d) + 
        (1 - ISNULL(rm.liquidity_score, 0)) * 20
    ) AS composite_risk_score

FROM gold.risk_metrics rm
WHERE rm.calculation_date >= DATEADD(DAY, -7, GETDATE());
GO

-- View: Portfolio Performance Summary
CREATE OR ALTER VIEW gold.v_portfolio_performance_summary
AS
SELECT 
    portfolio_name,
    analysis_date,
    FORMAT(total_value_usd, 'C', 'en-US') AS total_value_formatted,
    number_of_assets,
    largest_position_pct,
    portfolio_return_30d,
    portfolio_volatility_30d,
    portfolio_var_95_1d,
    diversification_ratio,
    concentration_risk_score,
    
    -- Performance Classification
    CASE 
        WHEN portfolio_return_30d > 20 THEN 'EXCELLENT'
        WHEN portfolio_return_30d > 10 THEN 'GOOD'
        WHEN portfolio_return_30d > 0 THEN 'POSITIVE'
        WHEN portfolio_return_30d > -10 THEN 'SLIGHT_LOSS'
        ELSE 'POOR'
    END AS performance_tier,
    
    -- Risk-Adjusted Score
    CASE 
        WHEN portfolio_volatility_30d > 0 THEN portfolio_return_30d / portfolio_volatility_30d 
        ELSE NULL 
    END AS risk_adjusted_return,
    
    -- Portfolio Health Score (0-100)
    (
        CASE WHEN portfolio_return_30d > 0 THEN 30 ELSE 0 END +
        CASE WHEN diversification_ratio > 0.8 THEN 25 ELSE (diversification_ratio * 25) END +
        CASE WHEN concentration_risk_score < 0.3 THEN 25 ELSE ((1-concentration_risk_score) * 25) END +
        CASE WHEN largest_position_pct < 50 THEN 20 ELSE ((100-largest_position_pct)/100 * 20) END
    ) AS portfolio_health_score,
    
    needs_rebalancing,
    suggested_actions

FROM gold.portfolio_analytics
WHERE analysis_date >= DATEADD(DAY, -30, GETDATE());
GO

-- View: Market Regime Dashboard
CREATE OR ALTER VIEW gold.v_market_regime_dashboard
AS
SELECT TOP 1
    analysis_date,
    current_regime,
    regime_strength,
    regime_duration_days,
    fear_greed_index,
    volatility_regime,
    overall_trend,
    trend_strength,
    FORMAT(market_support_level, 'C', 'en-US') AS support_level_formatted,
    FORMAT(market_resistance_level, 'C', 'en-US') AS resistance_level_formatted,
    current_position_pct,
    regime_change_probability,
    predicted_next_regime,
    confidence_level,
    
    -- Regime Health Indicators
    CASE 
        WHEN regime_strength >= 0.8 THEN 'STRONG_REGIME'
        WHEN regime_strength >= 0.6 THEN 'MODERATE_REGIME'
        ELSE 'WEAK_REGIME'
    END AS regime_stability,
    
    CASE 
        WHEN regime_change_probability >= 0.7 THEN 'LIKELY_CHANGE'
        WHEN regime_change_probability >= 0.4 THEN 'POSSIBLE_CHANGE'
        ELSE 'STABLE'
    END AS change_likelihood,
    
    -- Market Position Assessment
    CASE 
        WHEN current_position_pct >= 80 THEN 'NEAR_RESISTANCE'
        WHEN current_position_pct >= 60 THEN 'UPPER_RANGE'
        WHEN current_position_pct >= 40 THEN 'MID_RANGE'
        WHEN current_position_pct >= 20 THEN 'LOWER_RANGE'
        ELSE 'NEAR_SUPPORT'
    END AS market_position_assessment

FROM gold.market_regime_analysis
ORDER BY analysis_date DESC;
GO

-- View: Top Performers Analysis
CREATE OR ALTER VIEW gold.v_top_performers_analysis
AS
WITH performance_ranking AS (
    SELECT 
        pm.symbol,
        pm.analysis_date,
        pm.return_7d,
        pm.return_30d,
        pm.volatility_7d,
        pm.sharpe_ratio_30d,
        ts.confidence_score,
        ts.signal_type,
        
        -- Performance Rankings
        ROW_NUMBER() OVER (ORDER BY pm.return_7d DESC) AS rank_7d_return,
        ROW_NUMBER() OVER (ORDER BY pm.return_30d DESC) AS rank_30d_return,
        ROW_NUMBER() OVER (ORDER BY pm.sharpe_ratio_30d DESC) AS rank_sharpe,
        
        -- Combined Performance Score
        (pm.return_7d * 0.3 + pm.return_30d * 0.4 + ISNULL(pm.sharpe_ratio_30d, 0) * 10 * 0.3) AS performance_score
        
    FROM gold.crypto_performance_metrics pm
    LEFT JOIN gold.trading_signals ts ON pm.symbol = ts.symbol 
        AND CAST(ts.signal_date AS DATE) = pm.analysis_date
    WHERE pm.analysis_date >= DATEADD(DAY, -7, GETDATE())
)
SELECT TOP 20
    symbol,
    analysis_date,
    return_7d,
    return_30d,
    volatility_7d,
    sharpe_ratio_30d,
    performance_score,
    rank_7d_return,
    rank_30d_return,
    rank_sharpe,
    signal_type,
    confidence_score,
    
    -- Performance Tier
    CASE 
        WHEN performance_score > 50 THEN 'STAR_PERFORMER'
        WHEN performance_score > 25 THEN 'STRONG_PERFORMER'
        WHEN performance_score > 0 THEN 'AVERAGE_PERFORMER'
        ELSE 'UNDERPERFORMER'
    END AS performance_tier

FROM performance_ranking
ORDER BY performance_score DESC;
GO

-- View: Data Quality Summary
CREATE OR ALTER VIEW gold.v_data_quality_summary
AS
SELECT 
    'Gold Layer Data Quality' AS summary_type,
    COUNT(DISTINCT mo.report_date) AS market_overview_reports,
    COUNT(DISTINCT pm.symbol) AS symbols_with_performance_metrics,
    COUNT(ts.id) AS total_trading_signals,
    COUNT(ml.id) AS total_ml_features,
    
    -- Quality Metrics
    AVG(ml.data_quality_score) AS avg_ml_data_quality,
    AVG(ml.feature_completeness) AS avg_feature_completeness,
    
    -- Signal Quality
    COUNT(CASE WHEN ts.confidence_score >= 0.7 THEN 1 END) AS high_confidence_signals,
    CAST(COUNT(CASE WHEN ts.confidence_score >= 0.7 THEN 1 END) * 100.0 / COUNT(ts.id) AS DECIMAL(5,2)) AS high_confidence_signal_pct,
    
    -- Freshness Metrics  
    MAX(mo.created_timestamp) AS latest_market_overview,
    MAX(pm.created_timestamp) AS latest_performance_metrics,
    MAX(ts.created_timestamp) AS latest_trading_signal,
    MAX(ml.created_timestamp) AS latest_ml_features,
    
    DATEDIFF(HOUR, MAX(mo.created_timestamp), GETDATE()) AS hours_since_last_overview

FROM gold.market_overview_daily mo
FULL OUTER JOIN gold.crypto_performance_metrics pm ON 1=1
FULL OUTER JOIN gold.trading_signals ts ON 1=1  
FULL OUTER JOIN gold.ml_features ml ON 1=1
WHERE mo.report_date >= DATEADD(DAY, -7, GETDATE())
    AND pm.analysis_date >= DATEADD(DAY, -7, GETDATE())
    AND ts.signal_date >= DATEADD(DAY, -7, GETDATE())
    AND ml.feature_date >= DATEADD(DAY, -7, GETDATE());
GO

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

PRINT '';
PRINT '🥇 =====================================================';
PRINT '   GOLD LAYER ANALYTICS VIEWS CREATED';
PRINT '=====================================================';
PRINT '';
PRINT '✅ Views Created:';
PRINT '   • gold.v_executive_dashboard - Executive summary dashboard';
PRINT '   • gold.v_trading_signals_dashboard - Trading signals overview';
PRINT '   • gold.v_technical_analysis_summary - Technical indicators summary';
PRINT '   • gold.v_ml_features_summary - ML features quality overview';
PRINT '   • gold.v_risk_dashboard - Risk metrics and analysis';
PRINT '   • gold.v_portfolio_performance_summary - Portfolio analytics';
PRINT '   • gold.v_market_regime_dashboard - Market regime analysis';
PRINT '   • gold.v_top_performers_analysis - Top performing assets';
PRINT '   • gold.v_data_quality_summary - Gold layer data quality';
PRINT '';
PRINT '📊 Purpose: Executive dashboards and business intelligence';
PRINT '🎯 Usage: SELECT * FROM gold.v_executive_dashboard;';
PRINT '';
PRINT '💡 Gold Layer Complete: Schema + ETL + Views';
PRINT '=====================================================';
GO