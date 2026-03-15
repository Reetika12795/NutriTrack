"""
NutriTrack - Web scraping of nutritional guidelines (RDA values)
Source type: Web scraping (C8)
Sources: ANSES (French health authority) nutritional reference values
Entry point: main()
Dependencies: beautifulsoup4, requests, pandas
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; NutriTrack/1.0; Educational project; contact@nutritrack.local)"

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/raw/scraping"))

# Target URLs for nutritional guidelines
SOURCES = [
    {
        "name": "ANSES Nutritional References",
        "url": "https://www.anses.fr/fr/content/les-references-nutritionnelles-en-vitamines-et-mineraux",
        "type": "vitamins_minerals",
    },
    {
        "name": "EU Nutrition Reference Values",
        "url": "https://multimedia.efsa.europa.eu/drvs/index.htm",
        "type": "eu_drvs",
    },
]

# Fallback: hardcoded RDA values from official sources when scraping fails
# Source: EU Regulation No 1169/2011 (Annex XIII)
EU_RDA_VALUES = [
    {"nutrient": "Energy", "daily_value": 2000, "unit": "kcal", "source": "EU Reg 1169/2011"},
    {"nutrient": "Total fat", "daily_value": 70, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Saturated fat", "daily_value": 20, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Carbohydrates", "daily_value": 260, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Sugars", "daily_value": 90, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Protein", "daily_value": 50, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Salt", "daily_value": 6, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Fiber", "daily_value": 25, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Sodium", "daily_value": 2.4, "unit": "g", "source": "EU Reg 1169/2011"},
    {"nutrient": "Potassium", "daily_value": 2000, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Calcium", "daily_value": 800, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Iron", "daily_value": 14, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Zinc", "daily_value": 10, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin A", "daily_value": 800, "unit": "µg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin C", "daily_value": 80, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin D", "daily_value": 5, "unit": "µg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin E", "daily_value": 12, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin K", "daily_value": 75, "unit": "µg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin B1 (Thiamine)", "daily_value": 1.1, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin B2 (Riboflavin)", "daily_value": 1.4, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin B6", "daily_value": 1.4, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Vitamin B12", "daily_value": 2.5, "unit": "µg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Folic acid", "daily_value": 200, "unit": "µg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Magnesium", "daily_value": 375, "unit": "mg", "source": "EU Reg 1169/2011"},
    {"nutrient": "Phosphorus", "daily_value": 700, "unit": "mg", "source": "EU Reg 1169/2011"},
]


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a web page and return a BeautifulSoup object."""
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, "lxml")
    except requests.RequestException as e:
        logger.error("Error fetching %s: %s", url, e)
        return None


def scrape_anses_guidelines(url: str) -> list[dict]:
    """
    Scrape nutritional reference values from ANSES website.
    Extracts tables containing vitamin and mineral RDA values.
    """
    logger.info("Scraping ANSES nutritional guidelines from %s", url)
    guidelines = []

    soup = fetch_page(url)
    if not soup:
        logger.warning("Could not fetch ANSES page, using fallback data")
        return []

    # Look for data tables on the page
    tables = soup.find_all("table")
    logger.info("Found %d tables on ANSES page", len(tables))

    for table_idx, table in enumerate(tables):
        rows = table.find_all("tr")
        headers = []

        for row_idx, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            if row_idx == 0:
                headers = cell_texts
                continue

            if len(cell_texts) >= 2:
                guideline = {
                    "nutrient": cell_texts[0],
                    "daily_value": cell_texts[1] if len(cell_texts) > 1 else None,
                    "unit": cell_texts[2] if len(cell_texts) > 2 else "",
                    "age_group": headers[1] if len(headers) > 1 else "Adult",
                    "source": "ANSES",
                    "source_url": url,
                }
                guidelines.append(guideline)

    logger.info("Scraped %d guideline entries from ANSES", len(guidelines))
    return guidelines


