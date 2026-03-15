"""Tests for API Pydantic schemas — validates request/response models."""

from api.schemas.product import BrandOut, CategoryOut, ProductOut, ProductSearchResult
from api.schemas.user import LoginRequest, Token, UserCreate


def test_product_out_schema():
    """ProductOut accepts valid product data."""
    product = ProductOut(
        product_id=1,
        barcode="3017620422003",
        product_name="Nutella",
        energy_kcal=539.0,
        fat_g=30.9,
        proteins_g=6.3,
        nutriscore_grade="E",
        nova_group=4,
    )
    assert product.barcode == "3017620422003"
    assert product.product_name == "Nutella"
    assert product.nutriscore_grade == "E"


def test_product_out_optional_fields():
    """ProductOut works with minimal required fields."""
    product = ProductOut(product_id=1, barcode="1234567890123", product_name=None)
    assert product.product_name is None
    assert product.brand is None
    assert product.energy_kcal is None


def test_brand_out_schema():
    """BrandOut accepts valid brand data."""
    brand = BrandOut(brand_id=1, brand_name="Ferrero")
    assert brand.brand_name == "Ferrero"
    assert brand.parent_company is None


def test_category_out_schema():
    """CategoryOut accepts valid category data."""
    category = CategoryOut(category_id=1, category_name="Snacks")
    assert category.category_name == "Snacks"


def test_product_search_result_schema():
    """ProductSearchResult wraps paginated product list."""
    result = ProductSearchResult(
        total=100,
        page=1,
        page_size=20,
        products=[
            ProductOut(product_id=1, barcode="1234567890123", product_name="Test"),
        ],
    )
    assert result.total == 100
    assert len(result.products) == 1


def test_user_create_schema():
    """UserCreate validates registration data."""
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="securepassword123",
        consent_data_processing=True,
    )
    assert user.email == "test@example.com"
    assert user.consent_data_processing is True


def test_login_request_schema():
    """LoginRequest validates login credentials."""
    login = LoginRequest(username="testuser", password="pass123")
    assert login.username == "testuser"


def test_token_schema():
    """Token schema sets default token type."""
    token = Token(access_token="eyJ...")
    assert token.token_type == "bearer"
