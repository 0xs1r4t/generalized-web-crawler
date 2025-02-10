from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.db.models.product import Product, CrawlHistory, URLCache
from app.db.schemas.product import ProductCreate, CrawlHistoryCreate
from sqlalchemy import select


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, product_data: ProductCreate) -> Product:
        now = datetime.now(timezone.utc)
        db_product = Product(
            **product_data.model_dump(), created_at=now, updated_at=now
        )
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    async def get_product_by_url(self, url: str):
        """Get product by URL"""
        query = select(Product).where(Product.url == url)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def get_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.db.query(Product).offset(skip).limit(limit).all()

    def update_product(self, product_id: int, product_data: dict) -> Optional[Product]:
        product = self.get_product(product_id)
        if product:
            for key, value in product_data.items():
                setattr(product, key, value)
            product.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(product)
        return product

    def log_crawl_attempt(self, crawl_data: CrawlHistoryCreate) -> CrawlHistory:
        history = CrawlHistory(
            **crawl_data.model_dump(), crawled_at=datetime.now(timezone.utc)
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_crawl_history(self, product_id: int) -> List[CrawlHistory]:
        return (
            self.db.query(CrawlHistory)
            .filter(CrawlHistory.product_id == product_id)
            .order_by(CrawlHistory.crawled_at.desc())
            .all()
        )

    async def rollback(self):
        """Rollback the current transaction"""
        await self.db.rollback()
