# Data Dictionary

<!-- 
This file should contain:

## Data Sources
- Primary data sources and their descriptions
- Data freshness and update frequency
- Data volume estimates
- Source system contacts

## Bronze Layer Tables
- Raw data table schemas
- Column descriptions and data types
- Primary keys and relationships
- Data quality rules

## Silver Layer Tables
- Cleaned and normalized table schemas
- Transformation rules applied
- Business logic implemented
- Data lineage documentation

## Gold Layer Tables
- Business-ready aggregated tables
- Calculated fields and metrics
- Dimension and fact table descriptions
- Usage guidelines for analysts

## Data Lineage
- Source to target mapping
- Transformation dependencies
- Impact analysis documentation

Example structure:
```
# Customer Data

## customers_bronze
| Column | Type | Description | Source |
|--------|------|-------------|---------|
| customer_id | VARCHAR(50) | Unique customer identifier | CRM System |
| first_name | VARCHAR(100) | Customer first name | CRM System |
| last_name | VARCHAR(100) | Customer last name | CRM System |
| email | VARCHAR(255) | Customer email address | CRM System |
| created_date | TIMESTAMP | Account creation date | CRM System |

## Business Rules
- Email addresses must be unique
- Customer names cannot be null
- Created date cannot be future date
```
-->