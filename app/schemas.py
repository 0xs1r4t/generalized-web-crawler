from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    domain: str
    product_url: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    product_brand: Optional[str] = None
    product_price: Optional[int] = None
    product_image_url: Optional[str] = None

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True