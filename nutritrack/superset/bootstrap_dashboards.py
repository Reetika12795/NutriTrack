"""
Bootstrap Superset dashboards for NutriTrack analytics.
Creates datasets, charts, and 3 dashboards via the Superset REST API.

Issues: #12 (Product Market), #13 (Nutrition Trends), #14 (DW Health)
"""
import json
import os
import subprocess
import sys
import time

import requests

BASE_URL = os.environ.get("SUPERSET_URL", "http://localhost:8088")
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

# Global session for cookie persistence
SESSION = requests.Session()


def get_auth_tokens():
    """Get JWT access token and CSRF token using a session for cookie persistence."""
    r = SESSION.post(
        f"{BASE_URL}/api/v1/security/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS, "provider": "db"},
    )
    r.raise_for_status()
    access_token = r.json()["access_token"]

    SESSION.headers.update({"Authorization": f"Bearer {access_token}"})
    r = SESSION.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    r.raise_for_status()
    csrf_token = r.json()["result"]

    SESSION.headers.update({
        "X-CSRFToken": csrf_token,
        "Referer": BASE_URL,
    })
    return SESSION.headers


def get_database_id(headers):
    """Get the NutriTrack DW database ID."""
    r = SESSION.get(f"{BASE_URL}/api/v1/database/")
    r.raise_for_status()
    for db in r.json()["result"]:
        if "NutriTrack" in db["database_name"]:
            return db["id"]
    raise RuntimeError("NutriTrack DW database not found in Superset")


def create_dataset(headers, db_id, table_name, schema="dw"):
    """Create a dataset (or return existing) for a DW view/table."""
    # Check if dataset already exists
    r = SESSION.get(
        f"{BASE_URL}/api/v1/dataset/",
        params={"q": json.dumps({"filters": [{"col": "table_name", "opr": "eq", "value": table_name}]})},
    )
    r.raise_for_status()
    if r.json()["count"] > 0:
        ds_id = r.json()["result"][0]["id"]
        print(f"  Dataset exists: {schema}.{table_name} (id={ds_id})")
        return ds_id

    r = SESSION.post(
        f"{BASE_URL}/api/v1/dataset/",
        json={"database": db_id, "table_name": table_name, "schema": schema},
    )
    r.raise_for_status()
    ds_id = r.json()["id"]
    print(f"  Created dataset: {schema}.{table_name} (id={ds_id})")
    return ds_id


def create_chart(headers, name, viz_type, datasource_id, params):
    """Create a chart (slice) in Superset."""
    # Check if chart already exists
    r = SESSION.get(
        f"{BASE_URL}/api/v1/chart/",
        params={"q": json.dumps({"filters": [{"col": "slice_name", "opr": "eq", "value": name}]})},
    )
    r.raise_for_status()
    if r.json()["count"] > 0:
        chart_id = r.json()["result"][0]["id"]
        print(f"  Chart exists: {name} (id={chart_id})")
        return chart_id

    r = SESSION.post(
        f"{BASE_URL}/api/v1/chart/",
        json={
            "slice_name": name,
            "viz_type": viz_type,
            "datasource_id": datasource_id,
            "datasource_type": "table",
            "params": json.dumps(params),
        },
    )
    r.raise_for_status()
    chart_id = r.json()["id"]
    print(f"  Created chart: {name} (id={chart_id})")
    return chart_id


