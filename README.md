# Data Pipeline Project

A comprehensive, production-ready data pipeline framework built with modern data engineering best practices. This project provides a complete end-to-end solution for data acquisition, processing, validation, machine learning, and business intelligence.

## 🏗️ Architecture Overview

This project follows the **medallion architecture** pattern with bronze (raw), silver (cleaned), and gold (business-ready) data layers, combined with a comprehensive MLOps pipeline and automated orchestration.
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
- **Cryptocurrencies**: Focus on **top 10 coins** 
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
📁 data-pipeline-project/
├── 📁 00-docs/                    # Comprehensive documentation
├── 📁 01-data/                    # Data storage (medallion architecture)
│   ├── 📁 01-raw/                 # Bronze layer - raw data
│   ├── 📁 02-processed/           # Silver layer - cleaned data
│   ├── 📁 03-interim/             # Temporary processing data
│   └── 📁 04-external/            # External reference data
├── 📁 02-notebooks/               # Interactive development
├── 📁 03-sql-processing/          # Database operations
├── 📁 04-ml-models/               # Complete ML pipeline
├── 📁 05-data-validation/         # Data quality & governance
├── 📁 06-data-visualization/      # Power BI integration
├── 📁 07-automation/              # Orchestration & monitoring
└── 📁 config/                     # Configuration management
```

## ✨ Key Features

### 🔄 Complete Data Pipeline
- **Data Acquisition**: Multi-source data ingestion with API clients
- **Data Processing**: ETL/ELT with comprehensive transformation logic
- **Data Validation**: Automated quality checks and schema evolution tracking
- **Data Storage**: Medallion architecture with bronze, silver, gold layers

### 🤖 Advanced Machine Learning
- **Model Training**: Multi-algorithm support with hyperparameter optimization
- **Model Registry**: Version control and lifecycle management
- **Model Serving**: Production-ready prediction pipeline
- **MLOps**: Complete CI/CD for machine learning models

### 📊 Business Intelligence
- **Power BI Integration**: Automated dashboard creation and data refresh
- **Real-time Monitoring**: System and pipeline performance tracking
- **Automated Reporting**: Scheduled report generation and distribution

### 🚀 Production-Ready Features
- **Orchestration**: Advanced pipeline scheduling and dependency management
- **Monitoring**: Comprehensive logging, alerting, and performance tracking
- **Scalability**: Parallel processing and resource optimization
- **Security**: Authentication, authorization, and data governance

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd data-pipeline-project
   ```

2. **Create and activate virtual environment**
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   conda create -n data-pipeline python=3.9
   conda activate data-pipeline
   ```

3. **Install dependencies**
   ```bash
   # Production dependencies
   pip install -r requirements.txt
   
   # Development dependencies (optional)
   pip install -r requirements-dev.txt
   ```

4. **Initialize configuration**
   ```bash
   python main.py --init-config
   ```

5. **Run example pipeline**
   ```bash
   python main.py --run-example
   ```

## 📖 Documentation

### Core Components

#### 1. Data Processing (`02-notebooks/` & `03-sql-processing/`)
- **Data Acquisition**: Multi-source data ingestion
- **Data Cleaning**: Automated data quality improvement
- **EDA Analysis**: Comprehensive exploratory data analysis
- **Data Transformation**: Business logic and feature engineering

#### 2. Machine Learning (`04-ml-models/`)
- **Data Preprocessing**: Feature engineering and dataset preparation
- **Model Training**: Multi-algorithm training with cross-validation
- **Model Registry**: Version control and deployment tracking
- **Prediction Service**: Production-ready model serving

#### 3. Data Validation (`05-data-validation/`)
- **Quality Validation**: Comprehensive data quality assessment
- **Schema Evolution**: Track and manage schema changes over time
- **Governance**: Data lineage and metadata management

#### 4. Business Intelligence (`06-data-visualization/`)
- **Power BI Integration**: Automated dashboard creation
- **Report Templates**: Pre-built visualization templates
- **Automated Refresh**: Scheduled data updates

#### 5. Orchestration (`07-automation/`)
- **Pipeline Orchestration**: Advanced task scheduling and dependency management
- **Monitoring**: Real-time system and pipeline monitoring
- **Alerting**: Multi-channel notification system

### Configuration

The project uses YAML configuration files for easy customization:

```yaml
# config/main_config.yaml (example)
data_sources:
  api:
    base_url: "https://api.example.com"
    timeout: 30
  database:
    host: "localhost"
    port: 5432
    database: "analytics"

pipeline:
  batch_size: 10000
  max_workers: 4
  timeout: 3600

notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    recipients: ["team@company.com"]
```

## 🔧 Usage Examples

### Running Individual Components

#### Data Pipeline
```python
from src.data_pipeline import DataPipeline

# Initialize pipeline
pipeline = DataPipeline(config_path="config/pipeline_config.yaml")

# Run complete pipeline
results = pipeline.run_full_pipeline()

# Or run individual stages
raw_data = pipeline.extract_data()
clean_data = pipeline.clean_data(raw_data)
transformed_data = pipeline.transform_data(clean_data)
```

#### Machine Learning
```python
from ml_models.src.model_trainer import ModelTrainer

