# 🤖 ML Models - Cryptocurrency Price Prediction

This folder contains the complete machine learning pipeline for cryptocurrency price prediction and analysis.

## 📁 Folder Structure

```
📁 04-ml-models/
├── 📄 ml_config.yaml                   # ML configuration file
├── 📄 README.md                        # This file
├── 
├── 📁 01-exploratory-analysis/         # 🔍 Data Exploration
│   ├── 📁 notebooks/                   # Interactive analysis
│   │   ├── 📄 01-crypto_data_exploration.ipynb
│   │   └── 📄 02-feature_engineering_exploration.ipynb
│   └── 📁 src/                         # Python modules
│       ├── 📄 __init__.py
│       ├── 📄 crypto_data_explorer.py  # Comprehensive data analysis
│       └── 📄 market_pattern_analyzer.py # Market pattern detection
├── 
├── 📁 02-data-preprocessing/           # 🛠️ Data Preparation
│   ├── 📁 notebooks/
│   │   └── 📄 01-data_preprocessing.ipynb
│   └── 📁 src/
│       ├── 📄 __init__.py
│       ├── 📄 data_preprocessor.py     # Original preprocessing
│       ├── 📄 feature_engineer.py     # Advanced feature creation
│       └── 📄 data_scaler.py          # Data scaling & normalization
├── 
├── 📁 03-model-training/               # 🎯 Model Training
│   ├── 📁 notebooks/
│   │   └── 📄 01-model_training.ipynb
│   └── 📁 src/
│       ├── 📄 __init__.py
│       ├── 📄 model_trainer.py        # Original model trainer
│       ├── 📄 prediction_models.py    # ML model collection
│       └── 📄 hyperparameter_tuner.py # Automated tuning
├── 
├── 📁 04-model-persistence/            # 💾 Model Storage
│   ├── 📁 notebooks/
│   └── 📁 src/
│       ├── 📄 __init__.py
│       └── 📄 model_registry.py       # Model versioning & storage
├── 
├── 📁 05-prediction-pipeline/          # 🔮 Making Predictions
│   ├── 📁 notebooks/
│   └── 📁 src/
│       ├── 📄 __init__.py
│       └── 📄 prediction_service.py   # Real-time predictions
├── 
└── 📁 06-model-evaluation/             # 📊 Performance Analysis
    ├── 📁 notebooks/
    │   └── 📄 01-model_evaluation.ipynb
    └── 📁 src/
        ├── 📄 __init__.py
        └── 📄 model_evaluator.py      # Comprehensive evaluation
```

## 🎯 What Each Module Does

### 🔍 01-exploratory-analysis
**Purpose**: Understand cryptocurrency data patterns and relationships

**Key Components**:
- **Data Explorer**: Analyzes price patterns, correlations, and market trends
- **Pattern Analyzer**: Identifies support/resistance levels, trend channels, breakout patterns

**Use When**: Starting a new analysis, understanding market behavior, feature discovery

### 🛠️ 02-data-preprocessing  
**Purpose**: Prepare cryptocurrency data for machine learning models

**Key Components**:
- **Feature Engineer**: Creates 50+ technical indicators and features
- **Data Scaler**: Handles scaling, normalization, and missing values
- **Data Preprocessor**: Original preprocessing functionality

**Use When**: Before training any ML model, preparing data for analysis

### 🎯 03-model-training
**Purpose**: Train and optimize cryptocurrency prediction models

**Key Components**:
- **Prediction Models**: 8+ different ML algorithms (Random Forest, XGBoost, etc.)
- **Hyperparameter Tuner**: Automated parameter optimization
- **Model Trainer**: Original training functionality

**Use When**: Training new models, comparing algorithms, optimizing performance

### 💾 04-model-persistence
**Purpose**: Save, version, and manage trained models

**Key Components**:
- **Model Registry**: Version control and metadata tracking for models

**Use When**: Saving trained models, deploying models, tracking model versions

### 🔮 05-prediction-pipeline
**Purpose**: Make real-time cryptocurrency price predictions

**Key Components**:
- **Prediction Service**: Real-time and batch prediction capabilities

**Use When**: Making live predictions, automated trading signals, backtesting

### 📊 06-model-evaluation
**Purpose**: Evaluate and compare model performance

