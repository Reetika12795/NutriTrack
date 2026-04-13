"""Tests for Meal Pydantic schemas -- validates request/response models."""

from __future__ import annotations

from datetime import date

from api.schemas.meal import (
    DailyNutritionSummary,
    MealCreate,
    MealItemCreate,
    MealItemOut,
    MealOut,
    WeeklyTrend,
)


class TestMealItemCreate:
    def test_valid_meal_item(self):
        item = MealItemCreate(product_id=1, quantity_g=150.0)
        assert item.product_id == 1
        assert item.quantity_g == 150.0

    def test_default_quantity(self):
        item = MealItemCreate(product_id=1)
        assert item.quantity_g == 100.0


class TestMealCreate:
    def test_valid_meal(self):
        meal = MealCreate(
            meal_type="lunch",
            items=[MealItemCreate(product_id=1)],
        )
        assert meal.meal_type == "lunch"
        assert len(meal.items) == 1

    def test_meal_with_date(self):
        meal = MealCreate(
            meal_type="breakfast",
            meal_date=date(2026, 4, 1),
            notes="Quick morning meal",
            items=[MealItemCreate(product_id=1), MealItemCreate(product_id=2, quantity_g=50.0)],
        )
        assert meal.meal_date == date(2026, 4, 1)
        assert meal.notes == "Quick morning meal"
        assert len(meal.items) == 2

    def test_meal_optional_fields(self):
        meal = MealCreate(meal_type="snack", items=[])
        assert meal.meal_date is None
        assert meal.notes is None


class TestMealItemOut:
    def test_valid_output(self):
        item = MealItemOut(
            meal_item_id=1,
            product_id=10,
            quantity_g=200.0,
            energy_kcal=300.0,
            proteins_g=15.0,
        )
        assert item.meal_item_id == 1
        assert item.energy_kcal == 300.0

    def test_optional_nutrition_fields(self):
        item = MealItemOut(meal_item_id=1, product_id=1, quantity_g=100.0)
        assert item.energy_kcal is None
        assert item.fat_g is None
        assert item.product is None


class TestMealOut:
    def test_valid_meal_output(self):
        meal = MealOut(
            meal_id=1,
            meal_type="dinner",
            meal_date=date(2026, 4, 1),
        )
        assert meal.meal_id == 1
        assert meal.meal_type == "dinner"
        assert meal.items == []

    def test_meal_with_items(self):
        meal = MealOut(
            meal_id=1,
            meal_type="lunch",
            meal_date=date(2026, 4, 1),
            items=[
                MealItemOut(meal_item_id=1, product_id=1, quantity_g=100.0),
                MealItemOut(meal_item_id=2, product_id=2, quantity_g=200.0),
            ],
        )
        assert len(meal.items) == 2


class TestDailyNutritionSummary:
    def test_valid_summary(self):
        summary = DailyNutritionSummary(
            date=date(2026, 4, 1),
            total_kcal=2000.0,
            total_fat_g=65.0,
            total_carbohydrates_g=250.0,
            total_sugars_g=50.0,
            total_proteins_g=80.0,
            total_fiber_g=25.0,
            total_salt_g=5.0,
            protein_pct=16.0,
            carbs_pct=50.0,
            fat_pct=29.25,
            meals_count=3,
            items_count=8,
        )
        assert summary.total_kcal == 2000.0
        assert summary.meals_count == 3
        assert summary.avg_nutriscore is None


class TestWeeklyTrend:
    def test_valid_trend(self):
        trend = WeeklyTrend(
            dates=[date(2026, 4, 1), date(2026, 4, 2)],
            daily_kcal=[2000.0, 1800.0],
            daily_proteins=[80.0, 75.0],
            daily_carbs=[250.0, 230.0],
            daily_fat=[65.0, 60.0],
            moving_avg_kcal=[None, 1900.0],
        )
        assert len(trend.dates) == 2
        assert trend.moving_avg_kcal[0] is None
        assert trend.moving_avg_kcal[1] == 1900.0
