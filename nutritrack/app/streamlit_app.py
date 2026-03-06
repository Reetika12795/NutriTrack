"""
NutriTrack - Fitness Nutrition Tracker
Streamlit frontend application
"""

import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
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
                    "POST", "/api/v1/auth/login",
                    json={"username": username, "password": password},
                )
                if resp and resp.status_code == 200:
                    data = resp.json()
                    st.session_state["token"] = data["access_token"]
                    # Fetch user info
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
                        "POST", "/api/v1/auth/register",
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
# Main app pages
# ==============================================================

def product_search_page():
    """Product search and barcode lookup."""
    st.header("Product Search")

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

    # Barcode lookup
    st.divider()
    st.subheader("Barcode Lookup")
    barcode = st.text_input("Enter barcode", placeholder="e.g., 3017620422003")
    if barcode:
        resp = api_request("GET", f"/api/v1/products/{barcode}")
        if resp and resp.ok:
            product = resp.json()
            st.json(product)
        elif resp and resp.status_code == 404:
            st.warning("Product not found")


def meal_logger_page():
    """Log daily meals."""
    st.header("Meal Logger")

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
                "POST", "/api/v1/meals",
                json={
                    "meal_type": meal_type,
                    "meal_date": str(meal_date),
                    "notes": notes,
                    "items": [{"product_id": product_id, "quantity_g": quantity}],
                },
            )
            if resp and resp.status_code == 201:
                st.success("Meal logged successfully!")
                st.json(resp.json())
            elif resp:
                st.error(f"Error: {resp.json().get('detail', 'Unknown error')}")

    # Show recent meals
    st.divider()
    st.subheader("Recent Meals")
    resp = api_request("GET", "/api/v1/meals/", params={"page_size": 10})
    if resp and resp.ok:
        meals = resp.json()
        for meal in meals:
            with st.expander(f"{meal['meal_type'].title()} - {meal['meal_date']}"):
                for item in meal.get("items", []):
                    product_name = item.get("product", {}).get("product_name", "Unknown")
                    st.write(
                        f"- {product_name}: {item['quantity_g']}g "
                        f"({item.get('energy_kcal', 0):.0f} kcal)"
                    )


def daily_dashboard_page():
    """Daily nutrition dashboard."""
    st.header("Daily Dashboard")

    target_date = st.date_input("Select date", value=date.today())

    resp = api_request(
        "GET", "/api/v1/meals/daily-summary",
        params={"target_date": str(target_date)},
    )

    if resp and resp.ok:
        summary = resp.json()

        # KPI metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Calories", f"{summary['total_kcal']:.0f} kcal", delta=f"{summary['total_kcal'] - 2000:.0f} vs RDA")
        with col2:
            st.metric("Protein", f"{summary['total_proteins_g']:.1f} g", delta=f"{summary['total_proteins_g'] - 50:.1f} vs RDA")
        with col3:
            st.metric("Fiber", f"{summary['total_fiber_g']:.1f} g", delta=f"{summary['total_fiber_g'] - 25:.1f} vs RDA")
        with col4:
            st.metric("Meals", summary["meals_count"])

        # Macro breakdown chart
        if summary["total_kcal"] > 0:
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                fig = go.Figure(data=[go.Pie(
                    labels=["Protein", "Carbs", "Fat"],
                    values=[summary["protein_pct"], summary["carbs_pct"], summary["fat_pct"]],
                    marker_colors=["#2ecc71", "#3498db", "#e74c3c"],
                    hole=0.4,
                )])
                fig.update_layout(title="Macro Distribution", height=350)
                st.plotly_chart(fig, use_container_width=True)

            with col_chart2:
                # RDA progress bars
                rda_items = [
                    ("Energy", summary["total_kcal"], 2000, "kcal"),
                    ("Protein", summary["total_proteins_g"], 50, "g"),
                    ("Fat", summary["total_fat_g"], 70, "g"),
                    ("Carbs", summary["total_carbohydrates_g"], 260, "g"),
                    ("Fiber", summary["total_fiber_g"], 25, "g"),
                    ("Salt", summary["total_salt_g"], 6, "g"),
                ]

                for name, value, rda, unit in rda_items:
                    pct = min(value / rda * 100, 100) if rda > 0 else 0
                    st.write(f"**{name}**: {value:.1f} / {rda} {unit} ({pct:.0f}%)")
                    st.progress(pct / 100)
    else:
        st.info("No meals logged for this date. Start by adding meals in the Meal Logger!")


