# 🚀 CryptoSphere Analytics Platform

## 📖 What is this project?

**CryptoSphere Analytics Platform** is a simple cryptocurrency data analysis project that helps you:

1. **Get crypto data** from CoinMarketCap API (free tier - 333 calls per day)
2. **Clean and process** the data to make it useful
3. **Analyze trends** and create insights about cryptocurrency markets  
4. **Predict prices** using machine learning models
5. **Visualize everything** in dashboards and reports

## 🎯 Why is this important?

- **Track Market Trends**: Understand how crypto markets move and behave
- **Make Informed Decisions**: Use data instead of emotions for crypto investments
- **Learn Data Science**: Practice real-world data engineering and machine learning
- **Portfolio Management**: Monitor and analyze your crypto holdings
- **Automate Analysis**: Set up automated reports and alerts

## 🔢 Project Scope & Limitations

### What we're working with:
- **Data Source**: CoinMarketCap API (free tier)
- **Cryptocurrencies**: Focus on **top 10 coins** (BTC, ETH, ADA, DOT, etc.)
- **Update Frequency**: Every 5 minutes (API rate limit friendly)
- **Historical Data**: Limited to what's available through free API

### Limitations:
- **API Calls**: 333 calls per day (free tier limit)
- **Real-time Data**: 5-minute delays due to rate limiting
- **Coin Coverage**: Only top 10 most popular cryptocurrencies
- **Historical Data**: Limited historical depth on free tier
- **No Trading**: This is for analysis only, not actual trading

## 📁 Complete Project Structure

```
📁 CryptoSphere-Analytics-Platform/
├── 📄 main.py                          # Main application entry point
├── 📄 README.md                        # This file
├── 📄 requirements.txt                 # Python dependencies
├── 📄 requirements-dev.txt             # Development dependencies
├── 
├── 📁 00-docs/                         # 📚 Documentation
│   ├── 📄 01-project_charter.md        # Project overview
│   ├── 📄 02-data_dictionary.md        # Data definitions
│   ├── 📄 03-api_documentation.md      # CoinMarketCap API docs
│   ├── 📄 04-architecture_diagram.md   # System design
│   └── � 05-deployment_guide.md       # How to deploy
├── 
├── 📁 02-notebooks/                    # 📓 Jupyter Notebooks (Analysis)
│   ├── 📄 01-data_acquisition.ipynb    # Step 1: Get data from API
│   ├── � 02-data_cleaning.ipynb       # Step 2: Clean the data
│   ├── 📄 03-eda_analysis.ipynb        # Step 3: Explore and analyze
│   ├── 📄 04-data_transformation.ipynb # Step 4: Create features
│   ├── 📄 API_DATA_RETRIEVAL_GUIDE.md  # How to use CoinMarketCap API
│   │
│   ├── 📁 src/                         # 🐍 Python Modules
│   │   ├── 📄 __init__.py
│   │   ├── 📄 01-api_client.py         # Connect to CoinMarketCap API
│   │   ├── 📄 02-data_cleaner.py       # Clean crypto data
│   │   ├── 📄 03-eda_utils.py          # Analysis helper functions
│   │   └── 📄 04-transformation.py     # Create technical indicators
│   │
│   └── 📁 utils/                       # 🔧 Utility Functions
│       ├── 📄 __init__.py
│       ├── 📄 01-config_loader.py      # Load configuration files
│       └── 📄 02-logger.py             # Logging system
├── 
├── 📁 03-sql-processing/               # 🗄️ Database Operations
│   ├── 📁 01-bronze_layer/             # Raw data storage
│   │   └── 📄 01-create_bronze_tables.sql
│   ├── 📁 02-silver_layer/             # Cleaned data storage
│   │   └── 📄 01-create_silver_tables.sql
│   └── 📁 03-gold_layer/               # Business-ready data
│       └── 📄 01-create_gold_data_marts.sql
├── 
├── 📁 04-ml-models/                    # 🤖 Machine Learning
│   ├── 📁 02-data-preprocessing/
│   │   └── 📁 src/
│   │       └── 📄 data_preprocessor.py  # Prepare data for ML
│   ├── 📁 03-model-training/
│   │   └── 📁 src/
│   │       └── 📄 model_trainer.py      # Train price prediction models
│   ├── 📁 04-model-persistence/
│   │   └── 📁 src/
│   │       └── 📄 model_registry.py     # Save and version models
│   └── 📁 05-prediction-pipeline/
│       └── 📁 src/
│           └── 📄 prediction_service.py # Make predictions
├── 
├── 📁 05-data-validation/              # ✅ Data Quality Checks
│   ├── 📁 01-schema_validation/
│   │   ├── 📄 data_quality_validator.py    # Check data quality
│   │   └── 📄 schema_evolution_tracker.py # Track API changes
├── 
├── 📁 06-data-visualization/           # 📊 Dashboards & Reports
│   └── 📁 src/
│       └── 📄 powerbi_integration.py   # Create Power BI dashboards
├── 
├── 📁 07-automation/                   # ⚙️ Automation & Scheduling
│   └── 📁 01-orchestration/
│       └── 📄 pipeline_orchestrator.py # Schedule and run everything
├── 
└── 📁 config/                          # ⚙️ Configuration Files
    ├── 📄 config_manager.py            # Manage all configurations
    └── 📄 main_config.yaml             # Main settings file
```

