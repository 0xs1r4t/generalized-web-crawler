from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Generator
from app.config import settings
from app.db.models.product import Base  # Import Base from our models

# Main database for product data
main_engine = create_engine(
    settings.PRODUCT_DATABASE_URL,
    pool_pre_ping=True,  # Enables connection health checks
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Max number of connections to use beyond pool_size
)
MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)

# Cache database
cache_engine = create_engine(
    settings.CACHE_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,  # Smaller pool for cache database
    max_overflow=5,
)
CacheSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cache_engine)


def init_db() -> None:
    """Initialize database with all models"""
    Base.metadata.create_all(bind=main_engine)
    Base.metadata.create_all(bind=cache_engine)


def get_main_db() -> Generator[Session, None, None]:
    """Get database session for main database"""
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cache_db() -> Generator[Session, None, None]:
    """Get database session for cache database"""
    db = CacheSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine(cache: bool = False) -> Engine:
    """Get database engine"""
    return cache_engine if cache else main_engine
