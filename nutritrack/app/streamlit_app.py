"""
NutriTrack - Fitness Nutrition Tracker
Streamlit frontend application with role-based dashboards (C7, C12, C21)

Roles:
  - user:          Product Search, Meal Logger, Daily Dashboard, Weekly Trends,
                   Product Comparison, Healthier Alternatives
  - nutritionist:  All user pages + Nutritionist Dashboard (all patients)
  - analyst:       All user pages + Product Analytics + Data Catalog
  - admin:         Everything (all pages)
"""

import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="NutriTrack",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================
# Auth helpers
# ==============================================================


def api_request(method: str, endpoint: str, **kwargs) -> requests.Response | None:
    """Make an authenticated API request."""
    token = st.session_state.get("token")
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        url = f"{API_BASE_URL}{endpoint}"
        resp = requests.request(method, url, headers=headers, timeout=10, **kwargs)
        if resp.status_code == 401:
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
            st.warning("Session expired. Please log in again.")
            return None
        return resp
    except requests.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
        return None


def login_page():
    """Display login/register form."""
    st.title("NutriTrack")
    st.subheader("Fitness Nutrition Tracker")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted and username and password:
                resp = api_request(
                    "POST",
                    "/api/v1/auth/login",
                    json={"username": username, "password": password},
                )
                if resp and resp.status_code == 200:
                    data = resp.json()
                    st.session_state["token"] = data["access_token"]
                    user_resp = api_request("GET", "/api/v1/auth/me")
                    if user_resp and user_resp.ok:
                        st.session_state["user"] = user_resp.json()
                    st.rerun()
                elif resp:
                    st.error("Invalid username or password")

    with tab_register:
        with st.form("register_form"):
            new_email = st.text_input("Email")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            activity = st.selectbox(
                "Activity Level",
                ["sedentary", "light", "moderate", "active", "very_active"],
            )
            goal = st.selectbox(
                "Dietary Goal",
                ["eat_healthier", "lose_weight", "maintain", "gain_muscle"],
            )
            consent = st.checkbox("I consent to data processing (RGPD)")
            submitted = st.form_submit_button("Register")

            if submitted and new_email and new_username and new_password:
                if not consent:
                    st.error("You must consent to data processing to register.")
                else:
                    resp = api_request(
                        "POST",
                        "/api/v1/auth/register",
                        json={
                            "email": new_email,
                            "username": new_username,
                            "password": new_password,
                            "activity_level": activity,
                            "dietary_goal": goal,
                            "consent_data_processing": True,
                        },
                    )
                    if resp and resp.status_code == 201:
                        st.success("Account created! You can now log in.")
                    elif resp:
                        st.error(f"Registration failed: {resp.json().get('detail', 'Unknown error')}")


# ==============================================================
# User pages (all roles)
# ==============================================================


