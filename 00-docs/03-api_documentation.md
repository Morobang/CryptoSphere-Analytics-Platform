# API Documentation

<!-- 
This file should contain:

## Overview
- API purpose and functionality
- Authentication methods
- Base URLs and environments
- Rate limiting policies

## Endpoints
- Detailed endpoint documentation
- Request/response formats
- HTTP methods and status codes
- Error handling

## Authentication
- API key management
- OAuth flows
- Token refresh procedures
- Security best practices

## Data Models
- Request/response schemas
- Data type definitions
- Validation rules
- Example payloads

## Usage Examples
- Common use cases
- Code samples in different languages
- Integration patterns
- Testing procedures

Example structure:
```
# Data Pipeline API

## Base URL
- Production: `https://api.datapipeline.com/v1`
- Staging: `https://staging-api.datapipeline.com/v1`

## Authentication
All requests require an API key in the header:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### GET /pipeline/status
Returns the current status of all data pipelines.

**Response:**
```json
{
  "pipelines": [
    {
      "id": "customer-etl",
      "status": "running",
      "last_run": "2025-10-03T10:30:00Z",
      "next_run": "2025-10-03T11:00:00Z"
    }
  ]
}
```

### POST /pipeline/{pipeline_id}/trigger
Manually triggers a pipeline execution.

**Parameters:**
- `pipeline_id` (string): Unique pipeline identifier

**Request Body:**
```json
{
  "force": false,
  "parameters": {
    "start_date": "2025-10-01",
    "end_date": "2025-10-03"
  }
}
```
```
-->