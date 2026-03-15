"""Product endpoints (C12 - REST API)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth.jwt import get_current_user
from api.database import get_db
from api.models.product import Product
from api.models.user import User
from api.schemas.product import ProductAlternative, ProductOut, ProductSearchResult

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("/{barcode}", response_model=ProductOut)
async def get_product_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a product by its barcode."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.brand), selectinload(Product.category))
        .where(Product.barcode == barcode)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with barcode {barcode} not found")

    return product


@router.get("/", response_model=ProductSearchResult)
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    nutriscore: str | None = Query(None, description="Filter by Nutri-Score grade (A-E)"),
    nova_group: int | None = Query(None, ge=1, le=4, description="Filter by NOVA group"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search products by name with optional filters."""
    query = (
        select(Product)
        .options(selectinload(Product.brand), selectinload(Product.category))
        .where(Product.product_name.ilike(f"%{q}%"))
    )

    if nutriscore:
        query = query.where(Product.nutriscore_grade == nutriscore.upper())
    if nova_group:
        query = query.where(Product.nova_group == nova_group)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()

    return ProductSearchResult(
        total=total,
        page=page,
        page_size=page_size,
        products=products,
    )


@router.get("/{barcode}/alternatives", response_model=list[ProductAlternative])
async def get_healthier_alternatives(
    barcode: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find healthier alternatives in the same category."""
    # Get the reference product
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.brand), selectinload(Product.category))
        .where(Product.barcode == barcode)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.category_id:
        raise HTTPException(status_code=400, detail="Product has no category; cannot find alternatives")

    # Find better alternatives in same category
    query = (
        select(Product)
        .options(selectinload(Product.brand), selectinload(Product.category))
        .where(
            Product.category_id == product.category_id,
            Product.product_id != product.product_id,
            Product.nutriscore_score.isnot(None),
        )
    )

    if product.nutriscore_score is not None:
        query = query.where(Product.nutriscore_score < product.nutriscore_score)

    query = query.order_by(Product.nutriscore_score.asc()).limit(limit)
    result = await db.execute(query)
    alternatives = result.scalars().all()

    return [
        ProductAlternative(
            product=alt,
            nutriscore_improvement=(
                f"{product.nutriscore_grade or '?'} -> {alt.nutriscore_grade or '?'}"
                if product.nutriscore_grade
                else None
            ),
            nova_improvement=(
                f"{product.nova_group or '?'} -> {alt.nova_group or '?'}"
                if product.nova_group and alt.nova_group and alt.nova_group < product.nova_group
                else None
            ),
        )
        for alt in alternatives
    ]
