"""SQLAlchemy models for users, meals, meal items."""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "app"}

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), default="user")

    age_group = Column(String(20))
    activity_level = Column(String(20))
    dietary_goal = Column(String(30))

    consent_data_processing = Column(Boolean, default=False)
    consent_date = Column(DateTime)
    data_retention_until = Column(Date)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = {"schema": "app"}

    meal_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app.users.user_id", ondelete="CASCADE"), nullable=False)
    meal_type = Column(String(20), nullable=False)
    meal_date = Column(Date, nullable=False, server_default=func.current_date())
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="meals")
    items = relationship("MealItem", back_populates="meal", cascade="all, delete-orphan")


class MealItem(Base):
    __tablename__ = "meal_items"
    __table_args__ = {"schema": "app"}

    meal_item_id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey("app.meals.meal_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("app.products.product_id"), nullable=False)
    quantity_g = Column(Numeric(8, 2), nullable=False, default=100)

    energy_kcal = Column(Numeric(8, 2))
    fat_g = Column(Numeric(8, 2))
    carbohydrates_g = Column(Numeric(8, 2))
    proteins_g = Column(Numeric(8, 2))
    fiber_g = Column(Numeric(8, 2))
    salt_g = Column(Numeric(8, 4))

    created_at = Column(DateTime, server_default=func.now())

    meal = relationship("Meal", back_populates="items")
    product = relationship("Product", back_populates="meal_items")