def create_dashboard(headers, title, slug, chart_ids):
    """Create a dashboard and add charts to it."""
    # Check if dashboard exists
    r = SESSION.get(
        f"{BASE_URL}/api/v1/dashboard/",
        params={"q": json.dumps({"filters": [{"col": "slug", "opr": "eq", "value": slug}]})},
    )
    r.raise_for_status()
    if r.json()["count"] > 0:
        dash_id = r.json()["result"][0]["id"]
        print(f"  Dashboard exists: {title} (id={dash_id})")
        return dash_id

    # Build a simple grid layout for the charts
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": [f"ROW-{i}" for i in range(len(chart_ids))],
        },
    }
    for i, chart_id in enumerate(chart_ids):
        row_id = f"ROW-{i}"
        chart_key = f"CHART-{chart_id}"
        position[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [chart_key],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        position[chart_key] = {
            "type": "CHART",
            "id": chart_key,
            "children": [],
            "meta": {
                "chartId": chart_id,
                "width": 12,
                "height": 50,
                "sliceName": f"Chart {chart_id}",
            },
        }

    r = SESSION.post(
        f"{BASE_URL}/api/v1/dashboard/",
        json={
            "dashboard_title": title,
            "slug": slug,
            "published": True,
            "position_json": json.dumps(position),
        },
    )
    r.raise_for_status()
    dash_id = r.json()["id"]
    print(f"  Created dashboard: {title} (id={dash_id})")

    # Link charts to dashboard via metadata DB
    # (Superset REST API doesn't create dashboard_slices associations)
    link_charts_to_dashboard(dash_id, chart_ids)

    return dash_id


def link_charts_to_dashboard(dashboard_id, chart_ids):
    """Insert dashboard_slices rows to associate charts with a dashboard.

    Uses docker compose exec to run SQL against the superset metadata DB,
    because the Superset REST API does not create these associations.
    """
    values = ", ".join(f"({dashboard_id}, {cid})" for cid in chart_ids)
    sql = (
        f"INSERT INTO dashboard_slices (dashboard_id, slice_id) "
        f"VALUES {values} ON CONFLICT DO NOTHING;"
    )
    subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres",
         "psql", "-U", "superset", "-d", "superset", "-c", sql],
        capture_output=True, text=True,
    )
    print(f"  Linked {len(chart_ids)} charts to dashboard {dashboard_id}")


def build_product_market_dashboard(headers, db_id):
    """Issue #12: Product Market Analysis dashboard."""
    print("\n=== Dashboard: Product Market Analysis (#12) ===")

    # Datasets
    ds_market = create_dataset(headers, db_id, "dm_product_market_by_category")
    ds_brand = create_dataset(headers, db_id, "dm_brand_quality_ranking")
    ds_nutriscore = create_dataset(headers, db_id, "dm_nutriscore_distribution")
    ds_fact = create_dataset(headers, db_id, "fact_product_market")

    # Charts
    charts = []

    # 1. Nutri-Score distribution bar chart
    charts.append(create_chart(headers, "Nutri-Score Distribution by Category", "echarts_bar", ds_nutriscore, {
        "x_axis": "nutriscore_grade",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "product_count"}, "aggregate": "SUM", "label": "Product Count"}],
        "groupby": ["category_name"],
        "row_limit": 1000,
        "color_scheme": "supersetColors",
    }))

    # 2. Brand quality ranking
    charts.append(create_chart(headers, "Top Brands by Nutrition Quality", "echarts_bar", ds_brand, {
        "x_axis": "brand_name",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "avg_nutriscore_score"}, "aggregate": "AVG", "label": "Avg Nutri-Score"}],
        "row_limit": 20,
        "order_desc": True,
        "color_scheme": "supersetColors",
    }))

    # 3. Category nutrition comparison
    charts.append(create_chart(headers, "Category Nutrition Comparison", "echarts_bar", ds_market, {
        "x_axis": "category_name",
        "metrics": [
            {"expressionType": "SIMPLE", "column": {"column_name": "avg_kcal"}, "aggregate": "AVG", "label": "Avg Kcal"},
            {"expressionType": "SIMPLE", "column": {"column_name": "avg_proteins"}, "aggregate": "AVG", "label": "Avg Proteins"},
        ],
        "row_limit": 50,
        "color_scheme": "supersetColors",
    }))

    # 4. Product count by Nutri-Score grade (pie)
    charts.append(create_chart(headers, "Products by Nutri-Score Grade", "pie", ds_fact, {
        "groupby": ["nutriscore_grade"],
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Count"},
        "row_limit": 10,
        "color_scheme": "supersetColors",
    }))

    return create_dashboard(headers, "Product Market Analysis", "product-market", charts)


