"""Product analytics endpoints for analyst role (C12 role-based access)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.jwt import require_role
from api.database import get_db
from api.models.product import Brand, Category, Product
from api.models.user import User

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


class NutriscoreDistribution(BaseModel):
    grade: str
    count: int
    percentage: float


class CategoryStats(BaseModel):
    category_name: str
    product_count: int
    avg_energy_kcal: float | None
    avg_proteins_g: float | None
    avg_nutriscore_score: float | None
    pct_grade_a_b: float | None


class BrandRanking(BaseModel):
    brand_name: str
    product_count: int
    avg_nutriscore_score: float | None
    avg_nova_group: float | None
    best_grade: str | None
    worst_grade: str | None


class NovaDistribution(BaseModel):
    nova_group: int
    label: str
    count: int
    percentage: float


class DataQualityMetrics(BaseModel):
    total_products: int
    with_nutriscore: int
    with_nova: int
    with_energy: int
    with_ingredients: int
    avg_completeness: float | None
    nutriscore_pct: float
    nova_pct: float
    energy_pct: float
    ingredients_pct: float


class TopProduct(BaseModel):
    product_name: str
    barcode: str
    brand_name: str | None
    category_name: str | None
    energy_kcal: float | None
    nutriscore_grade: str | None
    nova_group: int | None


class AnalyticsSummary(BaseModel):
    nutriscore_distribution: list[NutriscoreDistribution]
    nova_distribution: list[NovaDistribution]
    top_categories: list[CategoryStats]
    top_brands_healthy: list[BrandRanking]
    top_brands_unhealthy: list[BrandRanking]
    data_quality: DataQualityMetrics
    healthiest_products: list[TopProduct]
    least_healthy_products: list[TopProduct]


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("analyst", "admin")),
):
    """Full analytics summary of the Open Food Facts product database.

    Restricted to analyst and admin roles.
    """
    # --- Nutri-Score distribution ---
    ns_result = await db.execute(
        select(
            Product.nutriscore_grade,
            func.count().label("cnt"),
        )
        .where(Product.nutriscore_grade.isnot(None))
        .group_by(Product.nutriscore_grade)
        .order_by(Product.nutriscore_grade)
    )
    ns_rows = ns_result.all()
    ns_total = sum(r.cnt for r in ns_rows)
    nutriscore_dist = [
        NutriscoreDistribution(
            grade=r.nutriscore_grade,
            count=r.cnt,
            percentage=round(r.cnt / max(ns_total, 1) * 100, 1),
        )
        for r in ns_rows
    ]

    # --- NOVA distribution ---
    nova_labels = {1: "Unprocessed", 2: "Processed ingredients", 3: "Processed", 4: "Ultra-processed"}
    nova_result = await db.execute(
        select(
            Product.nova_group,
            func.count().label("cnt"),
        )
        .where(Product.nova_group.isnot(None))
        .group_by(Product.nova_group)
        .order_by(Product.nova_group)
    )
    nova_rows = nova_result.all()
    nova_total = sum(r.cnt for r in nova_rows)
    nova_dist = [
        NovaDistribution(
            nova_group=r.nova_group,
            label=nova_labels.get(r.nova_group, f"Group {r.nova_group}"),
            count=r.cnt,
            percentage=round(r.cnt / max(nova_total, 1) * 100, 1),
        )
        for r in nova_rows
    ]

    # --- Top categories by product count ---
    cat_result = await db.execute(
        select(
            Category.category_name,
            func.count().label("product_count"),
            func.avg(cast(Product.energy_kcal, Float)).label("avg_energy"),
            func.avg(cast(Product.proteins_g, Float)).label("avg_proteins"),
            func.avg(cast(Product.nutriscore_score, Float)).label("avg_ns"),
            (func.sum(case((Product.nutriscore_grade.in_(["A", "B"]), 1), else_=0))
             * 100.0 / func.count()).label("pct_ab"),
        )
        .join(Product, Category.category_id == Product.category_id)
        .group_by(Category.category_name)
        .order_by(func.count().desc())
        .limit(15)
    )
    cat_rows = cat_result.all()
    top_categories = [
        CategoryStats(
            category_name=r.category_name,
            product_count=r.product_count,
            avg_energy_kcal=round(r.avg_energy, 1) if r.avg_energy else None,
            avg_proteins_g=round(r.avg_proteins, 1) if r.avg_proteins else None,
            avg_nutriscore_score=round(r.avg_ns, 1) if r.avg_ns else None,
            pct_grade_a_b=round(float(r.pct_ab), 1) if r.pct_ab else None,
        )
        for r in cat_rows
    ]

    # --- Healthiest brands (lowest avg nutriscore_score = better) ---
    brand_base = (
        select(
            Brand.brand_name,
            func.count().label("product_count"),
            func.avg(cast(Product.nutriscore_score, Float)).label("avg_ns"),
            func.avg(cast(Product.nova_group, Float)).label("avg_nova"),
            func.min(Product.nutriscore_grade).label("best"),
            func.max(Product.nutriscore_grade).label("worst"),
        )
        .join(Product, Brand.brand_id == Product.brand_id)
        .where(Product.nutriscore_score.isnot(None))
        .group_by(Brand.brand_name)
        .having(func.count() >= 5)
    )

    healthy_result = await db.execute(
        brand_base.order_by(func.avg(cast(Product.nutriscore_score, Float)).asc()).limit(10)
    )
    unhealthy_result = await db.execute(
        brand_base.order_by(func.avg(cast(Product.nutriscore_score, Float)).desc()).limit(10)
    )

    def brand_rows_to_list(rows):
        return [
            BrandRanking(
                brand_name=r.brand_name,
                product_count=r.product_count,
                avg_nutriscore_score=round(r.avg_ns, 1) if r.avg_ns else None,
                avg_nova_group=round(r.avg_nova, 1) if r.avg_nova else None,
                best_grade=r.best,
                worst_grade=r.worst,
            )
            for r in rows
        ]

    top_healthy = brand_rows_to_list(healthy_result.all())
    top_unhealthy = brand_rows_to_list(unhealthy_result.all())

    # --- Data quality ---
    total_result = await db.execute(select(func.count()).select_from(Product))
    total_products = total_result.scalar()

    quality_result = await db.execute(
        select(
            func.sum(case((Product.nutriscore_grade.isnot(None), 1), else_=0)).label("with_ns"),
            func.sum(case((Product.nova_group.isnot(None), 1), else_=0)).label("with_nova"),
            func.sum(case((Product.energy_kcal.isnot(None), 1), else_=0)).label("with_energy"),
            func.sum(case((Product.ingredients_text.isnot(None), 1), else_=0)).label("with_ingredients"),
            func.avg(cast(Product.completeness_score, Float)).label("avg_completeness"),
        )
    )
    qr = quality_result.one()
    data_quality = DataQualityMetrics(
        total_products=total_products,
        with_nutriscore=int(qr.with_ns or 0),
        with_nova=int(qr.with_nova or 0),
        with_energy=int(qr.with_energy or 0),
        with_ingredients=int(qr.with_ingredients or 0),
        avg_completeness=round(float(qr.avg_completeness), 3) if qr.avg_completeness else None,
        nutriscore_pct=round(int(qr.with_ns or 0) / max(total_products, 1) * 100, 1),
        nova_pct=round(int(qr.with_nova or 0) / max(total_products, 1) * 100, 1),
        energy_pct=round(int(qr.with_energy or 0) / max(total_products, 1) * 100, 1),
        ingredients_pct=round(int(qr.with_ingredients or 0) / max(total_products, 1) * 100, 1),
    )

    # --- Healthiest / least healthy products ---
    product_base = (
        select(Product, Brand.brand_name, Category.category_name)
        .outerjoin(Brand, Product.brand_id == Brand.brand_id)
        .outerjoin(Category, Product.category_id == Category.category_id)
        .where(Product.nutriscore_score.isnot(None), Product.product_name.isnot(None))
    )

    healthiest_result = await db.execute(
        product_base.order_by(Product.nutriscore_score.asc()).limit(10)
    )
    least_result = await db.execute(
        product_base.order_by(Product.nutriscore_score.desc()).limit(10)
    )

    def product_rows_to_list(rows):
        return [
            TopProduct(
                product_name=r.Product.product_name,
                barcode=r.Product.barcode,
                brand_name=r.brand_name,
                category_name=r.category_name,
                energy_kcal=float(r.Product.energy_kcal) if r.Product.energy_kcal else None,
                nutriscore_grade=r.Product.nutriscore_grade,
                nova_group=r.Product.nova_group,
            )
            for r in rows
        ]

    return AnalyticsSummary(
        nutriscore_distribution=nutriscore_dist,
        nova_distribution=nova_dist,
        top_categories=top_categories,
        top_brands_healthy=top_healthy,
        top_brands_unhealthy=top_unhealthy,
        data_quality=data_quality,
        healthiest_products=product_rows_to_list(healthiest_result.all()),
        least_healthy_products=product_rows_to_list(least_result.all()),
    )