def product_search_page():
    """Product search and barcode lookup."""
    st.header("🔍 Product Search")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search for a product", placeholder="e.g., chocolat noir, yaourt nature...")
    with col2:
        nutriscore_filter = st.selectbox("Nutri-Score", ["All", "A", "B", "C", "D", "E"])

    if query:
        params = {"q": query, "page_size": 20}
        if nutriscore_filter != "All":
            params["nutriscore"] = nutriscore_filter

        resp = api_request("GET", "/api/v1/products/", params=params)
        if resp and resp.ok:
            data = resp.json()
            st.write(f"**{data['total']} results found**")

            for product in data["products"]:
                with st.expander(f"{product['product_name']} - {product.get('barcode', '')}"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.write("**Nutri-Score:**", product.get("nutriscore_grade", "N/A"))
                        st.write("**NOVA Group:**", product.get("nova_group", "N/A"))
                        if product.get("brand"):
                            st.write("**Brand:**", product["brand"]["brand_name"])
                        if product.get("category"):
                            st.write("**Category:**", product["category"]["category_name"])
                    with col_b:
                        st.write("**Nutrition per 100g:**")
                        st.write(f"- Energy: {product.get('energy_kcal', 'N/A')} kcal")
                        st.write(f"- Fat: {product.get('fat_g', 'N/A')} g")
                        st.write(f"- Carbs: {product.get('carbohydrates_g', 'N/A')} g")
                        st.write(f"- Protein: {product.get('proteins_g', 'N/A')} g")
                    with col_c:
                        st.write(f"- Fiber: {product.get('fiber_g', 'N/A')} g")
                        st.write(f"- Salt: {product.get('salt_g', 'N/A')} g")
                        st.write(f"- Sugars: {product.get('sugars_g', 'N/A')} g")
                        if st.button("Add to meal", key=f"add_{product['product_id']}"):
                            st.session_state["selected_product"] = product
                            st.info(f"Selected: {product['product_name']}")

    st.divider()
    st.subheader("Barcode Lookup")
    barcode = st.text_input("Enter barcode", placeholder="e.g., 3017620422003")
    if barcode:
        resp = api_request("GET", f"/api/v1/products/{barcode}")
        if resp and resp.ok:
            st.json(resp.json())
        elif resp and resp.status_code == 404:
            st.warning("Product not found")


def meal_logger_page():
    """Log daily meals."""
    st.header("🍽️ Meal Logger")

    with st.form("meal_form"):
        meal_type = st.selectbox("Meal Type", ["breakfast", "lunch", "dinner", "snack"])
        meal_date = st.date_input("Date", value=date.today())
        notes = st.text_area("Notes (optional)")

        st.subheader("Add Products")
        product_id = st.number_input("Product ID", min_value=1, step=1)
        quantity = st.number_input("Quantity (g)", min_value=1.0, value=100.0, step=10.0)

        submitted = st.form_submit_button("Log Meal")
        if submitted:
            resp = api_request(
                "POST",
                "/api/v1/meals",
                json={
                    "meal_type": meal_type,
                    "meal_date": str(meal_date),
                    "notes": notes,
                    "items": [{"product_id": product_id, "quantity_g": quantity}],
                },
            )
            if resp and resp.status_code == 201:
                st.success("Meal logged successfully!")
            elif resp:
                st.error(f"Error: {resp.json().get('detail', 'Unknown error')}")

    st.divider()
    st.subheader("Recent Meals")
    resp = api_request("GET", "/api/v1/meals/", params={"page_size": 10})
    if resp and resp.ok:
        meals = resp.json()
        for meal in meals:
            with st.expander(f"{meal['meal_type'].title()} - {meal['meal_date']}"):
                for item in meal.get("items", []):
                    product_name = item.get("product", {}).get("product_name", "Unknown")
                    st.write(f"- {product_name}: {item['quantity_g']}g ({item.get('energy_kcal', 0):.0f} kcal)")


def daily_dashboard_page():
    """Daily nutrition dashboard."""
    st.header("📊 Daily Dashboard")
    target_date = st.date_input("Select date", value=date.today())

    resp = api_request("GET", "/api/v1/meals/daily-summary", params={"target_date": str(target_date)})
    if resp and resp.ok:
        s = resp.json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Calories", f"{s['total_kcal']:.0f} kcal", delta=f"{s['total_kcal'] - 2000:.0f} vs RDA")
        col2.metric("Protein", f"{s['total_proteins_g']:.1f} g", delta=f"{s['total_proteins_g'] - 50:.1f} vs RDA")
        col3.metric("Fiber", f"{s['total_fiber_g']:.1f} g", delta=f"{s['total_fiber_g'] - 25:.1f} vs RDA")
        col4.metric("Meals", s["meals_count"])

        if s["total_kcal"] > 0:
            col_l, col_r = st.columns(2)
            with col_l:
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Protein", "Carbs", "Fat"],
                            values=[s["protein_pct"], s["carbs_pct"], s["fat_pct"]],
                            marker_colors=["#2ecc71", "#3498db", "#e74c3c"],
                            hole=0.4,
                        )
                    ]
                )
                fig.update_layout(title="Macro Distribution", height=350)
                st.plotly_chart(fig, use_container_width=True)
            with col_r:
                for name, val, rda, unit in [
                    ("Energy", s["total_kcal"], 2000, "kcal"),
                    ("Protein", s["total_proteins_g"], 50, "g"),
                    ("Fat", s["total_fat_g"], 70, "g"),
                    ("Carbs", s["total_carbohydrates_g"], 260, "g"),
                    ("Fiber", s["total_fiber_g"], 25, "g"),
                    ("Salt", s["total_salt_g"], 6, "g"),
                ]:
                    pct = min(val / rda * 100, 100) if rda > 0 else 0
                    st.write(f"**{name}**: {val:.1f} / {rda} {unit} ({pct:.0f}%)")
                    st.progress(pct / 100)
    else:
        st.info("No meals logged for this date.")


