# 📓 CryptoSphere Notebooks - Data Analysis Pipeline

## 🎯 **Notebook Pipeline Overview**

This is a **proper sequential notebook architecture** for cryptocurrency data analysis, matching the medallion architecture pattern.

### 📊 **Analysis Flow: Collection → Cleaning → Exploration → Transformation**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  01-DATA-       │    │  02-DATA-       │    │ 03-EXPLORATORY- │    │ 04-DATA-        │
│  ACQUISITION    │───▶│  CLEANING       │───▶│ ANALYSIS        │───▶│ TRANSFORMATION  │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
   • API Collection        • Data Quality         • Statistical EDA      • Feature Engineering
   • Data Validation       • Missing Values       • Correlation Analysis • Data Aggregation
   • Incremental Loading   • Outlier Detection    • Trend Analysis       • Derived Metrics
   • Error Handling        • Type Conversion      • Visualization        • ML Preparation
```

## 📂 **Directory Structure & Purpose**

### 00-NOTEBOOK-SETUP (Master Control)
**Purpose**: Environment setup, configuration, and notebook management
- `README.md` - This master guide
- `notebook_config.yaml` - Jupyter configuration
- `environment_setup.ipynb` - Dependencies and environment setup
- `SETUP_AND_USAGE_GUIDE.md` - Step-by-step usage instructions

### 01-DATA-ACQUISITION (Step 1: Data Collection)
**Purpose**: Collect raw data from various cryptocurrency APIs
- `api_data_collection.ipynb` - Main data collection notebook
- `data_source_validation.ipynb` - Validate API responses
- `incremental_loading.ipynb` - Handle incremental data updates
- `error_handling_recovery.ipynb` - Handle API failures and recovery

### 02-DATA-CLEANING (Step 2: Data Quality)
**Purpose**: Clean and validate collected data
- `data_quality_assessment.ipynb` - Assess data quality metrics
- `missing_value_treatment.ipynb` - Handle missing/null values
- `outlier_detection_treatment.ipynb` - Detect and handle outliers
- `data_type_standardization.ipynb` - Standardize data types

### 03-EXPLORATORY-ANALYSIS (Step 3: Data Understanding)
**Purpose**: Understand data patterns and relationships
- `market_trend_analysis.ipynb` - Analyze market trends
- `correlation_analysis.ipynb` - Find correlations between cryptos
- `statistical_profiling.ipynb` - Statistical data profiling
- `visualization_dashboard.ipynb` - Create interactive visualizations

### 04-DATA-TRANSFORMATION (Step 4: Feature Engineering)
**Purpose**: Transform data for database storage and ML preparation
- `feature_engineering.ipynb` - Create new features
- `data_aggregation.ipynb` - Aggregate data by time periods
- `derived_metrics.ipynb` - Calculate technical indicators
- `ml_preparation.ipynb` - Prepare data for machine learning

### shared/ (Shared Utilities)
**Purpose**: Common functions and utilities used across notebooks
- `notebook_helpers.py` - Helper functions for notebooks
- `visualization_utils.py` - Common visualization functions
- `data_connectors.py` - Database and API connection utilities
- `config_loader.py` - Configuration management

## 🔄 **Execution Flow**

### **Phase 1: Setup (00-NOTEBOOK-SETUP)**
1. Run `environment_setup.ipynb` to configure environment
2. Review `notebook_config.yaml` for settings
3. Follow `SETUP_AND_USAGE_GUIDE.md` for first-time setup

### **Phase 2: Data Collection (01-DATA-ACQUISITION)**
1. Start with `api_data_collection.ipynb` for initial data fetch
2. Use `data_source_validation.ipynb` to validate API responses
3. Set up `incremental_loading.ipynb` for ongoing data collection
4. Configure `error_handling_recovery.ipynb` for robustness

### **Phase 3: Data Cleaning (02-DATA-CLEANING)**
1. Run `data_quality_assessment.ipynb` to understand data issues
2. Address missing values with `missing_value_treatment.ipynb`
3. Handle outliers using `outlier_detection_treatment.ipynb`
4. Standardize types with `data_type_standardization.ipynb`

### **Phase 4: Exploration (03-EXPLORATORY-ANALYSIS)**
1. Analyze trends with `market_trend_analysis.ipynb`
2. Find relationships using `correlation_analysis.ipynb`
3. Profile data with `statistical_profiling.ipynb`
4. Create visuals with `visualization_dashboard.ipynb`

### **Phase 5: Transformation (04-DATA-TRANSFORMATION)**
1. Engineer features with `feature_engineering.ipynb`
2. Aggregate data using `data_aggregation.ipynb`
3. Calculate metrics with `derived_metrics.ipynb`
4. Prepare for ML with `ml_preparation.ipynb`

## 🎯 **Integration Points**

### **Input Sources**
- CoinMarketCap API
- Raw CSV files from `01-data/raw/`
- Configuration from `shared/core/config_manager.py`

### **Output Destinations**
- Cleaned CSV files to `01-data/processed/`
- Database insertion via `03-sql-processing/01-BRONZE-LAYER/`
- ML-ready datasets to `04-ml-models/01-DATA-PREPARATION/`

### **Shared Dependencies**
- `shared/core/api_client.py` - API connections
- `shared/core/database_manager.py` - Database operations
- `shared/data/data_cleaner.py` - Data cleaning utilities
- `shared/utils/logging_utils.py` - Logging functionality

## 📋 **Execution Checklist**

### ✅ **Before Starting**
- [ ] Environment is set up (00-NOTEBOOK-SETUP)
- [ ] API keys are configured in `.env` file
- [ ] Database connection is established
- [ ] Required Python packages are installed

### ✅ **Data Collection Phase**
- [ ] API data collection is working (01-DATA-ACQUISITION)
- [ ] Data validation passes (data quality checks)
- [ ] Incremental loading is configured
- [ ] Error handling is tested

### ✅ **Data Processing Phase**
- [ ] Data cleaning is complete (02-DATA-CLEANING)
- [ ] Missing values are handled appropriately
- [ ] Outliers are detected and treated
- [ ] Data types are standardized

### ✅ **Analysis Phase**
- [ ] EDA is complete (03-EXPLORATORY-ANALYSIS)
- [ ] Key patterns are identified
- [ ] Correlations are documented
- [ ] Visualizations are created

### ✅ **Preparation Phase**
- [ ] Features are engineered (04-DATA-TRANSFORMATION)
- [ ] Data is aggregated as needed
- [ ] Technical indicators are calculated
- [ ] ML datasets are prepared

## 🚀 **Quick Start Commands**

```python
# 1. Setup environment
%run 00-NOTEBOOK-SETUP/environment_setup.ipynb

# 2. Collect data
%run 01-DATA-ACQUISITION/api_data_collection.ipynb

# 3. Clean data
%run 02-DATA-CLEANING/data_quality_assessment.ipynb

# 4. Explore data
%run 03-EXPLORATORY-ANALYSIS/market_trend_analysis.ipynb

# 5. Transform data
%run 04-DATA-TRANSFORMATION/feature_engineering.ipynb
```

## 🎯 **Success Metrics**

- **Data Quality**: >95% data completeness
- **Processing Speed**: <5 minutes per 1000 records
- **Error Rate**: <1% API call failures
- **Coverage**: All major cryptocurrencies included
- **Freshness**: Data updated every 15 minutes

This notebook architecture ensures:
- **Clear Sequential Flow**: Each phase builds upon the previous
- **No Duplication**: Shared utilities prevent code repetition
- **Easy Navigation**: Numbered directories show natural progression
- **Quality Assurance**: Built-in validation and error handling
- **Scalable Design**: Easy to add new analysis notebooks