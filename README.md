# Market Data Pipeline (Project-001)

A financial data ingestion and analytics system that downloads daily stock prices from Yahoo Finance, stores them in PostgreSQL, and serves data via a FastAPI REST API.

## Features

- **Automated Data Ingestion**: Downloads OHLCV data for configured tickers with smart delta detection
- **Efficient Upsert Logic**: Uses pandas merge operations to handle both inserts and updates in a single pass
- **REST API**: FastAPI endpoints for querying raw price data and calculating moving averages
- **Dockerized**: Multi-stage Docker build for testing, ingestion, and API serving
- **Test Coverage**: Comprehensive test suite with mocked API calls and in-memory database

## Tech Stack

- **Python 3.14+**
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM with database-agnostic operations
- **PostgreSQL** - Production database
- **SQLite** - Testing database
- **yfinance** - Yahoo Finance data source
- **pandas** - Data transformation and analysis
- **Docker** - Containerization with uv package manager

## Project Structure

```
market_data_001/
 src/
    config.py       # Configuration (watchlist, DB URL)
    database.py     # SQLAlchemy models and session
    ingestion.py    # ETL pipeline for data download
    server.py       # FastAPI application
 tests/
    conftest.py     # Test fixtures
    test_ingestion.py  # Pipeline tests
 Dockerfile          # Multi-stage container build
 pyproject.toml      # Project configuration
 uv.lock            # Dependency lock file
```

## Quick Start

### Using Docker

Build images with version tags:
```bash
docker build --target tester -t market-data-test:001 .
docker build --target server -t market-data-api:001 .
docker build --target ingestion -t market-data-ingestion:001 .
```

Run tests:
```bash
docker container run --name market_data_test -e PYTHONPATH=/app --network=market-data-network market-data-test:001
```

Start PostgreSQL database:
```bash
docker container run --name my-postgres -e POSTGRES_PASSWORD=******* -e POSTGRES_DB=stocks_db -v pgdata:/var/lib/postgresql -p 5432:5432 --network market-data-network -d postgres
```

Run ingestion service:
```bash
docker container run --name market-data-ingestion --network=market-data-network -e PYTHONPATH=/app -d market-data-ingestion:001
```

Run API server:
```bash
docker container run --name market-data-api -p 8000:8000 --network=market-data-network -e PYTHONPATH=/app -d market-data-api:001
```

### Local Development

Install dependencies:
```bash
uv sync
```

Run the API server:
```bash
uv run uvicorn src.server:app --reload
```

Run ingestion pipeline:
```bash
uv run python src/ingestion.py
```

Run tests:
```bash
uv run pytest
```

## Docker Network Setup

Create a Docker network for container communication:
```bash
docker network create market-data-network
```

## API Endpoints

### Health Check
```
GET /health
```
Returns server health status.

### Get Stock Prices
```
GET /prices/{ticker}
```
Returns all stored price records for a ticker.

**Response:**
```json
[
  {
    "date": "2026-07-10",
    "open": 180.0,
    "high": 185.0,
    "low": 179.0,
    "close": 182.0,
    "volume": 5000000
  }
]
```

### Get Analytics
```
GET /analysis/{ticker}?window={N}
```
Returns price data with calculated moving averages.

**Parameters:**
- `window`: Number of periods for moving average (default: 20)

**Response:**
```json
[
  {
    "date": "2026-07-10",
    "close": 182.0,
    "moving_average": 175.5
  }
]
```

## Configuration

Environment variables:
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/stocks_db`)

Edit `src/config.py` to modify the ticker watchlist:
```python
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
```

## Data Pipeline Logic

1. **Cold Start**: On first run, downloads 1 year of historical data
2. **Delta Updates**: Subsequent runs fetch only new data from the last stored date
3. **Deduplication**: Uses database composite key (date, ticker) to prevent duplicates
4. **Update Handling**: Detects and updates existing records when corrected data is available
5. **Transaction Safety**: All operations wrapped in transactions with automatic rollback on errors

## Testing

The test suite uses:
- In-memory SQLite database for isolation
- Mocked yfinance calls to avoid external dependencies
- Database fixtures that clean up after each test

Run with coverage:
```bash
uv run pytest -v
```
