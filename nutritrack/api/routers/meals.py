"""Meal tracking endpoints (C12 - REST API)."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth.jwt import get_current_user
from api.database import get_db
from api.models.product import Product
from api.models.user import Meal, MealItem, User
from api.schemas.meal import DailyNutritionSummary, MealCreate, MealOut, WeeklyTrend

router = APIRouter(prefix="/api/v1/meals", tags=["Meals"])


@router.post("/", response_model=MealOut, status_code=201)
async def create_meal(
    meal_data: MealCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a new meal with food items."""
    meal = Meal(
        user_id=current_user.user_id,
        meal_type=meal_data.meal_type,
        meal_date=meal_data.meal_date or date.today(),
        notes=meal_data.notes,
    )
    db.add(meal)
    await db.flush()

    for item_data in meal_data.items:
        # Verify product exists
        result = await db.execute(
            select(Product).where(Product.product_id == item_data.product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")

        # Compute nutrition for quantity
        ratio = float(item_data.quantity_g) / 100.0
        meal_item = MealItem(
            meal_id=meal.meal_id,
            product_id=item_data.product_id,
            quantity_g=item_data.quantity_g,
            energy_kcal=float(product.energy_kcal) * ratio if product.energy_kcal else None,
            fat_g=float(product.fat_g) * ratio if product.fat_g else None,
            carbohydrates_g=float(product.carbohydrates_g) * ratio if product.carbohydrates_g else None,
            proteins_g=float(product.proteins_g) * ratio if product.proteins_g else None,
            fiber_g=float(product.fiber_g) * ratio if product.fiber_g else None,
            salt_g=float(product.salt_g) * ratio if product.salt_g else None,
        )
        db.add(meal_item)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.items).selectinload(MealItem.product).selectinload(Product.brand),
            selectinload(Meal.items).selectinload(MealItem.product).selectinload(Product.category))
        .where(Meal.meal_id == meal.meal_id)
    )
    return result.scalar_one()


@router.get("/", response_model=list[MealOut])
async def list_meals(
    meal_date: date | None = Query(None),
    meal_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's meals with optional filters."""
    query = (
        select(Meal)
        .options(selectinload(Meal.items).selectinload(MealItem.product).selectinload(Product.brand),
            selectinload(Meal.items).selectinload(MealItem.product).selectinload(Product.category))
        .where(Meal.user_id == current_user.user_id)
    )

    if meal_date:
        query = query.where(Meal.meal_date == meal_date)
    if meal_type:
        query = query.where(Meal.meal_type == meal_type)

    query = query.order_by(Meal.meal_date.desc(), Meal.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/daily-summary", response_model=DailyNutritionSummary)
async def get_daily_nutrition(
    target_date: date = Query(default=None, description="Date to summarize (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get daily nutrition summary for the current user."""
    target = target_date or date.today()

    # Get meals for the day
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.items).selectinload(MealItem.product).selectinload(Product.brand),
            selectinload(Meal.items).selectinload(MealItem.product).selectinload(Product.category))
        .where(Meal.user_id == current_user.user_id, Meal.meal_date == target)
        .order_by(Meal.meal_type)
    )
    meals = result.scalars().all()

    # Aggregate nutrition
    total_kcal = 0.0
    total_fat = 0.0
    total_carbs = 0.0
    total_sugars = 0.0
    total_proteins = 0.0
    total_fiber = 0.0
    total_salt = 0.0
    items_count = 0
    nutriscore_scores = []

    for meal in meals:
        for item in meal.items:
            items_count += 1
            if item.energy_kcal:
                total_kcal += float(item.energy_kcal)
            if item.fat_g:
                total_fat += float(item.fat_g)
            if item.carbohydrates_g:
                total_carbs += float(item.carbohydrates_g)
            if item.proteins_g:
                total_proteins += float(item.proteins_g)
            if item.fiber_g:
                total_fiber += float(item.fiber_g)
            if item.salt_g:
                total_salt += float(item.salt_g)
            if item.product and item.product.nutriscore_score is not None:
                nutriscore_scores.append(item.product.nutriscore_score)

    # Compute macro percentages
    total_macro_kcal = (total_proteins * 4) + (total_carbs * 4) + (total_fat * 9)
    protein_pct = round((total_proteins * 4 / total_macro_kcal * 100) if total_macro_kcal > 0 else 0, 1)
    carbs_pct = round((total_carbs * 4 / total_macro_kcal * 100) if total_macro_kcal > 0 else 0, 1)
    fat_pct = round((total_fat * 9 / total_macro_kcal * 100) if total_macro_kcal > 0 else 0, 1)

    return DailyNutritionSummary(
        date=target,
        total_kcal=round(total_kcal, 1),
        total_fat_g=round(total_fat, 1),
        total_carbohydrates_g=round(total_carbs, 1),
        total_sugars_g=round(total_sugars, 1),
        total_proteins_g=round(total_proteins, 1),
        total_fiber_g=round(total_fiber, 1),
        total_salt_g=round(total_salt, 2),
        protein_pct=protein_pct,
        carbs_pct=carbs_pct,
        fat_pct=fat_pct,
        meals_count=len(meals),
        items_count=items_count,
        avg_nutriscore=round(sum(nutriscore_scores) / len(nutriscore_scores), 1) if nutriscore_scores else None,
        meals=meals,
    )


@router.get("/weekly-trends", response_model=WeeklyTrend)
async def get_weekly_trends(
    weeks: int = Query(4, ge=1, le=12, description="Number of weeks to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get weekly nutrition trends for the current user."""
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    result = await db.execute(
        select(
            Meal.meal_date,
            func.sum(MealItem.energy_kcal).label("daily_kcal"),
            func.sum(MealItem.proteins_g).label("daily_proteins"),
            func.sum(MealItem.carbohydrates_g).label("daily_carbs"),
            func.sum(MealItem.fat_g).label("daily_fat"),
        )
        .join(MealItem, Meal.meal_id == MealItem.meal_id)
        .where(
            Meal.user_id == current_user.user_id,
            Meal.meal_date >= start_date,
            Meal.meal_date <= end_date,
        )
        .group_by(Meal.meal_date)
        .order_by(Meal.meal_date)
    )
    rows = result.all()

    dates = [r.meal_date for r in rows]
    daily_kcal = [float(r.daily_kcal or 0) for r in rows]
    daily_proteins = [float(r.daily_proteins or 0) for r in rows]
    daily_carbs = [float(r.daily_carbs or 0) for r in rows]
    daily_fat = [float(r.daily_fat or 0) for r in rows]

    # Compute 7-day moving average
    moving_avg = []
    for i in range(len(daily_kcal)):
        window = daily_kcal[max(0, i - 6): i + 1]
        moving_avg.append(round(sum(window) / len(window), 0))

    return WeeklyTrend(
        dates=dates,
        daily_kcal=daily_kcal,
        daily_proteins=daily_proteins,
        daily_carbs=daily_carbs,
        daily_fat=daily_fat,
        moving_avg_kcal=moving_avg,
    )