def weekly_trends_page():
    """Weekly nutrition trends."""
    st.header("📈 Weekly Trends")
    weeks = st.slider("Weeks to display", 1, 12, 4)
    resp = api_request("GET", "/api/v1/meals/weekly-trends", params={"weeks": weeks})

    if resp and resp.ok:
        data = resp.json()
        if data["dates"]:
            df = pd.DataFrame(
                {
                    "Date": pd.to_datetime(data["dates"]),
                    "Calories": data["daily_kcal"],
                    "Protein (g)": data["daily_proteins"],
                    "Carbs (g)": data["daily_carbs"],
                    "Fat (g)": data["daily_fat"],
                    "7-day Avg": data["moving_avg_kcal"],
                }
            )

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["Date"], y=df["Calories"], name="Daily Calories", marker_color="#3498db"))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["7-day Avg"], name="7-day Avg", line=dict(color="#e74c3c", width=3)))
            fig.add_hline(y=2000, line_dash="dash", annotation_text="RDA (2000 kcal)")
            fig.update_layout(title="Daily Calorie Intake", height=400)
            st.plotly_chart(fig, use_container_width=True)

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["Date"], y=df["Protein (g)"], name="Protein", fill="tozeroy"))
            fig2.add_trace(go.Scatter(x=df["Date"], y=df["Carbs (g)"], name="Carbs", fill="tozeroy"))
            fig2.add_trace(go.Scatter(x=df["Date"], y=df["Fat (g)"], name="Fat", fill="tozeroy"))
            fig2.update_layout(title="Macro Nutrients Over Time", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data available for the selected period.")


def product_comparison_page():
    """Compare 2-3 products side by side."""
    st.header("⚖️ Product Comparison")

    col1, col2, col3 = st.columns(3)
    barcodes = []
    with col1:
        b1 = st.text_input("Product 1 barcode", key="bc1")
        if b1:
            barcodes.append(b1)
    with col2:
        b2 = st.text_input("Product 2 barcode", key="bc2")
        if b2:
            barcodes.append(b2)
    with col3:
        b3 = st.text_input("Product 3 (optional)", key="bc3")
        if b3:
            barcodes.append(b3)

    if len(barcodes) >= 2 and st.button("Compare"):
        products = []
        for bc in barcodes:
            resp = api_request("GET", f"/api/v1/products/{bc}")
            if resp and resp.ok:
                products.append(resp.json())
            else:
                st.warning(f"Product {bc} not found")

        if len(products) >= 2:
            nutrients = ["energy_kcal", "fat_g", "carbohydrates_g", "sugars_g", "proteins_g", "fiber_g", "salt_g"]
            labels = ["Energy (kcal)", "Fat (g)", "Carbs (g)", "Sugars (g)", "Protein (g)", "Fiber (g)", "Salt (g)"]

            comparison_data = {"Nutrient": labels}
            for p in products:
                name = (p.get("product_name") or "Unknown")[:30]
                comparison_data[name] = [p.get(n, "N/A") for n in nutrients]

            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

            fig = go.Figure()
            for p in products:
                name = (p.get("product_name") or "Unknown")[:30]
                values = [float(p.get(n, 0) or 0) for n in nutrients]
                fig.add_trace(go.Scatterpolar(r=values, theta=labels, name=name, fill="toself"))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=500)
            st.plotly_chart(fig, use_container_width=True)