**Key Components**:
- **Model Evaluator**: Comprehensive performance metrics and analysis

**Use When**: Comparing models, validating performance, generating reports

## 🚀 Quick Start Guide

### 1. Interactive Analysis (Use Notebooks)
```bash
# Start Jupyter in the project root
jupyter notebook

# Navigate to any notebook, for example:
# 04-ml-models/01-exploratory-analysis/notebooks/01-crypto_data_exploration.ipynb
```

### 2. Automated Processing (Use Python Scripts)
```python
# Example: Complete ML pipeline
from ml_models.src.feature_engineer import CryptoFeatureEngineer
from ml_models.src.prediction_models import CryptoPredictionModels
from ml_models.src.model_evaluator import CryptoModelEvaluator

# 1. Engineer features
engineer = CryptoFeatureEngineer()
featured_data = engineer.process_features(crypto_data, 'BTC')

# 2. Train models
trainer = CryptoPredictionModels()
results = trainer.train_multiple_models(X_train, y_train, X_val, y_val)

# 3. Evaluate performance
evaluator = CryptoModelEvaluator()
evaluation = evaluator.evaluate_multiple_models(trained_models, X_test, y_test)
```

## 🔧 Configuration

Edit `ml_config.yaml` to customize:

```yaml
# Which models to train
model_training:
  default_models:
    - "random_forest"
    - "xgboost" 
    - "lightgbm"

# Which cryptocurrencies to analyze
crypto_settings:
  target_cryptos:
    - "BTC"
    - "ETH"
    - "ADA"
```

## 📈 Available Models

1. **Linear Regression** - Simple baseline model
2. **Ridge Regression** - Regularized linear model  
3. **Random Forest** - Ensemble tree-based model
4. **XGBoost** - Gradient boosting (great for crypto data)
5. **LightGBM** - Fast gradient boosting
6. **Support Vector Regression** - Non-linear predictions
7. **Neural Network (MLP)** - Deep learning approach
8. **Ensemble Models** - Combines multiple models

## 📊 Features Created

The feature engineering creates 50+ features including:

- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Price Features**: Returns, volatility, price positions
- **Volume Features**: Volume ratios, On-Balance Volume
- **Time Features**: Hour, day of week, seasonal patterns
- **Market Features**: Correlations, market dominance

## 🎯 Prediction Targets

Models can predict:
- **Price** (next day, 3-day, 7-day)
- **Returns** (percentage changes)
- **Direction** (up/down classification)
- **Volatility** (risk measures)

## 📋 Evaluation Metrics

Models are evaluated using:
- **RMSE** - Root Mean Squared Error
- **MAE** - Mean Absolute Error  
- **R²** - Coefficient of determination
- **Directional Accuracy** - Trend prediction accuracy
- **Sharpe Ratio** - Risk-adjusted returns
- **Maximum Drawdown** - Worst-case losses

## 🔄 Typical Workflow

1. **Explore Data** → Use notebooks in `01-exploratory-analysis/`
2. **Prepare Features** → Run `02-data-preprocessing/` modules
3. **Train Models** → Use `03-model-training/` components
4. **Evaluate Performance** → Analyze with `06-model-evaluation/`
5. **Save Best Models** → Store using `04-model-persistence/`
6. **Make Predictions** → Deploy with `05-prediction-pipeline/`

## ⚠️ Important Notes

- **Data Requirements**: Need at least 100 data points per cryptocurrency
- **Memory Usage**: Feature engineering can be memory-intensive
- **Training Time**: Some models (XGBoost, Neural Networks) take longer to train
- **Validation**: Always use time-based splits for cryptocurrency data
- **Performance**: Crypto markets are volatile - perfect predictions are impossible!

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the project root directory
cd CryptoSphere-Analytics-Platform
python -m pip install -r requirements.txt
```

### "Not enough data" errors
- Ensure you have at least 100 days of cryptocurrency data
- Check that your data loading is working correctly

### Memory errors during feature engineering
- Reduce the number of cryptocurrencies being processed
- Process one cryptocurrency at a time
- Increase available system memory

### Models not training
- Check that features don't have too many missing values
- Verify that target variables are properly defined
- Ensure data types are correct (numerical features)

This ML pipeline is designed to be comprehensive yet beginner-friendly. Start with the notebooks to understand the concepts, then move to the Python scripts for automated processing!