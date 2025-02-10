from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    domain = Column(String, index=True)

    # Core product details
    external_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    image_url = Column(String, nullable=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_active = Column(Boolean, default=True)

    # Relationship with crawl history
    crawl_history = relationship("CrawlHistory", back_populates="product")


class CrawlHistory(Base):
    __tablename__ = "crawl_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    crawled_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status_code = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)

    # Relationship with product
    product = relationship("Product", back_populates="crawl_history")


class URLCache(Base):
    __tablename__ = "url_cache"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    domain = Column(String, index=True)
    first_seen = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_accessed = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    access_count = Column(Integer, default=1)
    ttl = Column(Integer, default=86400)  # Time to live in seconds (24 hours)