def alternatives_page():
    """Find healthier alternatives."""
    st.header("🥦 Healthier Alternatives")
    barcode = st.text_input("Enter product barcode to find healthier alternatives")

    if barcode:
        resp = api_request("GET", f"/api/v1/products/{barcode}")
        if resp and resp.ok:
            product = resp.json()
            st.subheader(f"Original: {product.get('product_name', 'Unknown')}")
            st.write(f"Nutri-Score: **{product.get('nutriscore_grade', 'N/A')}** | NOVA: **{product.get('nova_group', 'N/A')}**")

            alt_resp = api_request("GET", f"/api/v1/products/{barcode}/alternatives", params={"limit": 5})
            if alt_resp and alt_resp.ok:
                alternatives = alt_resp.json()
                if alternatives:
                    st.subheader("Better alternatives:")
                    for alt in alternatives:
                        p = alt["product"]
                        cols = st.columns([3, 1, 1, 1])
                        cols[0].write(f"**{p.get('product_name', 'Unknown')}**")
                        cols[1].write(f"Nutri-Score: {p.get('nutriscore_grade', 'N/A')}")
                        cols[2].write(f"{p.get('energy_kcal', 'N/A')} kcal")
                        cols[3].write(f"({alt.get('nutriscore_improvement', '')})")
                else:
                    st.info("No healthier alternatives found in the same category.")
        elif resp and resp.status_code == 404:
            st.warning("Product not found")


# ==============================================================
# Nutritionist pages (nutritionist + admin)
# ==============================================================


def nutritionist_dashboard_page():
    """Nutritionist dashboard: aggregated view of all patients."""
    st.header("👩‍⚕️ Nutritionist Dashboard")
    st.caption("Aggregated view of all patients — only visible to nutritionist and admin roles")

    resp = api_request("GET", "/api/v1/nutritionist/users")
    if resp and resp.ok:
        users = resp.json()
        if not users:
            st.info("No patients found.")
            return

        # KPI row
        col1, col2, col3, col4 = st.columns(4)
        active_users = [u for u in users if u["is_active"]]
        total_meals = sum(u["total_meals"] for u in users)
        avg_kcal = sum(u["avg_daily_kcal"] for u in users if u["total_meals"] > 0)
        active_with_meals = len([u for u in users if u["total_meals"] > 0])

        col1.metric("Total Patients", len(users))
        col2.metric("Active Patients", len(active_users))
        col3.metric("Total Meals Logged", total_meals)
        col4.metric("Avg Daily kcal", f"{avg_kcal / max(active_with_meals, 1):.0f}")

        st.divider()

        # Patient table
        st.subheader("Patient Overview")
        df = pd.DataFrame(users)
        display_cols = ["username", "role", "activity_level", "dietary_goal", "is_active", "total_meals", "total_kcal", "avg_daily_kcal"]
        available = [c for c in display_cols if c in df.columns]
        st.dataframe(
            df[available].style.format({"total_kcal": "{:.0f}", "avg_daily_kcal": "{:.1f}"}),
            use_container_width=True,
            height=400,
        )

        st.divider()

        # Charts
        col_l, col_r = st.columns(2)

        with col_l:
            st.subheader("Meals per Patient")
            df_meals = df[df["total_meals"] > 0].sort_values("total_meals", ascending=True).tail(15)
            if not df_meals.empty:
                fig = px.bar(df_meals, x="total_meals", y="username", orientation="h", color="total_meals", color_continuous_scale="Greens")
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.subheader("Avg Daily kcal by Patient")
            df_kcal = df[df["avg_daily_kcal"] > 0].sort_values("avg_daily_kcal", ascending=True).tail(15)
            if not df_kcal.empty:
                fig = px.bar(df_kcal, x="avg_daily_kcal", y="username", orientation="h", color="avg_daily_kcal", color_continuous_scale="RdYlGn_r")
                fig.add_vline(x=2000, line_dash="dash", annotation_text="RDA")
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Dietary goal distribution
        st.subheader("Patient Distribution")
        col_l2, col_r2 = st.columns(2)
        with col_l2:
            if "dietary_goal" in df.columns:
                fig = px.pie(df, names="dietary_goal", title="By Dietary Goal", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig, use_container_width=True)
        with col_r2:
            if "activity_level" in df.columns:
                fig = px.pie(df, names="activity_level", title="By Activity Level", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)

    elif resp and resp.status_code == 403:
        st.error("Access denied. Nutritionist or admin role required.")
    else:
        st.warning("Could not load patient data.")


