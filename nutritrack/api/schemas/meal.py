"""Pydantic schemas for meal-related endpoints."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from api.schemas.product import ProductOut


class MealItemCreate(BaseModel):
    product_id: int
    quantity_g: float = 100.0


class MealCreate(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    meal_date: date | None = None
    notes: str | None = None
    items: list[MealItemCreate]


class MealItemOut(BaseModel):
    meal_item_id: int
    product_id: int
    quantity_g: float
    energy_kcal: float | None = None
    fat_g: float | None = None
    carbohydrates_g: float | None = None
    proteins_g: float | None = None
    fiber_g: float | None = None
    salt_g: float | None = None
    product: ProductOut | None = None

    class Config:
        from_attributes = True


class MealOut(BaseModel):
    meal_id: int
    meal_type: str
    meal_date: date
    notes: str | None = None
    items: list[MealItemOut] = []
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class DailyNutritionSummary(BaseModel):
    date: date
    total_kcal: float
    total_fat_g: float
    total_carbohydrates_g: float
    total_sugars_g: float
    total_proteins_g: float
    total_fiber_g: float
    total_salt_g: float
    protein_pct: float
    carbs_pct: float
    fat_pct: float
    meals_count: int
    items_count: int
    avg_nutriscore: float | None = None
    meals: list[MealOut] = []


class WeeklyTrend(BaseModel):
    dates: list[date]
    daily_kcal: list[float]
    daily_proteins: list[float]
    daily_carbs: list[float]
    daily_fat: list[float]
    moving_avg_kcal: list[float | None]
