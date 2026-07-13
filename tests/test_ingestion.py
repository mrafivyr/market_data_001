from datetime import date
from unittest.mock import patch
import pandas as pd
from src.database import StockPrice
from src.ingestion import get_latest_stored_date, run_pipeline

def test_get_latest_stored_date_empty(db_session):
    """Verifies that an uninitialized database returns None for the max date."""
    assert get_latest_stored_date(db_session) is None

def test_get_latest_stored_date_with_data(db_session):
    """Verifies that the correct maximum date is extracted from existing records."""
    record1 = StockPrice(date=date(2026, 7, 1), ticker="AAPL", close=150.0)
    record2 = StockPrice(date=date(2026, 7, 10), ticker="AAPL", close=155.0)
    
    db_session.add(record1)
    db_session.add(record2)
    db_session.commit()
    
    assert get_latest_stored_date(db_session) == date(2026, 7, 10)

@patch("src.ingestion.yf.download")
@patch("src.ingestion.SessionLocal")
def test_pipeline_cold_start_inserts_data(mock_session_local, mock_yf_download, db_session):
    """Tests Day 1 execution path: database is empty, calls API, inserts matrices."""
    # 1. Bind our isolated test DB session fixture to the mock engine instantiation
    mock_session_local.return_value.__enter__.return_value = db_session

    # 2. Build a structural mock MultiIndex DataFrame matching yfinance output
    columns = pd.MultiIndex.from_product(
        [['Open', 'High', 'Low', 'Close', 'Volume'], ['AAPL']],
        names=['Price', 'Ticker']
    )
    mock_data = pd.DataFrame(
        [[180.0, 185.0, 179.0, 182.0, 5000000]], 
        index=pd.DatetimeIndex(['2026-07-10'], name="Date"), 
        columns=columns
    )
    mock_yf_download.return_value = mock_data

    # 3. Trigger the ingestion pipeline run execution pass
    run_pipeline()

    # 4. Verify data was split, parsed, and pushed safely to our DB records
    saved_records = db_session.query(StockPrice).all()
    assert len(saved_records) == 1
    assert saved_records[0].ticker == "AAPL"
    assert float(saved_records[0].close) == 182.0
    assert saved_records[0].date == date(2026, 7, 10)

@patch("src.ingestion.yf.download")
@patch("src.ingestion.SessionLocal")
def test_pipeline_delta_run_updates_overlapping_data(mock_session_local, mock_yf_download, db_session):
    """Tests Day 2 execution path: handles overlaps via matrix merge and updates records."""
    mock_session_local.return_value.__enter__.return_value = db_session
    
    # Pre-populate the DB with a single record for 2026-07-10
    existing_record = StockPrice(
        date=date(2026, 7, 10), ticker="AAPL", open=180.0, high=185.0, low=179.0, close=182.0, volume=5000000
    )
    db_session.add(existing_record)
    db_session.commit()

    # Create mock API data returning the SAME date but with an updated/corrected Close price
    columns = pd.MultiIndex.from_product(
        [['Open', 'High', 'Low', 'Close', 'Volume'], ['AAPL']],
        names=['Price', 'Ticker']
    )
    mock_data = pd.DataFrame(
        [[180.0, 185.0, 179.0, 195.0, 6000000]],  # Close altered to 195.0
        index=pd.DatetimeIndex(['2026-07-10'], name="Date"), 
        columns=columns
    )
    mock_yf_download.return_value = mock_data

    # Trigger the ingestion pass logic
    run_pipeline()

    # Verify that the total row count did not grow, but the record was updated safely
    all_records = db_session.query(StockPrice).all()
    assert len(all_records) == 1
    assert float(all_records[0].close) == 195.0  # Successfully updated
    assert all_records[0].volume == 6000000
