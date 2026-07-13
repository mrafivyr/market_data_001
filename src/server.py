from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal, StockPrice
import pandas as pd

app = FastAPI(title="Financial Analytics Engine")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/prices/{ticker}")
def get_stock_prices(ticker: str, db: Session = Depends(get_db)):
    """Fetches clean records directly from our localized warehouse."""
    records = db.query(StockPrice).filter(StockPrice.ticker == ticker.upper()).all()
    if not records:
        raise HTTPException(status_code=404, detail="Ticker not found in database.")
    
    return [
        {
            "date": r.date.isoformat(),
            "open": float(r.open),
            "high": float(r.high),
            "low": float(r.low),
            "close": float(r.close),
            "volume": r.volume
        } for r in records
    ]

@app.get("/analysis/{ticker}")
def get_analytics(ticker: str, window: int = 20, db: Session = Depends(get_db)):
    """Pulls raw records, loads into Pandas, and runs fast math on-the-fly."""
    records = db.query(StockPrice).filter(StockPrice.ticker == ticker.upper()).all()
    if not records:
        raise HTTPException(status_code=404, detail="Ticker analytics unavailable.")

    # Convert database data instantly into a Pandas DataFrame
    data = [{ "date": r.date, "close": float(r.close) } for r in records]
    df = pd.DataFrame(data).sort_values("date")

    # Fast Vectorized Pandas calculation
    df["moving_average"] = df["close"].rolling(window=window).mean()
    
    # Return calculated results cleanly to the frontend
    df["date"] = df["date"].apply(lambda x: x.isoformat())
    return df.dropna().to_dict(orient="records")
