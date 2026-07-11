from sqlalchemy import create_engine, Column, String, Date, Numeric, BigInteger
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 1. Define Base as a real, static class instead of a runtime variable
class Base(DeclarativeBase):
    pass

class StockPrice(Base):
    __tablename__ = "stock_prices"

    # Compound Primary Key: Prevents duplicate records for the same ticker on the same day
    date = Column(Date, primary_key=True, index=True)
    symbol = Column(String(10), primary_key=True, index=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    volume = Column(BigInteger)

def init_db():
    Base.metadata.create_all(bind=engine)
