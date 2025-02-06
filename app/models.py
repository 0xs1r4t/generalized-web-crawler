from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, index=True)
    product_url = Column(String, unique=True, index=True)
    product_id = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    product_brand  = Column(String, nullable=True)
    product_price = Column(Integer, nullable=True)
    product_image_url = Column(String, nullable=True)



