from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_main_db
from app.db.repositories.product import ProductRepository
from app.db.schemas.product import Product, ProductCreate

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("/", response_model=Product)
async def create_product(product: ProductCreate, db: Session = Depends(get_main_db)):
    repo = ProductRepository(db)
    return repo.create_product(product)


@router.get("/", response_model=List[Product])
async def get_products(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_main_db)
):
    repo = ProductRepository(db)
    return repo.get_products(skip=skip, limit=limit)


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int, db: Session = Depends(get_main_db)):
    repo = ProductRepository(db)
    product = repo.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/history")
async def get_product_history(product_id: int, db: Session = Depends(get_main_db)):
    repo = ProductRepository(db)
    return repo.get_crawl_history(product_id)