## 🔄 Data Flow Process

Here's exactly how data moves through our system:

### Step 1: Data Collection 📥
**File**: `02-notebooks/src/01-api_client.py`
- Connects to CoinMarketCap API
- Gets data for top 10 cryptocurrencies
- Saves raw data to bronze layer (database)

### Step 2: Data Cleaning 🧹
**File**: `02-notebooks/src/02-data_cleaner.py`
- Takes raw crypto data from bronze layer
- Removes bad/missing data
- Standardizes formats and currency values
- Saves clean data to silver layer

### Step 3: Data Analysis 🔍
**File**: `02-notebooks/src/03-eda_utils.py`
- Loads clean data from silver layer
- Calculates price changes, trends, correlations
- Creates summary statistics and insights
- Generates analysis reports

### Step 4: Feature Engineering 🛠️
**File**: `02-notebooks/src/04-transformation.py`
- Takes analyzed data
- Creates technical indicators (moving averages, RSI, etc.)
- Prepares features for machine learning
- Saves processed data to gold layer

### Step 5: Machine Learning 🤖
**Files**: `04-ml-models/src/` folder
- `data_preprocessor.py`: Prepares data for ML models
- `model_trainer.py`: Trains price prediction models
- `model_registry.py`: Saves and versions trained models
- `prediction_service.py`: Makes price predictions

### Step 6: Visualization 📊
**File**: `06-data-visualization/src/powerbi_integration.py`
- Connects to gold layer data
- Creates Power BI dashboards
- Updates charts and graphs automatically

### Step 7: Automation ⚙️
**File**: `07-automation/01-orchestration/pipeline_orchestrator.py`
- Runs all steps automatically
- Schedules data updates every 5 minutes
- Sends alerts if something breaks

## 🎮 How to Use Each Component

### For Jupyter Notebooks (Interactive Analysis):
- Use files in `02-notebooks/` folder
- Run `01-data_acquisition.ipynb` first to get data
- Then run other notebooks in order (02, 03, 04)

### For Python Scripts (Automated Processing):
- Use `.py` files in `02-notebooks/src/` folder
- Run them from command line or main.py
- These do the same work as notebooks but automatically

## 🚀 Quick Start Guide

### What you need:
- Python 3.8 or newer
- CoinMarketCap API key (free)
- 30 minutes of your time

### Step-by-step setup:

1. **Get the code**
   ```bash
   git clone https://github.com/Morobang/CryptoSphere-Analytics-Platform.git
   cd CryptoSphere-Analytics-Platform
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv crypto_env
   
   # Activate it (Windows)
   crypto_env\Scripts\activate
   
   # Activate it (Mac/Linux)  
   source crypto_env/bin/activate
   ```

3. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get your FREE CoinMarketCap API key**
   - Go to [CoinMarketCap API](https://coinmarketcap.com/api/)
   - Sign up for free account
   - Copy your API key
   - Add it to `config/main_config.yaml`

5. **Test it works**
   ```bash
   python main.py --test-connection
   ```

6. **Run your first analysis**
   ```bash
   # Option 1: Use Jupyter notebooks (recommended for learning)
   jupyter notebook 02-notebooks/01-data_acquisition.ipynb
   
   # Option 2: Run automated pipeline
   python main.py --run-pipeline
   ```

## 📊 Target Cryptocurrencies

We focus on the **top 10 cryptocurrencies** by market cap:

1. **Bitcoin (BTC)** - The original cryptocurrency
2. **Ethereum (ETH)** - Smart contract platform
3. **Cardano (ADA)** - Proof-of-stake blockchain
4. **Polkadot (DOT)** - Multi-chain protocol
5. **Binance Coin (BNB)** - Exchange token
6. **XRP (XRP)** - Digital payment protocol
7. **Solana (SOL)** - High-performance blockchain
8. **Dogecoin (DOGE)** - Meme cryptocurrency
9. **Polygon (MATIC)** - Ethereum scaling solution
10. **Avalanche (AVAX)** - Smart contracts platform

*Note: This list may change based on market conditions and can be updated in the config file.*

## � What Each Folder Does

### 📚 `00-docs/` - Documentation
- Contains guides and explanations
- **Start here** if you want to understand the project
- Includes API documentation and setup guides

### 📓 `02-notebooks/` - Interactive Analysis
- **Jupyter notebooks** for step-by-step data analysis
- **Perfect for learning** and experimenting
- Run these when you want to explore the data manually

### 🐍 `02-notebooks/src/` - Python Scripts  
- **Automated versions** of the notebook analyses
- Use these for **production/scheduled runs**
- Same functionality as notebooks, but runs automatically

### 🗄️ `03-sql-processing/` - Database Setup
- SQL scripts to create database tables
- **Bronze**: Raw API data storage
- **Silver**: Cleaned data storage  
- **Gold**: Analysis-ready data storage

### 🤖 `04-ml-models/` - Machine Learning
- Scripts for **price prediction models**
- Trains models to forecast crypto prices
- Saves trained models for later use

### ✅ `05-data-validation/` - Quality Checks
- Makes sure the data is **good quality**
- Detects **unusual price movements** or data errors
- Alerts you if something looks wrong

### 📊 `06-data-visualization/` - Dashboards
- Creates **Power BI dashboards** automatically
- **Beautiful charts and graphs** of crypto data
- Updates in real-time as new data comes in

### ⚙️ `07-automation/` - Scheduling
- **Runs everything automatically**
- Schedules data collection every 5 minutes
- Sends **alerts** if prices change significantly

### ⚙️ `config/` - Settings
- **Configuration files** for the entire project
- Set your **API keys** here
- Customize which cryptocurrencies to track

## ⚙️ Configuration

Edit `config/main_config.yaml` to customize the project:

```yaml
# Your CoinMarketCap API settings
coinmarketcap:
  api_key: "PUT-YOUR-API-KEY-HERE"
  rate_limit: 333  # Free tier limit (calls per day)
  
# Which cryptocurrencies to track  
cryptocurrencies:
  - "BTC"   # Bitcoin
  - "ETH"   # Ethereum  
  - "ADA"   # Cardano
  - "DOT"   # Polkadot
  - "BNB"   # Binance Coin
  - "XRP"   # XRP
  - "SOL"   # Solana
  - "DOGE"  # Dogecoin
  - "MATIC" # Polygon
  - "AVAX"  # Avalanche

# How often to get new data
schedule:
  update_frequency: 300  # seconds (5 minutes)
  
# Price change alerts  
alerts:
  price_threshold: 5  # Alert if price changes more than 5%
  email: "your-email@gmail.com"
```

## � Simple Usage Examples

### 1. Get Crypto Data (Basic)
```python
# File: 02-notebooks/src/01-api_client.py
from notebooks.src.api_client import CoinMarketCapClient

client = CoinMarketCapClient(api_key="your-key-here")
data = client.get_top_cryptocurrencies(limit=10)
print(f"Got data for {len(data)} cryptocurrencies!")
```

### 2. Clean the Data
```python  
# File: 02-notebooks/src/02-data_cleaner.py
from notebooks.src.data_cleaner import CryptoDataCleaner

cleaner = CryptoDataCleaner()
clean_data = cleaner.clean_data(raw_crypto_data)
print("Data is now clean and ready!")
```

### 3. Predict Bitcoin Price
```python
# File: 04-ml-models/src/model_trainer.py  
from ml_models.src.model_trainer import CryptoPredictionTrainer

trainer = CryptoPredictionTrainer()
model = trainer.train_model('BTC')
prediction = model.predict_next_price()
print(f"Bitcoin price prediction: ${prediction}")
```

### 4. Run Everything at Once
```bash
# Command line - runs the full pipeline
python main.py --run-all

# Or run step by step
python main.py --step data-collection
python main.py --step data-cleaning  
python main.py --step analysis
python main.py --step prediction
```

## � Common Issues & Solutions

### "API Key not working"
- Make sure you signed up at CoinMarketCap and got your free API key
- Check that you put the key in `config/main_config.yaml`
- Verify you haven't exceeded the 333 calls per day limit

### "No data showing up"
- Check your internet connection
- Make sure the CoinMarketCap API is working (visit their status page)
- Look at the log files for error messages

### "Jupyter notebooks won't start"
- Make sure you installed jupyter: `pip install jupyter`
- Try: `jupyter notebook --ip=127.0.0.1`
- Check that your virtual environment is activated

### "Models not training"
- You need at least 30 days of data before training models
- Check that the data cleaning step completed successfully
- Make sure you have enough disk space

## 🤝 Contributing

Want to help improve this project?

1. **Fork** this repository
2. **Create** a new branch for your feature
3. **Make** your changes
4. **Test** that everything still works
5. **Submit** a pull request

### Ideas for improvements:
- Add more cryptocurrencies
- Improve price prediction accuracy
- Create better visualizations
- Add more technical indicators
- Optimize API usage

## 📈 What You'll Get

After running this project, you'll have:

### 📊 **Real-time Crypto Dashboard**
- Live prices for top 10 cryptocurrencies
- Price change alerts (email notifications)
- Beautiful charts showing price trends
- Portfolio tracking (if you add your holdings)

### 🤖 **Price Prediction Models**
- AI models that predict future crypto prices
- Accuracy reports showing how good the predictions are
- Historical backtesting to validate the models
- Daily prediction updates

### 📋 **Automated Reports**
- Daily crypto market summary
- Weekly performance analysis  
- Monthly trend reports
- Data quality reports

### � **Learning Experience**
- Hands-on experience with APIs
- Real-world data science project
- Machine learning implementation
- Database design and management

## 🎯 Next Steps

Once you have this working:

1. **Customize**: Add your favorite cryptocurrencies
2. **Extend**: Add more data sources (Twitter sentiment, news, etc.)
3. **Improve**: Fine-tune the prediction models
4. **Share**: Show friends your crypto analysis skills
5. **Learn**: Use this as a portfolio project for job applications

## ⚠️ Disclaimer

**This project is for educational and analysis purposes only.**

- � **Not financial advice** - Don't make investment decisions based solely on this
- 🚫 **No trading integration** - This doesn't buy/sell cryptocurrencies
- 🚫 **No guarantees** - Crypto predictions are never 100% accurate
- ✅ **Learning tool** - Great for understanding data science and crypto markets
- ✅ **Portfolio project** - Perfect for showcasing your skills

## 📞 Support & Questions

### Need Help?
- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Open an issue with your idea
- ❓ **Questions**: Check the documentation in `00-docs/` folder
- 📧 **Contact**: Email questions to the repository owner

### Useful Resources
- [CoinMarketCap API Documentation](https://coinmarketcap.com/api/documentation/v1/)
- [Python for Data Science Tutorial](https://www.python.org/about/gettingstarted/)
- [Jupyter Notebook Basics](https://jupyter-notebook-beginner-guide.readthedocs.io/)

---

## � Final Notes

**CryptoSphere Analytics Platform** is designed to be:
- ✅ **Beginner-friendly** - Easy to understand and use
- ✅ **Educational** - Learn real data science skills  
- ✅ **Practical** - Work with real cryptocurrency data
- ✅ **Scalable** - Can be extended with more features
- ✅ **Professional** - Good enough for portfolio/resume

**Happy Crypto Analytics!** 🚀📈💰

*Remember: This is for learning and analysis only. Always do your own research before making any investment decisions.*