def build_nutrition_trends_dashboard(headers, db_id):
    """Issue #13: User Nutrition Trends dashboard."""
    print("\n=== Dashboard: Nutrition Trends (#13) ===")

    ds_trends = create_dataset(headers, db_id, "dm_nutrition_trends")
    ds_daily = create_dataset(headers, db_id, "dm_user_daily_nutrition")

    charts = []

    # 1. Daily calorie trends with moving average
    charts.append(create_chart(headers, "Daily Calorie Intake Trend", "echarts_timeseries_line", ds_trends, {
        "x_axis": "full_date",
        "metrics": [
            {"expressionType": "SIMPLE", "column": {"column_name": "total_kcal"}, "aggregate": "SUM", "label": "Total Kcal"},
            {"expressionType": "SIMPLE", "column": {"column_name": "kcal_7day_moving_avg"}, "aggregate": "AVG", "label": "7-Day Moving Avg"},
        ],
        "row_limit": 365,
        "color_scheme": "supersetColors",
    }))

    # 2. Macro distribution (stacked area)
    charts.append(create_chart(headers, "Macro Nutrient Distribution", "echarts_area", ds_trends, {
        "x_axis": "full_date",
        "metrics": [
            {"expressionType": "SIMPLE", "column": {"column_name": "total_proteins_g"}, "aggregate": "SUM", "label": "Proteins (g)"},
            {"expressionType": "SIMPLE", "column": {"column_name": "total_fat_g"}, "aggregate": "SUM", "label": "Fat (g)"},
            {"expressionType": "SIMPLE", "column": {"column_name": "total_carbs_g"}, "aggregate": "SUM", "label": "Carbs (g)"},
        ],
        "row_limit": 365,
        "stack": True,
        "color_scheme": "supersetColors",
    }))

    # 3. Meal type breakdown (pie)
    charts.append(create_chart(headers, "Meal Type Breakdown", "pie", ds_daily, {
        "groupby": ["meal_type"],
        "metric": {"expressionType": "SIMPLE", "column": {"column_name": "items_count"}, "aggregate": "SUM", "label": "Items"},
        "row_limit": 10,
        "color_scheme": "supersetColors",
    }))

    # 4. Active users by dietary goal
    charts.append(create_chart(headers, "Active Users by Dietary Goal", "echarts_bar", ds_trends, {
        "x_axis": "dietary_goal",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "active_users"}, "aggregate": "SUM", "label": "Active Users"}],
        "row_limit": 20,
        "color_scheme": "supersetColors",
    }))

    return create_dashboard(headers, "Nutrition Trends", "nutrition-trends", charts)


def build_dw_health_dashboard(headers, db_id):
    """Issue #14: DW Health & Data Quality dashboard."""
    print("\n=== Dashboard: DW Health & Data Quality (#14) ===")

    ds_health = create_dataset(headers, db_id, "dm_dw_health")

    charts = []

    # 1. Record counts per table
    charts.append(create_chart(headers, "DW Record Counts by Table", "echarts_bar", ds_health, {
        "x_axis": "table_name",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_rows"}, "aggregate": "SUM", "label": "Total Rows"}],
        "groupby": ["table_type"],
        "row_limit": 50,
        "color_scheme": "supersetColors",
    }))

    # 2. Data completeness
    charts.append(create_chart(headers, "Data Completeness by Table", "echarts_bar", ds_health, {
        "x_axis": "table_name",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "name_completeness_pct"}, "aggregate": "AVG", "label": "Completeness %"}],
        "row_limit": 50,
        "color_scheme": "supersetColors",
    }))

    # 3. Active vs total rows (SCD tracking)
    charts.append(create_chart(headers, "Active vs Total Records (SCD)", "echarts_bar", ds_health, {
        "x_axis": "table_name",
        "metrics": [
            {"expressionType": "SIMPLE", "column": {"column_name": "total_rows"}, "aggregate": "SUM", "label": "Total Rows"},
            {"expressionType": "SIMPLE", "column": {"column_name": "active_rows"}, "aggregate": "SUM", "label": "Active Rows"},
        ],
        "row_limit": 50,
        "color_scheme": "supersetColors",
    }))

    return create_dashboard(headers, "DW Health & Data Quality", "dw-health", charts)


def main():
    print("Waiting for Superset API to be ready...")
    for attempt in range(30):
        try:
            r = SESSION.get(f"{BASE_URL}/health", timeout=5)
            if r.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(5)
    else:
        print("ERROR: Superset not reachable after 150s")
        sys.exit(1)

    print("Superset is ready. Authenticating...")
    headers = get_auth_tokens()
    db_id = get_database_id(headers)
    print(f"NutriTrack DW database ID: {db_id}")

    build_product_market_dashboard(headers, db_id)
    build_nutrition_trends_dashboard(headers, db_id)
    build_dw_health_dashboard(headers, db_id)

    print("\n=== All dashboards created successfully ===")
    print(f"  Product Market Analysis: {BASE_URL}/superset/dashboard/product-market/")
    print(f"  Nutrition Trends:        {BASE_URL}/superset/dashboard/nutrition-trends/")
    print(f"  DW Health & Data Quality:{BASE_URL}/superset/dashboard/dw-health/")


if __name__ == "__main__":
    main()
