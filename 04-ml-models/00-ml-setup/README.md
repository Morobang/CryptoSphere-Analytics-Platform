# 🤖 CryptoSphere ML Models - Machine Learning Pipeline

## 🎯 **ML Pipeline Overview**

This is a **proper sequential ML architecture** for cryptocurrency prediction and analysis, matching the medallion architecture pattern.

### 🧠 **ML Flow: Data → Exploration → Training → Validation → Deployment → Monitoring**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 01-EXPLORATORY  │    │ 02-DATA-        │    │ 03-MODEL-       │    │ 04-MODEL-       │
│ ANALYSIS        │───▶│ PREPROCESSING   │───▶│ TRAINING        │───▶│ PERSISTENCE     │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
   • Pattern Discovery     • Feature Engineering    • Model Training        • Model Storage
   • Data Understanding    • Data Scaling           • Hyperparameter Tuning • Version Control
   • Feature Analysis      • Train/Test Splits      • Cross Validation      • Model Registry
   • Market Insights       • ML Data Preparation    • Algorithm Selection   • Deployment Prep

┌─────────────────┐    ┌─────────────────┐
│ 05-PREDICTION   │    │ 06-MODEL-       │
│ PIPELINE        │───▶│ EVALUATION      │
│                 │    │                 │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
   • Real-time Prediction   • Performance Metrics
   • Batch Processing       • Model Comparison
   • API Endpoints          • Drift Detection
   • Production Serving     • Continuous Monitoring
```

## 📂 **Directory Structure & Purpose**

### 00-ML-SETUP (Master Control)
**Purpose**: ML environment setup, configuration, and pipeline management
- `README.md` - This master guide
- `ml_config.yaml` - ML pipeline configuration
- `environment_setup.py` - ML dependencies and environment setup
- `SETUP_AND_USAGE_GUIDE.md` - Step-by-step ML pipeline usage
- `model_registry_setup.sql` - Database setup for model tracking

### 01-EXPLORATORY-ANALYSIS (Step 1: Data Understanding)
**Purpose**: Explore data patterns and identify ML opportunities
- `notebooks/01-crypto_data_exploration.ipynb` - Main data exploration
- `notebooks/02-feature_engineering_exploration.ipynb` - Feature discovery
- `src/crypto_data_explorer.py` - Data exploration utilities
- `src/market_pattern_analyzer.py` - Pattern detection algorithms

### 02-DATA-PREPROCESSING (Step 2: ML Data Preparation)
**Purpose**: Prepare data specifically for machine learning models
- `notebooks/01-data_preprocessing.ipynb` - Data preprocessing workflow
- `src/data_preprocessor.py` - Main preprocessing pipeline
- `src/data_scaler.py` - Feature scaling utilities
- `src/feature_engineer.py` - Feature engineering functions

### 03-MODEL-TRAINING (Step 3: Model Development)
**Purpose**: Train and optimize machine learning models
- `notebooks/01-model_training.ipynb` - Model training workflow
- `src/model_trainer.py` - Training pipeline manager
- `src/prediction_models.py` - Model definitions and architectures
- `src/hyperparameter_tuner.py` - Automated hyperparameter optimization

### 04-MODEL-PERSISTENCE (Step 4: Model Storage)
**Purpose**: Save, version, and manage trained models
- `src/model_registry.py` - Model versioning and storage
- `models/` - Saved model artifacts (created dynamically)
- `metadata/` - Model metadata and tracking (created dynamically)

### 05-PREDICTION-PIPELINE (Step 5: Production Deployment)
**Purpose**: Deploy models for real-time and batch predictions
- `src/prediction_service.py` - Production prediction API
- `src/batch_processor.py` - Batch prediction utilities
- `src/real_time_predictor.py` - Real-time prediction service

### 06-MODEL-EVALUATION (Step 6: Performance Monitoring)
**Purpose**: Evaluate model performance and monitor for drift
- `notebooks/01-model_evaluation.ipynb` - Model evaluation workflow
- `src/model_evaluator.py` - Performance evaluation utilities
- `src/drift_detector.py` - Model drift detection
- `src/performance_monitor.py` - Continuous monitoring

## 🔄 **ML Pipeline Execution Flow**

### **Phase 1: Setup (00-ML-SETUP)**
1. Run `environment_setup.py` to configure ML environment
2. Review `ml_config.yaml` for pipeline settings
3. Follow `SETUP_AND_USAGE_GUIDE.md` for first-time setup
4. Execute `model_registry_setup.sql` to create tracking tables

### **Phase 2: Data Exploration (01-EXPLORATORY-ANALYSIS)**
1. Start with `01-crypto_data_exploration.ipynb` for data understanding
2. Use `02-feature_engineering_exploration.ipynb` for feature discovery
3. Analyze patterns with `crypto_data_explorer.py`
4. Identify opportunities with `market_pattern_analyzer.py`

### **Phase 3: Data Preprocessing (02-DATA-PREPROCESSING)**
1. Run `01-data_preprocessing.ipynb` for data preparation workflow
2. Use `data_preprocessor.py` for automated preprocessing
3. Scale features with `data_scaler.py`
4. Engineer features using `feature_engineer.py`

### **Phase 4: Model Training (03-MODEL-TRAINING)**
1. Execute `01-model_training.ipynb` for training workflow
2. Use `model_trainer.py` for automated training
3. Optimize with `hyperparameter_tuner.py`
4. Define models in `prediction_models.py`

### **Phase 5: Model Storage (04-MODEL-PERSISTENCE)**
1. Save models using `model_registry.py`
2. Version control trained models
3. Store metadata and performance metrics
4. Prepare for deployment

### **Phase 6: Production Deployment (05-PREDICTION-PIPELINE)**
1. Deploy with `prediction_service.py`
2. Set up batch processing with `batch_processor.py`
3. Enable real-time predictions with `real_time_predictor.py`
4. Monitor production performance

### **Phase 7: Performance Monitoring (06-MODEL-EVALUATION)**
1. Evaluate with `01-model_evaluation.ipynb`
2. Monitor performance using `model_evaluator.py`
3. Detect drift with `drift_detector.py`
4. Continuous monitoring with `performance_monitor.py`

## 🎯 **Integration Points**

### **Input Sources**
- Gold layer data from `03-sql-processing/03-GOLD-LAYER/`
- Processed data from `02-notebooks/04-DATA-TRANSFORMATION/`
- Real-time data from `shared/core/api_client.py`

### **Output Destinations**
- Model predictions to Gold layer analytics tables
- Real-time predictions via API endpoints
- Batch predictions to `01-data/processed/predictions/`

### **Shared Dependencies**
- `shared/core/database_manager.py` - Database operations
- `shared/data/data_preprocessor.py` - Data preprocessing utilities
- `shared/utils/monitoring_utils.py` - Monitoring functionality

## 📋 **ML Pipeline Checklist**

### ✅ **Before Starting**
- [ ] ML environment is set up (00-ML-SETUP)
- [ ] Data sources are available (Gold layer or processed data)
- [ ] Model registry database is configured
- [ ] Required Python ML packages are installed

### ✅ **Data Exploration Phase**
- [ ] Data exploration is complete (01-EXPLORATORY-ANALYSIS)
- [ ] Key patterns are identified
- [ ] Feature importance is analyzed
- [ ] ML opportunities are documented

### ✅ **Data Preprocessing Phase**
- [ ] Data preprocessing pipeline is built (02-DATA-PREPROCESSING)
- [ ] Features are engineered and scaled
- [ ] Train/validation/test splits are created
- [ ] Data quality is validated

### ✅ **Model Training Phase**
- [ ] Models are trained and optimized (03-MODEL-TRAINING)
- [ ] Hyperparameters are tuned
- [ ] Cross-validation is performed
- [ ] Model performance is acceptable

### ✅ **Model Storage Phase**
- [ ] Models are saved and versioned (04-MODEL-PERSISTENCE)
- [ ] Metadata is stored
- [ ] Performance metrics are recorded
- [ ] Deployment artifacts are prepared

### ✅ **Production Phase**
- [ ] Prediction pipeline is deployed (05-PREDICTION-PIPELINE)
- [ ] Real-time predictions are working
- [ ] Batch processing is configured
- [ ] API endpoints are tested

### ✅ **Monitoring Phase**
- [ ] Model evaluation is automated (06-MODEL-EVALUATION)
- [ ] Performance monitoring is active
- [ ] Drift detection is configured
- [ ] Retraining pipeline is ready

## 🚀 **Quick Start Commands**

```python
# 1. Setup ML environment
python 00-ML-SETUP/environment_setup.py