# ==============================================================
# Analyst pages (analyst + admin)
# ==============================================================


def product_analytics_page():
    """Product analytics dashboard with Open Food Facts insights."""
    st.header("📊 Product Analytics")
    st.caption("Market insights from 777K+ French food products — analyst and admin only")

    resp = api_request("GET", "/api/v1/analytics/summary")
    if resp and resp.ok:
        data = resp.json()

        # Data quality KPIs
        dq = data["data_quality"]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Products", f"{dq['total_products']:,}")
        col2.metric("With Nutri-Score", f"{dq['nutriscore_pct']:.0f}%")
        col3.metric("With NOVA", f"{dq['nova_pct']:.0f}%")
        col4.metric("With Energy", f"{dq['energy_pct']:.0f}%")
        col5.metric("Avg Completeness", f"{dq['avg_completeness']:.1%}" if dq["avg_completeness"] else "N/A")

        st.divider()

        # Nutri-Score and NOVA distribution
        col_l, col_r = st.columns(2)

        with col_l:
            st.subheader("Nutri-Score Distribution")
            ns = data["nutriscore_distribution"]
            if ns:
                df_ns = pd.DataFrame(ns)
                colors = {"A": "#038141", "B": "#85BB2F", "C": "#FECB02", "D": "#EE8100", "E": "#E63E11"}
                fig = px.bar(
                    df_ns,
                    x="grade",
                    y="count",
                    color="grade",
                    color_discrete_map=colors,
                    text="percentage",
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(height=400, showlegend=False, xaxis_title="Nutri-Score", yaxis_title="Products")
                st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.subheader("NOVA Processing Groups")
            nova = data["nova_distribution"]
            if nova:
                df_nova = pd.DataFrame(nova)
                fig = px.pie(df_nova, values="count", names="label", hole=0.4, color_discrete_sequence=["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Top categories
        st.subheader("Top 15 Categories by Product Count")
        cats = data["top_categories"]
        if cats:
            df_cat = pd.DataFrame(cats)
            fig = px.bar(
                df_cat,
                x="product_count",
                y="category_name",
                orientation="h",
                color="avg_nutriscore_score",
                color_continuous_scale="RdYlGn_r",
            )
            fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

        # Brand rankings
        st.divider()
        col_l2, col_r2 = st.columns(2)

        with col_l2:
            st.subheader("🏆 Healthiest Brands (lowest Nutri-Score)")
            healthy = data["top_brands_healthy"]
            if healthy:
                df_h = pd.DataFrame(healthy)
                st.dataframe(
                    df_h[["brand_name", "product_count", "avg_nutriscore_score", "avg_nova_group", "best_grade"]],
                    use_container_width=True,
                )

        with col_r2:
            st.subheader("⚠️ Least Healthy Brands (highest Nutri-Score)")
            unhealthy = data["top_brands_unhealthy"]
            if unhealthy:
                df_u = pd.DataFrame(unhealthy)
                st.dataframe(
                    df_u[["brand_name", "product_count", "avg_nutriscore_score", "avg_nova_group", "worst_grade"]],
                    use_container_width=True,
                )

        # Top/bottom products
        st.divider()
        col_l3, col_r3 = st.columns(2)

        with col_l3:
            st.subheader("🥇 Healthiest Products")
            for p in data["healthiest_products"][:5]:
                st.write(f"**{p['product_name']}** — Nutri-Score {p['nutriscore_grade']}, {p.get('energy_kcal', 'N/A')} kcal")

        with col_r3:
            st.subheader("🚨 Least Healthy Products")
            for p in data["least_healthy_products"][:5]:
                st.write(f"**{p['product_name']}** — Nutri-Score {p['nutriscore_grade']}, {p.get('energy_kcal', 'N/A')} kcal")

    elif resp and resp.status_code == 403:
        st.error("Access denied. Analyst or admin role required.")
    else:
        st.warning("Could not load analytics data. Check API connection.")


# ==============================================================
# Main app with role-based navigation
# ==============================================================

# Page definitions with role access
ALL_PAGES = {
    # Pages available to all roles
    "Product Search": {"func": product_search_page, "roles": ["user", "nutritionist", "analyst", "admin"], "icon": "🔍"},
    "Meal Logger": {"func": meal_logger_page, "roles": ["user", "nutritionist", "analyst", "admin"], "icon": "🍽️"},
    "Daily Dashboard": {"func": daily_dashboard_page, "roles": ["user", "nutritionist", "analyst", "admin"], "icon": "📊"},
    "Weekly Trends": {"func": weekly_trends_page, "roles": ["user", "nutritionist", "analyst", "admin"], "icon": "📈"},
    "Product Comparison": {"func": product_comparison_page, "roles": ["user", "nutritionist", "analyst", "admin"], "icon": "⚖️"},
    "Healthier Alternatives": {"func": alternatives_page, "roles": ["user", "nutritionist", "analyst", "admin"], "icon": "🥦"},
    # Nutritionist + admin only
    "Nutritionist Dashboard": {"func": nutritionist_dashboard_page, "roles": ["nutritionist", "admin"], "icon": "👩‍⚕️"},
    # Analyst + admin only
    "Product Analytics": {"func": product_analytics_page, "roles": ["analyst", "admin"], "icon": "📊"},
}


def main():
    if "token" not in st.session_state:
        login_page()
        return

    user = st.session_state.get("user", {})
    role = user.get("role", "user")

    # Filter pages by role
    available_pages = {name: cfg for name, cfg in ALL_PAGES.items() if role in cfg["roles"]}

    # Default home page per role
    home_pages = {
        "nutritionist": "Nutritionist Dashboard",
        "analyst": "Product Analytics",
        "admin": "Nutritionist Dashboard",
        "user": "Product Search",
    }
    default_page = home_pages.get(role, "Product Search")
    default_index = list(available_pages.keys()).index(default_page) if default_page in available_pages else 0

    # Sidebar
    with st.sidebar:
        st.title("🥗 NutriTrack")
        st.write(f"Welcome, **{user.get('username', 'User')}**")

        # Role badge
        role_colors = {"user": "🟢", "nutritionist": "🔵", "analyst": "🟣", "admin": "🔴"}
        st.write(f"{role_colors.get(role, '⚪')} Role: **{role.title()}**")
        st.divider()

        # Navigation with icons — default to role's home page
        page_labels = [f"{cfg['icon']} {name}" for name, cfg in available_pages.items()]
        selected_label = st.radio("Navigate", page_labels, index=default_index)

        # Extract page name from label
        selected_page = selected_label.split(" ", 1)[1] if selected_label else list(available_pages.keys())[0]

        st.divider()
        st.caption(f"Pages: {len(available_pages)} / {len(ALL_PAGES)}")
        if role != "admin":
            hidden = len(ALL_PAGES) - len(available_pages)
            if hidden > 0:
                st.caption(f"({hidden} pages restricted)")

        st.divider()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # Route to selected page
    if selected_page in available_pages:
        available_pages[selected_page]["func"]()


if __name__ == "__main__":
    main()
