"""SQLAlchemy models for products, brands, categories."""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


class Brand(Base):
    __tablename__ = "brands"
    __table_args__ = {"schema": "app"}

    brand_id = Column(Integer, primary_key=True)
    brand_name = Column(String(255), nullable=False)
    parent_company = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    products = relationship("Product", back_populates="brand")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "app"}

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(255), nullable=False)
    parent_category_id = Column(Integer, ForeignKey("app.categories.category_id"))
    level = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "app"}

    product_id = Column(Integer, primary_key=True)
    barcode = Column(String(20), unique=True, nullable=False)
    product_name = Column(String(500))
    generic_name = Column(String(500))
    quantity = Column(String(100))
    packaging = Column(String(255))
    brand_id = Column(Integer, ForeignKey("app.brands.brand_id"))
    category_id = Column(Integer, ForeignKey("app.categories.category_id"))

    energy_kcal = Column(Numeric(8, 2))
    energy_kj = Column(Numeric(8, 2))
    fat_g = Column(Numeric(8, 2))
    saturated_fat_g = Column(Numeric(8, 2))
    carbohydrates_g = Column(Numeric(8, 2))
    sugars_g = Column(Numeric(8, 2))
    fiber_g = Column(Numeric(8, 2))
    proteins_g = Column(Numeric(8, 2))
    salt_g = Column(Numeric(8, 4))
    sodium_g = Column(Numeric(8, 4))

    nutriscore_grade = Column(String(1))
    nutriscore_score = Column(Integer)
    nova_group = Column(Integer)
    ecoscore_grade = Column(String(1))

    countries = Column(String(500))
    ingredients_text = Column(Text)
    allergens = Column(Text)
    traces = Column(Text)
    image_url = Column(String(1000))
    off_url = Column(String(500))
    completeness_score = Column(Numeric(5, 2))
    data_source = Column(String(50))
    last_modified_off = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    brand = relationship("Brand", back_populates="products")
    category = relationship("Category", back_populates="products")
    meal_items = relationship("MealItem", back_populates="product")