# 2. Explore data
jupyter notebook 01-EXPLORATORY-ANALYSIS/notebooks/01-crypto_data_exploration.ipynb

# 3. Preprocess data
python 02-DATA-PREPROCESSING/src/data_preprocessor.py

# 4. Train models
python 03-MODEL-TRAINING/src/model_trainer.py

# 5. Save models
python 04-MODEL-PERSISTENCE/src/model_registry.py

# 6. Deploy predictions
python 05-PREDICTION-PIPELINE/src/prediction_service.py

# 7. Monitor performance
python 06-MODEL-EVALUATION/src/performance_monitor.py
```

## 🎯 **Success Metrics**

- **Model Accuracy**: >85% prediction accuracy
- **Training Speed**: <30 minutes per model
- **Prediction Latency**: <100ms for real-time predictions
- **Data Coverage**: All major cryptocurrencies included
- **Model Freshness**: Models retrained weekly

## 🔮 **Supported ML Use Cases**

### **Price Prediction Models**
- Short-term price forecasting (1-24 hours)
- Long-term trend prediction (1-30 days)
- Support/resistance level identification

### **Classification Models**
- Bull/bear market classification
- Volatility regime detection
- Trading signal generation

### **Anomaly Detection**
- Price anomaly detection
- Volume spike identification
- Market manipulation detection

### **Risk Models**
- Portfolio risk assessment
- Value-at-Risk (VaR) calculation
- Correlation analysis

This ML architecture ensures:
- **Clear Sequential Flow**: Each phase builds upon the previous
- **No Duplication**: Shared utilities prevent code repetition
- **Easy Navigation**: Numbered directories show natural progression
- **Production Ready**: Built-in deployment and monitoring capabilities
- **Scalable Design**: Easy to add new models and use cases