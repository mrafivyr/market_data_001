import os

# Connection configuration falling back to standard defaults
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/stocks_db"
)

# The portfolio tickers your daily script tracks
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
