"""
NutriTrack - Extract products from Open Food Facts REST API
Source type: REST API (C8)
Entry point: main()
Dependencies: requests, json, logging
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Open Food Facts API configuration
OFF_API_BASE = "https://world.openfoodfacts.org"
OFF_API_SEARCH = f"{OFF_API_BASE}/cgi/search.pl"
OFF_API_PRODUCT = f"{OFF_API_BASE}/api/v2/product"
USER_AGENT = "NutriTrack/1.0 (https://github.com/nutritrack; contact@nutritrack.local)"

# Fields to extract
PRODUCT_FIELDS = [
    "code",
    "product_name",
    "generic_name",
    "quantity",
    "packaging",
    "brands",
    "categories",
    "countries",
    "energy-kcal_100g",
    "energy-kj_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "fiber_100g",
    "proteins_100g",
    "salt_100g",
    "sodium_100g",
    "nutriscore_grade",
    "nutriscore_score",
    "nova_group",
    "ecoscore_grade",
    "ingredients_text",
    "allergens",
    "traces",
    "image_url",
    "url",
    "completeness",
    "last_modified_t",
]

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/raw/api"))


def extract_product_by_barcode(barcode: str) -> dict | None:
    """Extract a single product by barcode from the OFF API."""
    url = f"{OFF_API_PRODUCT}/{barcode}"
    params = {"fields": ",".join(PRODUCT_FIELDS)}
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == 1:
            return data["product"]
        logger.warning("Product %s not found in OFF", barcode)
        return None

    except requests.RequestException as e:
        logger.error("Error fetching barcode %s: %s", barcode, e)
        return None


def search_products(query: str, page: int = 1, page_size: int = 50) -> list[dict]:
    """Search products by query string with pagination."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": ",".join(PRODUCT_FIELDS),
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(OFF_API_SEARCH, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])

    except requests.RequestException as e:
        logger.error("Error searching products for '%s': %s", query, e)
        return []


def extract_products_by_category(category: str, max_pages: int = 10, page_size: int = 50) -> list[dict]:
    """Extract all products in a category with pagination and rate limiting."""
    all_products = []

    for page in range(1, max_pages + 1):
        logger.info("Fetching category '%s' - page %d/%d", category, page, max_pages)
        products = search_products(category, page=page, page_size=page_size)

        if not products:
            logger.info("No more products found at page %d", page)
            break

        all_products.extend(products)
        logger.info("Retrieved %d products (total: %d)", len(products), len(all_products))

        # Rate limiting: respect OFF API guidelines (max ~100 req/min)
        time.sleep(0.6)

    return all_products


def save_results(products: list[dict], filename: str) -> Path:
    """Save extracted products to a JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "extraction_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "source": "Open Food Facts API",
                "record_count": len(products),
                "products": products,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    logger.info("Saved %d products to %s", len(products), output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Extract products from Open Food Facts API")
    parser.add_argument(
        "--mode",
        choices=["barcode", "search", "category"],
        default="category",
        help="Extraction mode",
    )
    parser.add_argument("--query", type=str, help="Search query or category name")
    parser.add_argument(
        "--barcodes",
        type=str,
        nargs="+",
        help="Barcodes to extract (barcode mode)",
    )
    parser.add_argument("--max-pages", type=int, default=5, help="Max pages to fetch")
    parser.add_argument("--page-size", type=int, default=50, help="Products per page")
    parser.add_argument("--output", type=str, default="off_api_extract.json", help="Output filename")

    args = parser.parse_args()

    logger.info("Starting Open Food Facts API extraction (mode: %s)", args.mode)

    products = []
    if args.mode == "barcode":
        barcodes = args.barcodes or ["3017620422003", "5449000000996", "8000500310427"]
        for barcode in barcodes:
            product = extract_product_by_barcode(barcode)
            if product:
                products.append(product)
            time.sleep(0.5)

    elif args.mode == "search":
        query = args.query or "chocolat"
        products = search_products(query, page_size=args.page_size)

    elif args.mode == "category":
        categories = [
            "breakfast cereals",
            "yogurts",
            "chocolate",
            "beverages",
            "snacks",
        ]
        if args.query:
            categories = [args.query]

        for category in categories:
            category_products = extract_products_by_category(
                category, max_pages=args.max_pages, page_size=args.page_size
            )
            products.extend(category_products)

    if products:
        output_path = save_results(products, args.output)
        logger.info(
            "Extraction complete: %d products saved to %s",
            len(products),
            output_path,
        )
    else:
        logger.warning("No products extracted")
        sys.exit(1)


if __name__ == "__main__":
    main()
