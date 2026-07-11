import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Creates a fresh, database-independent in-memory SQLite database for testing."""
    # Using an in-memory SQLite URL ensures tests leave no residual cleanup files
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create the schema tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
