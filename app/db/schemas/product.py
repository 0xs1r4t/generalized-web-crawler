from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Product schemas
class ProductBase(BaseModel):
    domain: str
    url: str
    external_id: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Crawl History schemas
class CrawlHistoryBase(BaseModel):
    status_code: int
    success: bool
    error_message: Optional[str] = None


class CrawlHistoryCreate(CrawlHistoryBase):
    product_id: int


class CrawlHistory(CrawlHistoryBase):
    id: int
    product_id: int
    crawled_at: datetime

    class Config:
        from_attributes = True


# URL Cache schemas
class URLCacheBase(BaseModel):
    url: str
    ttl: int = Field(default=86400, description="Time to live in seconds")


class URLCache(URLCacheBase):
    id: int
    first_seen: datetime
    last_accessed: datetime
    access_count: int

    class Config:
        from_attributes = True
