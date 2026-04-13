"""Nutritionist endpoints - aggregated user analytics (C12 role-based access)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.jwt import require_role
from api.database import get_db
from api.models.user import Meal, MealItem, User

router = APIRouter(prefix="/api/v1/nutritionist", tags=["Nutritionist"])


class UserStats(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    activity_level: str | None
    dietary_goal: str | None
    is_active: bool
    total_meals: int
    total_kcal: float
    avg_daily_kcal: float

    class Config:
        from_attributes = True


@router.get("/users", response_model=list[UserStats])
async def list_users_with_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("nutritionist", "admin")),
):
    """List all users with aggregated nutrition statistics.

    Restricted to nutritionist and admin roles.
    """
    stmt = (
        select(
            User.user_id,
            User.username,
            User.email,
            User.role,
            User.activity_level,
            User.dietary_goal,
            User.is_active,
            func.count(func.distinct(Meal.meal_id)).label("total_meals"),
            func.coalesce(func.sum(MealItem.energy_kcal), 0).label("total_kcal"),
        )
        .outerjoin(Meal, User.user_id == Meal.user_id)
        .outerjoin(MealItem, Meal.meal_id == MealItem.meal_id)
        .group_by(
            User.user_id,
            User.username,
            User.email,
            User.role,
            User.activity_level,
            User.dietary_goal,
            User.is_active,
        )
        .order_by(User.username)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        UserStats(
            user_id=str(r.user_id),
            username=r.username,
            email=r.email,
            role=r.role,
            activity_level=r.activity_level,
            dietary_goal=r.dietary_goal,
            is_active=r.is_active,
            total_meals=r.total_meals,
            total_kcal=float(r.total_kcal),
            avg_daily_kcal=round(float(r.total_kcal) / max(r.total_meals, 1), 1),
        )
        for r in rows
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("nutritionist", "admin")),
):
    """Delete a user and all their meal records (cascade).

    Restricted to nutritionist and admin roles.
    Cannot delete yourself.
    """
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account.",
        )

    result = await db.execute(select(User).where(User.user_id == user_id))
    target = result.scalar_one_or_none()

    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target.role == "admin" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete admin accounts.",
        )

    await db.delete(target)
    await db.commit()
