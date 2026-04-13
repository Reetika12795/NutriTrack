"""Pydantic schemas for product-related endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class BrandOut(BaseModel):
    brand_id: int
    brand_name: str
    parent_company: str | None = None

    class Config:
        from_attributes = True


class CategoryOut(BaseModel):
    category_id: int
    category_name: str
    level: int | None = None

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    product_id: int
    barcode: str
    product_name: str | None
    generic_name: str | None = None
    quantity: str | None = None
    packaging: str | None = None
    brand: BrandOut | None = None
    category: CategoryOut | None = None
    energy_kcal: float | None = None
    fat_g: float | None = None
    saturated_fat_g: float | None = None
    carbohydrates_g: float | None = None
    sugars_g: float | None = None
    fiber_g: float | None = None
    proteins_g: float | None = None
    salt_g: float | None = None
    nutriscore_grade: str | None = None
    nutriscore_score: int | None = None
    nova_group: int | None = None
    ecoscore_grade: str | None = None
    ingredients_text: str | None = None
    allergens: str | None = None
    image_url: str | None = None
    completeness_score: float | None = None

    class Config:
        from_attributes = True


class ProductSearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    products: list[ProductOut]


class ProductAlternative(BaseModel):
    product: ProductOut
    nutriscore_improvement: str | None = None
    nova_improvement: str | None = None
