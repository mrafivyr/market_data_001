from datetime import datetime, timedelta, date
import yfinance as yf
import pandas as pd
from sqlalchemy import func
from src.config import WATCHLIST
from src.database import SessionLocal, StockPrice, init_db


def get_latest_stored_date(session) -> date | None:
    """Finds the newest date using a database-independent ORM query."""
    return session.query(func.max(StockPrice.date)).scalar()

def run_pipeline():
    init_db()  # Verifies tables exist independently of database type
    
    # Open an explicit, safe ORM session transaction context manager
    with SessionLocal() as session:
        today = datetime.now().date()
        latest_date = get_latest_stored_date(session)

        # 1. DYNAMIC API EXTRACTION WINDOWING
        if latest_date is None:
            print("📦 Cold start! Extracting 1 year of historical market data...")
            try:
                df = yf.download(WATCHLIST, period="1y", interval="1d")
            except Exception as e:
                print(f"❌ Error contacting yfinance API: {e}")
                return
        else:
            start_date = latest_date + timedelta(days=1)
            if start_date > today:
                print(f"✅ Data warehouse is fully up-to-date up to {latest_date}. Aborting.")
                return
                
            print(f"⚡ Delta run! Extracting rows starting from: {start_date}")
            try:
                df = yf.download(WATCHLIST, start=start_date, interval="1d")
            except Exception as e:
                print(f"❌ Error contacting yfinance API: {e}")
                return

        if df.empty:
            print("📭 No new trading records surfaced from the API.")
            return

        # 2. PANDAS TRANSFORMATION LAYER
        df = df.stack(level=1).reset_index()
        df.columns = [col.lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.dropna(subset=['date', 'ticker', 'close'])

        # 3. VECTORIZED MATRIX SPLITTING VIA MERGE
        print("🔍 Fetching existing records from DB to check for overlaps...")
        min_date = df['date'].min()
        existing_records = (
            session.query(StockPrice.date, StockPrice.ticker)
            .filter(StockPrice.date >= min_date)
            .all()
        )
        
        # Convert existing DB composite keys into a clean lookup DataFrame
        existing_df = pd.DataFrame(existing_records, columns=['date', 'ticker'])
        existing_df['is_existing'] = True

        # Left-join the fresh API data with our existing DB flags in optimized C-code
        merged_df = pd.merge(df, existing_df, on=['date', 'ticker'], how='left')
        merged_df['is_existing'] = merged_df['is_existing'].fillna(False)

        # Slice the combined matrix using boolean masks instead of python row loops
        insert_mask = merged_df['is_existing'] == False
        update_mask = merged_df['is_existing'] == True

        db_columns = ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        df_to_insert = merged_df.loc[insert_mask, db_columns]
        df_to_update = merged_df.loc[update_mask, db_columns]

        # Instantly export filtered matrices straight to dictionaries
        records_to_insert = df_to_insert.to_dict(orient="records")
        records_to_update = df_to_update.to_dict(orient="records")

        # 4. DATABASE-INDEPENDENT ORM UPSERT BATCHING
        try:
            if records_to_insert:
                print(f"➕ Bulk Inserting {len(records_to_insert)} fresh records...")
                session.bulk_insert_mappings(StockPrice, records_to_insert)

            if records_to_update:
                print(f"🔄 Bulk Updating {len(records_to_update)} overlapping records...")
                session.bulk_update_mappings(StockPrice, records_to_update)

            # Complete the transaction unit of work
            session.commit()
            print("🚀 Pipeline sync complete. Session changes successfully committed.")

        except Exception as e:
            session.rollback()  # Instantly rolls back the workspace if anything breaks
            print(f"❌ Transaction crashed! Rollback executed. Detail: {e}")

if __name__ == "__main__":
    run_pipeline()