def scrape_efsa_drvs(url: str) -> list[dict]:
    """
    Scrape Dietary Reference Values from EFSA interactive tool.
    Falls back to known EU regulation values if the page isn't scrapable.
    """
    logger.info("Attempting to scrape EFSA DRVs from %s", url)

    soup = fetch_page(url)
    if not soup:
        logger.warning("Could not fetch EFSA page, using EU regulation fallback")
        return []

    # EFSA's tool is JavaScript-heavy; extract what we can from static HTML
    guidelines = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:  # Skip header
            cells = row.find_all(["th", "td"])
            if len(cells) >= 3:
                guidelines.append(
                    {
                        "nutrient": cells[0].get_text(strip=True),
                        "daily_value": cells[1].get_text(strip=True),
                        "unit": cells[2].get_text(strip=True),
                        "source": "EFSA",
                        "source_url": url,
                    }
                )

    logger.info("Scraped %d entries from EFSA", len(guidelines))
    return guidelines


def get_fallback_rda() -> list[dict]:
    """Return fallback RDA values from EU Regulation 1169/2011."""
    logger.info("Using fallback EU RDA values (%d nutrients)", len(EU_RDA_VALUES))
    return EU_RDA_VALUES


def parse_numeric_value(value_str: str) -> float | None:
    """Parse a numeric value from a string, handling various formats."""
    if not value_str or not isinstance(value_str, str):
        return None

    # Remove common non-numeric characters
    cleaned = value_str.strip().replace(",", ".").replace(" ", "")

    # Handle ranges like "10-15" -> take midpoint
    if "-" in cleaned and not cleaned.startswith("-"):
        parts = cleaned.split("-")
        try:
            return (float(parts[0]) + float(parts[1])) / 2
        except (ValueError, IndexError):
            pass

    # Handle "< 5" or "> 10"
    for prefix in ["<", ">", "≤", "≥", "~"]:
        cleaned = cleaned.replace(prefix, "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def save_results(guidelines: list[dict], filename: str) -> Path:
    """Save scraped guidelines to JSON and CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = OUTPUT_DIR / f"{filename}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "extraction_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "source": "Web scraping (ANSES, EFSA, EU Regulation)",
                "record_count": len(guidelines),
                "guidelines": guidelines,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Save CSV
    df = pd.DataFrame(guidelines)
    csv_path = OUTPUT_DIR / f"{filename}.csv"
    df.to_csv(csv_path, index=False)

    logger.info("Saved %d guidelines to %s and %s", len(guidelines), json_path, csv_path)
    return json_path


def main():
    parser = argparse.ArgumentParser(description="Scrape nutritional guidelines from health authority websites")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["anses", "efsa", "fallback", "all"],
        default=["all"],
        help="Sources to scrape",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="nutritional_guidelines",
        help="Output filename (without extension)",
    )

    args = parser.parse_args()
    sources = args.sources if "all" not in args.sources else ["anses", "efsa", "fallback"]

    logger.info("Starting nutritional guidelines scraping (sources: %s)", sources)

    all_guidelines = []

    if "anses" in sources:
        guidelines = scrape_anses_guidelines(SOURCES[0]["url"])
        all_guidelines.extend(guidelines)
        time.sleep(1)  # Polite crawling

    if "efsa" in sources:
        guidelines = scrape_efsa_drvs(SOURCES[1]["url"])
        all_guidelines.extend(guidelines)
        time.sleep(1)

    if "fallback" in sources or not all_guidelines:
        fallback = get_fallback_rda()
        all_guidelines.extend(fallback)

    # Parse numeric values
    for g in all_guidelines:
        if isinstance(g.get("daily_value"), str):
            parsed = parse_numeric_value(g["daily_value"])
            if parsed is not None:
                g["daily_value"] = parsed

    if all_guidelines:
        save_results(all_guidelines, args.output)
        logger.info(
            "Scraping complete: %d guideline entries extracted",
            len(all_guidelines),
        )
    else:
        logger.warning("No guidelines extracted from any source")


if __name__ == "__main__":
    main()