# Initialize trainer
trainer = ModelTrainer(config_path="config/ml_config.yaml")

# Train models
results = trainer.train_multiple_models(
    X_train, y_train, X_test, y_test,
    models=['random_forest', 'xgboost', 'lightgbm']
)

# Get best model
best_model = trainer.get_best_model()
```

#### Data Validation
```python
from data_validation.src.data_quality_validator import DataValidator

# Initialize validator
validator = DataValidator()

# Validate dataset
report = validator.validate_dataset(
    data=df,
    dataset_name="customer_data",
    schema_rules=schema_config
)

print(f"Quality Score: {report.overall_score}/100")
```

#### Orchestration
```python
from automation.src.pipeline_orchestrator import OrchestrationEngine

# Initialize engine
engine = OrchestrationEngine()

# Define pipeline
pipeline_config = PipelineConfig(
    name="daily_analytics",
    tasks=[...],
    schedule="0 2 * * *"  # Daily at 2 AM
)

# Register and run
engine.register_pipeline(pipeline_config)
execution_id = engine.trigger_pipeline("daily_analytics")
```

### Power BI Integration
```python
from data_visualization.src.powerbi_integration import PowerBIIntegrator

# Initialize Power BI integration
pbi = PowerBIIntegrator(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Create dataset
dataset = pbi.create_dataset_from_dataframe(
    df=sales_data,
    dataset_name="Sales Analytics",
    workspace_id=workspace_id
)

# Schedule refresh
pbi.schedule_dataset_refresh(
    dataset_id=dataset.id,
    schedule_config={
        "days": ["Monday", "Wednesday", "Friday"],
        "times": ["09:00", "17:00"]
    }
)
```

## 📁 Project Structure Detail

### Documentation (`00-docs/`)
- `01-project_charter.md`: Project overview and objectives
- `02-data_dictionary.md`: Data definitions and metadata
- `03-api_documentation.md`: API specifications and usage
- `04-architecture_diagram.md`: System architecture documentation
- `05-deployment_guide.md`: Production deployment instructions

### Data Layer (`01-data/`)
Following medallion architecture:
- **Bronze Layer** (`01-raw/`): Raw, unprocessed data
- **Silver Layer** (`02-processed/`): Cleaned and validated data
- **Gold Layer** (`03-interim/`): Business-ready, aggregated data
- **External** (`04-external/`): Reference and lookup data

### Notebooks (`02-notebooks/`)
Interactive development environment:
- `01-data_acquisition.ipynb`: Data extraction and ingestion
- `02-data_cleaning.ipynb`: Data quality improvement
- `03-eda_analysis.ipynb`: Exploratory data analysis
- `04-data_transformation.ipynb`: Feature engineering

### SQL Processing (`03-sql-processing/`)
Database operations organized by layer:
- `01-bronze_layer/`: Raw data table creation
- `02-silver_layer/`: Data cleaning and validation
- `03-gold_layer/`: Business logic and aggregations

### Machine Learning (`04-ml-models/`)
Complete MLOps pipeline:
- `02-data-preprocessing/`: Feature engineering
- `03-model-training/`: Multi-algorithm training
- `04-model-persistence/`: Model registry and versioning
- `05-prediction-pipeline/`: Production serving

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete pipeline testing
- **Performance Tests**: Load and performance testing

## 🔧 Development

### Code Quality

The project maintains high code quality standards:

```bash
# Code formatting
black .
isort .

# Linting
flake8 src/
mypy src/

# Security scanning
bandit -r src/
safety check
```

### Pre-commit Hooks

Install pre-commit hooks for automated quality checks:

```bash
pre-commit install
```

## 📊 Monitoring and Observability

### Built-in Monitoring
- **Pipeline Metrics**: Execution time, success rate, resource usage
- **Data Quality Metrics**: Completeness, validity, consistency scores
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Data freshness, processing volume

### Alerting
- **Email Notifications**: SMTP-based alerting
- **Webhook Integration**: Custom webhook endpoints
- **Slack Integration**: Real-time team notifications

### Dashboards
- **System Health Dashboard**: Overall system status
- **Pipeline Performance Dashboard**: Execution metrics
- **Data Quality Dashboard**: Quality trends and issues

## 🚀 Deployment

### Local Development
```bash
python main.py --mode development
```

### Production Deployment
```bash
# Docker deployment
docker-compose up -d

# Kubernetes deployment
kubectl apply -f k8s/

# Manual deployment
python main.py --mode production
```

### Environment Configuration
- **Development**: Local testing and development
- **Staging**: Pre-production testing
- **Production**: Live production environment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for changes
- Ensure all tests pass before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [User Guide](00-docs/user_guide.md)
- [API Reference](00-docs/api_reference.md)
- [Troubleshooting](00-docs/troubleshooting.md)

### Community
- **Issues**: Report bugs and request features
- **Discussions**: Community Q&A and discussions
- **Wiki**: Extended documentation and tutorials

### Professional Support
For enterprise support and custom development, contact [support@company.com](mailto:support@company.com).

## 🙏 Acknowledgments

- Built with modern data engineering best practices
- Inspired by industry-leading data platforms
- Community contributions and feedback

---

**Happy Data Engineering! 🚀**
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
