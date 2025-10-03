# 📊 Financial API Data Retrieval Guide

## 🎯 **Complete Beginner's Guide to APIs and Financial Data**

This guide explains **everything** from what an API is to how to retrieve thousands of financial records. Perfect for your first time working with APIs!

---

## 📋 **Table of Contents**
1. [What is an API? (Complete Beginner)](#what-is-an-api-complete-beginner)
2. [Understanding Financial Data](#understanding-financial-data)
3. [What is a Dataset?](#what-is-a-dataset)
4. [Basic Concepts](#basic-concepts)
5. [Getting 1 Record](#getting-1-record)
6. [Getting 5 Records](#getting-5-records)
7. [Getting Hundreds of Records](#getting-hundreds-of-records)
8. [Getting the WHOLE Dataset](#getting-the-whole-dataset)
9. [API Endpoints Reference](#api-endpoints-reference)
10. [Code Examples](#code-examples)
11. [Troubleshooting](#troubleshooting)

---

## 🤔 **What is an API? (Complete Beginner)**

### **Think of an API Like a Restaurant:**
- **You (your code)** = The customer
- **API** = The waiter
- **Database** = The kitchen
- **Request** = Your order
- **Response** = Your food

### **Real Example:**
```
YOU: "I want Apple's stock price"
API: "Let me get that from our database..."
API: "Here's Apple's data: Price=$175.43, Company=Apple Inc, Market Cap=$2.8T"
```

### **What Does API Stand For?**
**A**pplication **P**rogramming **I**nterface
- **Application** = Your Python code
- **Programming** = Using code to communicate
- **Interface** = The way to talk to their system

### **Why Use APIs Instead of Websites?**
| Website (Human Use) | API (Computer Use) |
|-------------------|-------------------|
| Pretty pages with colors/buttons | Pure data (JSON format) |
| Click buttons manually | Send automated requests |
| Copy/paste data by hand | Process thousands of records instantly |
| "Apple Inc stock is $175.43" | `{"symbol":"AAPL","price":175.43}` |

### **What is an Endpoint?**
An **endpoint** is like a specific menu item at the restaurant:

```
🏪 FINANCIAL DATA RESTAURANT MENU:
├── 📋 /profile        → "Company Information Plate"
├── 💰 /quote          → "Current Stock Price"  
├── 📈 /historical     → "Price History Buffet"
├── 📊 /income-statement → "Financial Report"
└── 🔍 /search         → "Find Companies"
```

**Example:** 
- Endpoint: `/profile` 
- What it gives you: Company information
- Like ordering: "I'll have the Company Information Plate for Apple please"

---

## 💼 **Understanding Financial Data**

### **What is Financial Data?**
Financial data is **information about companies and their money**. Think of it like a company's report card that shows:

### **Types of Financial Information:**

#### **1. Company Profile (Company's ID Card)**
```
🏢 APPLE INC.
📍 Address: 1 Apple Park Way, Cupertino, CA
👥 Employees: 164,000 people
💼 Business: Makes iPhones, computers, services
📊 Stock Symbol: AAPL (how it's traded on stock market)
💰 Stock Price: $175.43 (what 1 share costs right now)
🏆 Market Value: $2.8 Trillion (total company worth)
🏭 Industry: Technology
```

#### **2. Stock Quote (Price Right Now)**
```
📈 APPLE STOCK QUOTE
💰 Current Price: $175.43
⬆️ Change Today: +$2.15 (+1.24%)
📊 Volume: 45,123,456 shares traded today
🕐 Last Updated: 2025-10-03 16:00:00
```

#### **3. Historical Prices (Price Over Time)**
```
📅 APPLE PRICE HISTORY
2025-10-03: $175.43
2025-10-02: $173.28
2025-10-01: $171.56
2025-09-30: $169.84
... (hundreds of days)
```

#### **4. Financial Statements (Company's Report Card)**
```
💰 APPLE'S MONEY REPORT (Income Statement)
📅 Year: 2024
💵 Revenue (Money In): $394.3 Billion
💸 Expenses (Money Out): $267.2 Billion  
✅ Profit (Money Left): $127.1 Billion
📊 Earnings Per Share: $6.42
```

### **Real-World Examples:**

#### **Example 1: What Does "Company Profile" Mean?**
Imagine Apple as a person:
- **Name:** Apple Inc.
- **Address:** 1 Apple Park Way, Cupertino
- **Job:** Makes technology products
- **Salary:** $394 billion per year (revenue)
- **Bank Account:** $2.8 trillion (market cap)
- **ID Number:** AAPL (stock symbol)

#### **Example 2: What Does "1 Record" Mean?**
1 Record = 1 Piece of Information

```
📋 RECORD #1 (Apple's Profile):
{
  "symbol": "AAPL",
  "companyName": "Apple Inc.",
  "price": 175.43,
  "marketCap": 2800000000000,
  "employees": 164000,
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "website": "https://www.apple.com",
  "description": "Apple Inc. designs, manufactures, and markets smartphones..."
}
```

This is **1 record** containing **36+ fields** of information about Apple.

---

## 📦 **What is a Dataset?**

### **Simple Explanation:**
A **dataset** is like a big **Excel spreadsheet** full of information.

### **Real Example - Company Dataset:**
```
| Symbol | Company Name    | Price   | Market Cap | Sector     |
|--------|----------------|---------|------------|------------|
| AAPL   | Apple Inc.     | $175.43 | $2.8T      | Technology |
| MSFT   | Microsoft      | $415.26 | $3.1T      | Technology |
| GOOGL  | Google         | $138.45 | $1.7T      | Technology |
| AMZN   | Amazon         | $145.86 | $1.5T      | Consumer   |
| TSLA   | Tesla          | $248.50 | $789B      | Automotive |
```

**This dataset has:**
- **5 records** (5 companies)
- **5 columns** (5 pieces of info per company)
- **25 data points** total (5×5)

### **Different Types of Datasets:**

#### **1. Company Profiles Dataset**
```
📊 WHAT: Basic information about companies
📈 SIZE: 1 record per company
🎯 USE: "I want to know about Apple, Microsoft, Google"

Example:
- 1 company = 1 record
- 500 companies = 500 records
```

#### **2. Stock Price History Dataset**
```
📊 WHAT: Daily stock prices over time
📈 SIZE: 1 record per day per company
🎯 USE: "I want Apple's price for every day in 2024"

Example:
- Apple for 1 year = ~250 records (250 trading days)
- 5 companies for 1 year = ~1,250 records
```

#### **3. Financial Statements Dataset**
```
📊 WHAT: Company's financial reports by year
📈 SIZE: 1 record per year per company
🎯 USE: "I want Apple's profit for the last 10 years"

Example:
- Apple for 10 years = 10 records
- 100 companies for 10 years = 1,000 records
```

### **Dataset Size Examples:**

| What You Want | Records | Like Having |
|---------------|---------|-------------|
| 1 company profile | 1 | 1 business card |
| 10 company profiles | 10 | Phone book page |
| S&P 500 profiles | 500 | Entire phone book |
| Apple's 5-year prices | ~1,250 | Small novel |
| 50 companies' 5-year prices | ~62,500 | Encyclopedia |

---

## 🌐 **How This All Works Together**

### **The Complete Process:**
```
1. 🤔 YOU THINK: "I want to know Apple's stock price"

2. 💻 YOUR CODE: Makes a request to the API
   "GET https://api.com/quote?symbol=AAPL&apikey=YOUR_KEY"

3. 🌐 API: Receives your request
   "Someone wants Apple's quote data"

4. 🗄️ DATABASE: API queries its database
   "SELECT * FROM quotes WHERE symbol='AAPL'"

5. 📦 API: Sends back the data
   '{"symbol":"AAPL","price":175.43,"change":2.15}'

6. ✅ YOUR CODE: Receives the data
   You now have Apple's current stock price!
```

### **Real Code Example:**
```python
# What you write:
url = "https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey=YOUR_KEY"
data = requests.get(url).json()

# What you get back:
[{
  "symbol": "AAPL",
  "companyName": "Apple Inc.",
  "price": 175.43,
  "marketCap": 2800000000000,
  # ... 30+ more fields
}]
```

### **Understanding the Response:**
- **[ ]** = List (can contain multiple records)
- **{ }** = Dictionary (one record with key-value pairs)
- **"symbol": "AAPL"** = Key is "symbol", Value is "AAPL"
- **"price": 175.43** = Key is "price", Value is 175.43

---

## 🧠 **Basic Concepts (Now You Know What APIs Are!)**

### **What is a "Record"? (Simple Answer)**
A **record** is like **1 row in Excel** containing information about something:
- **1 company profile** = 1 row with Apple's info (name, price, market cap, etc.)
- **1 day's stock price** = 1 row with Apple's price on October 3rd
- **1 financial statement** = 1 row with Apple's 2024 profits

### **JSON Format (How APIs Send Data)**
APIs don't send pretty tables - they send **JSON** (JavaScript Object Notation):

**What you see in Excel:**
```
Company    | Price  | Market Cap
Apple Inc. | 175.43 | 2.8T
```

**What APIs send (JSON):**
```json
{
  "companyName": "Apple Inc.",
  "price": 175.43,
  "marketCap": 2800000000000
}
```

### **How API Calls Work:**
```
🔄 THE API PROCESS:
1 API Call → 1 Endpoint → 1 Specific Type of Data

Examples:
📞 Call /profile endpoint → Get company info
📞 Call /quote endpoint → Get current stock price  
📞 Call /historical endpoint → Get price history
```

### **Why Different Endpoints Give Different Amounts of Data:**
```
🏢 Company Profile endpoint:
   ├── 1 company = 1 record
   └── 5 companies = 5 API calls = 5 records

📈 Stock Quote endpoint:
   ├── 1 company = 1 record (today's price)
   └── Same as profile - just different info

📊 Historical Prices endpoint:
   ├── 1 company = MANY records (1 per day)
   └── Apple for 1 year = ~250 records (250 trading days)

💰 Financial Statements endpoint:
   ├── 1 company = MANY records (1 per year)
   └── Apple for 10 years = 10 records
```

### **Your API Key = Your Restaurant Membership Card**
- **Free API Key:** Can access basic menu items (stable endpoints)
- **Paid API Key:** Can access premium menu items (all endpoints + more data)
- **No API Key:** Can't order anything

### **Rate Limits = Restaurant's "No Rushing" Policy**
- **Why they exist:** So their servers don't get overwhelmed
- **What it means:** You can only make X requests per minute
- **Solution:** Add small delays between requests (`time.sleep(0.2)`)

### **Key Understanding for Beginners:**
```
🎯 REMEMBER:
- 1 API call = Ask for 1 specific type of data
- 1 endpoint = 1 type of information (profile, price, history)
- 1 record = 1 row of data (1 company, 1 day, 1 year)
- More records = More companies OR more time periods OR more data types
```

---

## 🔢 **Getting 1 Record**

### **What This Means:**
Get information about **1 company** (like Apple)

### **How To Do It:**
```python
# Example: Get Apple's company profile
symbol = "AAPL"
url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"

# This returns: 1 record with Apple's info
```

### **What You Get:**
- 1 record with ~36 fields
- Company name, price, market cap, sector, etc.
- **Result:** `[{symbol: "AAPL", companyName: "Apple Inc", price: 258.68, ...}]`

---

## 📈 **Getting 5 Records**

### **What This Means:**
Get information about **5 companies** (Apple, Microsoft, Google, Amazon, Tesla)

### **Method 1: Loop Through Multiple Symbols**
```python
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
all_data = []

for symbol in symbols:
    url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"
    data = fetch_data(url)  # Your function to get data
    all_data.extend(data)   # Add to list

# Result: 5 records (1 per company)
```

### **Method 2: Use Time-Series Data**
```python
# Get 5 years of Apple's financial statements
url = f"https://financialmodelingprep.com/api/v3/income-statement/AAPL?limit=5&apikey={API_KEY}"

# Result: 5 records (1 per year for Apple)
```

---

## 📊 **Getting Hundreds of Records**

### **Method 1: Historical Price Data**
```python
# Get 1 year of daily prices for Apple (≈365 records)
start_date = "2023-01-01"
end_date = "2023-12-31"
url = f"https://financialmodelingprep.com/api/v3/historical-price-full/AAPL?from={start_date}&to={end_date}&apikey={API_KEY}"

# Result: ~365 records (1 per trading day)
```

### **Method 2: Multiple Companies + Multiple Years**
```python
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # 5 companies
years = 10  # 10 years of data

total_records = 0
for symbol in symbols:
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?limit={years}&apikey={API_KEY}"
    data = fetch_data(url)
    total_records += len(data)

# Result: 5 companies × 10 years = 50 financial statement records
```

### **Method 3: Multiple Data Types**
```python
symbols = ['AAPL', 'MSFT', 'GOOGL']
data_types = ['profile', 'quote', 'income-statement', 'balance-sheet']

# This gives you: 3 companies × 4 data types = 12+ records
```

---

## 🌍 **Getting the WHOLE Dataset**

### **Strategy 1: All S&P 500 Companies**
```python
# Step 1: Get list of all S&P 500 symbols (500 companies)
sp500_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', ...]  # 500 symbols

# Step 2: Get profiles for all companies
all_profiles = []
for symbol in sp500_symbols:
    url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"
    data = fetch_data(url)
    all_profiles.extend(data)

# Result: 500 company profile records
```

### **Strategy 2: Historical Data for Multiple Companies**
```python
# Get 5 years of daily prices for top 50 companies
top_50_symbols = ['AAPL', 'MSFT', 'GOOGL', ...]  # 50 companies
start_date = "2019-01-01"
end_date = "2024-01-01"

all_historical_data = []
for symbol in top_50_symbols:
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date}&to={end_date}&apikey={API_KEY}"
    data = fetch_data(url)
    if data and 'historical' in data:
        all_historical_data.extend(data['historical'])

# Result: 50 companies × ~1,250 trading days = ~62,500 records
```

### **Strategy 3: Complete Financial Database**
```python
# Build complete database
companies = get_sp500_list()  # 500 companies
data_types = [
    'profile',           # Company info
    'income-statement',  # Revenue, profits (10 years each)
    'balance-sheet',     # Assets, liabilities (10 years each)  
    'cash-flow',        # Cash movements (10 years each)
    'ratios',           # Financial ratios (10 years each)
]

total_records = 0
for company in companies:
    for data_type in data_types:
        # Get 10 years of each data type
        url = f"https://financialmodelingprep.com/api/v3/{data_type}/{company}?limit=10&apikey={API_KEY}"
        data = fetch_data(url)
        total_records += len(data) if data else 0

# Result: 500 companies × 5 data types × 10 years = 25,000+ records
```

---

## 🔗 **API Endpoints Reference**

### **Company Information**
| Endpoint | Records Returned | Example |
|----------|------------------|---------|
| `/profile` | 1 per company | Company details |
| `/quote` | 1 per company | Current stock price |

### **Financial Statements** 
| Endpoint | Records Returned | Example |
|----------|------------------|---------|
| `/income-statement` | 1 per year | Revenue, profit by year |
| `/balance-sheet` | 1 per year | Assets, liabilities by year |
| `/cash-flow-statement` | 1 per year | Cash flows by year |

### **Price Data**
| Endpoint | Records Returned | Example |
|----------|------------------|---------|
| `/historical-price-full` | 1 per day | Daily stock prices |
| `/historical-chart/1min` | 1 per minute | Minute-by-minute prices |

### **Market Data**
| Endpoint | Records Returned | Example |
|----------|------------------|---------|
| `/stock-screener` | 100s-1000s | Filter stocks by criteria |
| `/etf-stock-exposure` | Many | ETF holdings |

---

## 💻 **Code Examples**

### **Example 1: Single Company Profile**
```python
def get_single_company(symbol):
    url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"
    data = get_jsonparsed_data_urllib(url)
    return data  # Returns 1 record

# Usage
apple_data = get_single_company("AAPL")
print(f"Got {len(apple_data)} record(s)")  # Output: Got 1 record(s)
```

### **Example 2: Multiple Companies**
```python
def get_multiple_companies(symbols):
    all_data = []
    for symbol in symbols:
        url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"
        data = get_jsonparsed_data_urllib(url)
        if data:
            all_data.extend(data)
        time.sleep(0.2)  # Rate limiting
    return all_data

# Usage
tech_giants = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
all_companies = get_multiple_companies(tech_giants)
print(f"Got {len(all_companies)} record(s)")  # Output: Got 5 record(s)
```

### **Example 3: Historical Data (Many Records)**
```python
def get_historical_data(symbol, days=365):
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&apikey={API_KEY}"
    
    data = get_jsonparsed_data_requests(url)
    if data and 'historical' in data:
        return data['historical']
    return []

# Usage
apple_prices = get_historical_data("AAPL", days=365)
print(f"Got {len(apple_prices)} record(s)")  # Output: Got ~250 record(s)
```

### **Example 4: Large Dataset Builder**
```python
def build_large_dataset():
    # Define what you want
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'CRM', 'ADBE']
    data_types = {
        'profiles': 'profile',
        'quotes': 'quote', 
        'financials': 'income-statement'
    }
    
    dataset = {}
    total_records = 0
    
    for data_name, endpoint in data_types.items():
        print(f"Fetching {data_name}...")
        dataset[data_name] = []
        
        for symbol in symbols:
            if endpoint == 'income-statement':
                url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{symbol}?limit=5&apikey={API_KEY}"
            else:
                url = f"https://financialmodelingprep.com/stable/{endpoint}?symbol={symbol}&apikey={API_KEY}"
            
            data = get_jsonparsed_data_urllib(url)
            if data:
                dataset[data_name].extend(data)
                total_records += len(data)
            
            time.sleep(0.3)  # Rate limiting
    
    print(f"Dataset built! Total records: {total_records}")
    return dataset

# Usage
big_dataset = build_large_dataset()
# Output: Dataset built! Total records: 70+ (10 companies × 7 data points each)
```

---

## 🚨 **Troubleshooting**

### **Common Issues & Solutions**

#### **❌ Getting 403 Forbidden Errors**
**Problem:** API v3 endpoints return 403 errors
**Solution:** Use the stable endpoint instead
```python
# ❌ This gives 403 error:
url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={API_KEY}"

# ✅ This works:
url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"
```

#### **❌ Getting Empty Results**
**Problem:** API returns empty list `[]`
**Solutions:**
1. Check symbol spelling: `AAPL` not `Apple`
2. Use correct endpoint for your API tier
3. Check API key validity
4. Verify rate limits aren't exceeded

#### **❌ API Rate Limits**
**Problem:** Too many requests too fast
**Solution:** Add delays between requests
```python
import time
for symbol in symbols:
    # ... make API call ...
    time.sleep(0.2)  # Wait 200ms between calls
```

#### **❌ SSL Certificate Errors**
**Problem:** SSL verification fails
**Solution:** Use the urllib method with SSL context (already implemented in notebook)

---

## 📊 **Data Scale Examples**

| What You Want | Records | API Calls | Time |
|---------------|---------|-----------|------|
| 1 Company Profile | 1 | 1 | <1 sec |
| 5 Company Profiles | 5 | 5 | ~2 secs |
| 10 Companies × 5 Years Financials | 50 | 10 | ~5 secs |
| 100 Companies Profiles | 100 | 100 | ~30 secs |
| S&P 500 All Profiles | 500 | 500 | ~3 mins |
| 50 Companies × 1 Year Daily Prices | ~12,500 | 50 | ~15 secs |
| Complete S&P 500 Database | 25,000+ | 2,500+ | ~20 mins |

---

## 🎯 **Quick Start Recipes**

### **Recipe 1: "I want basic info on 10 tech companies"**
```python
tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'CRM', 'ADBE']
companies_data = fetch_multiple_symbols(tech_symbols, API_KEY)
# Result: 10 records
```

### **Recipe 2: "I want 5 years of Apple's financial history"**
```python
apple_financials = []
endpoints = ['income-statement', 'balance-sheet', 'cash-flow-statement']
for endpoint in endpoints:
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/AAPL?limit=5&apikey={API_KEY}"
    data = get_jsonparsed_data_requests(url)
    apple_financials.extend(data)
# Result: 15 records (3 statement types × 5 years)
```

### **Recipe 3: "I want to build a stock screener database"**
```python
# Get top 100 companies by market cap
symbols = get_sp500_symbols()[:100]  # Top 100
dataset = []

for symbol in symbols:
    # Get profile + latest financials
    profile_url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={API_KEY}"
    financial_url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?limit=1&apikey={API_KEY}"
    
    profile_data = get_jsonparsed_data_urllib(profile_url)
    financial_data = get_jsonparsed_data_requests(financial_url)
    
    # Combine data
    if profile_data and financial_data:
        combined = {**profile_data[0], **financial_data[0]}
        dataset.append(combined)
    
    time.sleep(0.3)

# Result: 100 records with comprehensive company data
```

---

## 🎉 **Summary**

### **Key Takeaways:**
1. **1 API call** = **1 endpoint** = **specific amount of data**
2. **More records** = **More symbols** OR **Time-series data** OR **Multiple endpoints**
3. **Use stable endpoint** to avoid 403 errors
4. **Add delays** to respect rate limits  
5. **Combine strategies** for large datasets

### **Data Growth Pattern:**
```
1 Company Profile → 1 record
5 Companies → 5 records  
5 Companies × 10 Years Financials → 50 records
5 Companies × 1 Year Daily Prices → ~1,250 records
S&P 500 Complete Database → 25,000+ records
```

**Now you understand exactly how to scale from 1 record to the entire financial universe! 🚀**