def weekly_trends_page():
    """Weekly nutrition trends."""
    st.header("Weekly Trends")

    weeks = st.slider("Weeks to display", 1, 12, 4)
    resp = api_request("GET", "/api/v1/meals/weekly-trends", params={"weeks": weeks})

    if resp and resp.ok:
        data = resp.json()

        if data["dates"]:
            df = pd.DataFrame({
                "Date": pd.to_datetime(data["dates"]),
                "Calories": data["daily_kcal"],
                "Protein (g)": data["daily_proteins"],
                "Carbs (g)": data["daily_carbs"],
                "Fat (g)": data["daily_fat"],
                "7-day Avg Calories": data["moving_avg_kcal"],
            })

            # Calories chart
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["Date"], y=df["Calories"], name="Daily Calories", marker_color="#3498db"))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["7-day Avg Calories"], name="7-day Moving Avg", line=dict(color="#e74c3c", width=3)))
            fig.add_hline(y=2000, line_dash="dash", annotation_text="RDA (2000 kcal)")
            fig.update_layout(title="Daily Calorie Intake", xaxis_title="Date", yaxis_title="kcal", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Macros chart
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["Date"], y=df["Protein (g)"], name="Protein", fill="tozeroy"))
            fig2.add_trace(go.Scatter(x=df["Date"], y=df["Carbs (g)"], name="Carbs", fill="tozeroy"))
            fig2.add_trace(go.Scatter(x=df["Date"], y=df["Fat (g)"], name="Fat", fill="tozeroy"))
            fig2.update_layout(title="Macro Nutrients Over Time", xaxis_title="Date", yaxis_title="grams", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data available for the selected period.")


def product_comparison_page():
    """Compare 2-3 products side by side."""
    st.header("Product Comparison")

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
        b3 = st.text_input("Product 3 barcode (optional)", key="bc3")
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
            # Comparison table
            nutrients = ["energy_kcal", "fat_g", "saturated_fat_g", "carbohydrates_g",
                        "sugars_g", "proteins_g", "fiber_g", "salt_g"]
            labels = ["Energy (kcal)", "Fat (g)", "Sat. Fat (g)", "Carbs (g)",
                     "Sugars (g)", "Protein (g)", "Fiber (g)", "Salt (g)"]

            comparison_data = {"Nutrient": labels}
            for p in products:
                name = (p.get("product_name") or "Unknown")[:30]
                comparison_data[name] = [p.get(n, "N/A") for n in nutrients]

            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)

            # Radar chart
            fig = go.Figure()
            for p in products:
                name = (p.get("product_name") or "Unknown")[:30]
                values = [float(p.get(n, 0) or 0) for n in nutrients]
                fig.add_trace(go.Scatterpolar(r=values, theta=labels, name=name, fill="toself"))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=500)
            st.plotly_chart(fig, use_container_width=True)


def alternatives_page():
    """Find healthier alternatives."""
    st.header("Healthier Alternatives")

    barcode = st.text_input("Enter product barcode to find healthier alternatives")

    if barcode:
        # Show original product
        resp = api_request("GET", f"/api/v1/products/{barcode}")
        if resp and resp.ok:
            product = resp.json()
            st.subheader(f"Original: {product.get('product_name', 'Unknown')}")
            st.write(f"Nutri-Score: **{product.get('nutriscore_grade', 'N/A')}** | NOVA: **{product.get('nova_group', 'N/A')}**")
            st.write(f"Energy: {product.get('energy_kcal', 'N/A')} kcal/100g")

            # Get alternatives
            alt_resp = api_request("GET", f"/api/v1/products/{barcode}/alternatives", params={"limit": 5})
            if alt_resp and alt_resp.ok:
                alternatives = alt_resp.json()
                if alternatives:
                    st.subheader("Better alternatives:")
                    for alt in alternatives:
                        p = alt["product"]
                        improvement = alt.get("nutriscore_improvement", "")
                        with st.container():
                            cols = st.columns([3, 1, 1, 1])
                            cols[0].write(f"**{p.get('product_name', 'Unknown')}**")
                            cols[1].write(f"Nutri-Score: {p.get('nutriscore_grade', 'N/A')}")
                            cols[2].write(f"{p.get('energy_kcal', 'N/A')} kcal")
                            if improvement:
                                cols[3].write(f"({improvement})")
                else:
                    st.info("No healthier alternatives found in the same category.")
            elif alt_resp:
                st.warning(alt_resp.json().get("detail", "Error finding alternatives"))
        elif resp and resp.status_code == 404:
            st.warning("Product not found")


# ==============================================================
# Main app
# ==============================================================

def main():
    # Check if logged in
    if "token" not in st.session_state:
        login_page()
        return

    user = st.session_state.get("user", {})

    # Sidebar navigation
    with st.sidebar:
        st.title("NutriTrack")
        st.write(f"Welcome, **{user.get('username', 'User')}**")
        st.write(f"Role: {user.get('role', 'user')}")
        st.divider()

        page = st.radio(
            "Navigate",
            [
                "Product Search",
                "Meal Logger",
                "Daily Dashboard",
                "Weekly Trends",
                "Product Comparison",
                "Healthier Alternatives",
            ],
        )

        st.divider()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # Page routing
    pages = {
        "Product Search": product_search_page,
        "Meal Logger": meal_logger_page,
        "Daily Dashboard": daily_dashboard_page,
        "Weekly Trends": weekly_trends_page,
        "Product Comparison": product_comparison_page,
        "Healthier Alternatives": alternatives_page,
    }

    pages[page]()


if __name__ == "__main__":
    main()
