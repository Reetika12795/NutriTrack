# NutriTrack Demo Credentials & Services

## Demo Accounts

| Account          | Username           | Password      | Role           | Access                                                                 |
|------------------|--------------------|---------------|----------------|------------------------------------------------------------------------|
| Regular User     | `reetika`          | `user123demo` | `user`         | 6 pages: Product Search, Meal Logger, Daily Dashboard, Weekly Trends, Product Comparison, Healthier Alternatives |
| Test User        | `user_1` to `user_50` | `user123demo` | `user`      | Same as regular user (50 test accounts with meal history)              |
| Nutritionist     | `dr_martin`        | `user123demo` | `nutritionist` | Nutritionist Dashboard (home) + 6 user pages                           |
| Analyst          | `analyst_sophie`   | `user123demo` | `analyst`      | Product Analytics (home) + 6 user pages + Data Catalog                 |
| Admin            | `admin_nutritrack` | `user123demo` | `admin`        | Nutritionist Dashboard + Product Analytics (home) + 6 user pages + Data Catalog |

## Role-Based Access Summary

| Feature                | user | nutritionist | analyst | admin |
|------------------------|------|--------------|---------|-------|
| Product Search         | Yes  | Yes          | Yes     | Yes   |
| Meal Logger            | Yes  | Yes          | Yes     | Yes   |
| Daily Dashboard        | Yes  | Yes          | Yes     | Yes   |
| Weekly Trends          | Yes  | Yes          | Yes     | Yes   |
| Product Comparison     | Yes  | Yes          | Yes     | Yes   |
| Healthier Alternatives | Yes  | Yes          | Yes     | Yes   |
| Nutritionist Dashboard | No   | Yes (home)   | No      | Yes   |
| Product Analytics      | No   | No           | Yes (home) | Yes |
| Data Catalog (MinIO)   | No   | No           | Yes     | Yes   |
| Delete Users           | No   | Yes          | No      | Yes   |

## Service URLs

| Service              | URL                        | Credentials (if any)          |
|----------------------|----------------------------|-------------------------------|
| Streamlit App        | http://localhost:8501       | See demo accounts above       |
| FastAPI Swagger Docs | http://localhost:8000/docs  | JWT Bearer token from login   |
| FastAPI ReDoc        | http://localhost:8000/redoc | —                             |
| Airflow              | http://localhost:8080       | admin / admin                 |
| MinIO Console        | http://localhost:9001       | minioadmin / minioadmin123    |
| Grafana              | http://localhost:3000       | admin / admin                 |
| Superset             | http://localhost:8088       | admin / admin                 |
| Prometheus           | http://localhost:9090       | —                             |
| MailHog (SMTP UI)    | http://localhost:8025       | —                             |
| cAdvisor             | http://localhost:8081       | —                             |

## Database Access

```bash
# Connect to PostgreSQL via Docker (no psql needed on host)
docker exec nutritrack-postgres-1 psql -U nutritrack -d nutritrack

# Quick user check
docker exec nutritrack-postgres-1 psql -U nutritrack -d nutritrack \
  -c "SELECT username, role FROM app.users WHERE role != 'user';"
```

- **Host**: localhost:5432
- **Database**: nutritrack
- **User**: nutritrack
- **Password**: nutritrack
- **Schemas**: `app` (operational), `dw` (data warehouse)

## Platform Stats (as of 2026-04-02)

- 53 registered users (51 user, 1 nutritionist, 1 admin)
- 50,553 products (from Open Food Facts)
- 9,244 meal records across 50 test users
- MinIO buckets: bronze, silver, gold, backups

## API Endpoints

| Method | Endpoint                                | Auth     | Role Required        |
|--------|-----------------------------------------|----------|----------------------|
| POST   | `/api/v1/auth/register`                 | No       | —                    |
| POST   | `/api/v1/auth/login`                    | No       | —                    |
| GET    | `/api/v1/auth/me`                       | Yes      | any                  |
| GET    | `/api/v1/products/`                     | Yes      | any                  |
| GET    | `/api/v1/products/{barcode}`            | Yes      | any                  |
| GET    | `/api/v1/products/{barcode}/alternatives` | Yes    | any                  |
| POST   | `/api/v1/meals`                         | Yes      | any                  |
| GET    | `/api/v1/meals/`                        | Yes      | any                  |
| GET    | `/api/v1/meals/daily-summary`           | Yes      | any                  |
| GET    | `/api/v1/meals/weekly-trends`           | Yes      | any                  |
| GET    | `/api/v1/nutritionist/users`            | Yes      | nutritionist, admin  |

## Sample Barcodes for Demo

The product database contains 50,000+ French products from Open Food Facts. US barcodes will NOT work.

### Product Search (search terms that return good results)

| Search Term  | Results | Notes                          |
|--------------|---------|--------------------------------|
| `chocolat`   | ~1,900  | Wide range of Nutri-Scores     |
| `yaourt`     | ~800    | Dairy products, mostly A/B     |
| `pomme`      | ~500    | Fruits, juices, desserts       |
| `biscuit`    | ~400    | Snacks, mostly D/E             |
| `fromage`    | ~700    | Cheeses, varied scores         |
| `poulet`     | ~300    | Meats, mostly A/B              |

### Healthier Alternatives (use D/E products to see alternatives)

| Barcode         | Product                      | Score | Alternatives |
|-----------------|------------------------------|-------|--------------|
| `3760121210616` | Chocolat lait 41%            | E     | 5+ found     |
| `3560071018528` | Royal Chocolat praline       | E     | 5+ found     |
| `3760226260431` | Tablette chocolat 75% cacao  | E     | 5+ found     |
| `3250391686698` | Olives vertes picholines     | E     | 5+ found     |
| `3760121212429` | Cookie chocolat noisette     | E     | 5+ found     |

### Product Comparison (use 2-3 barcodes side by side)

**Pair 1: Snacks (E vs A)**
- `3760121210616` - Chocolat lait 41% (E, 582 kcal)
- `3263851321510` - Barres cerealieres (A, 94 kcal)

**Pair 2: Dairy (A vs B)**
- `5054402745989` - 0% Fat Greek Yoghurt (A, 65 kcal)
- `3410280020822` - 12 Yaourts sucres aromatises (B, 70 kcal)

**Pair 3: Chocolate (E vs E, compare nutrition)**
- `3760121210616` - Chocolat lait 41% (E, 582 kcal)
- `3760226260431` - Tablette chocolat 75% cacao (E)

### Meal Logger (product IDs to log meals)

Search for a product first, note its `product_id`, then use it in the Meal Logger.
Or use these known product IDs:

| product_id | Product                           | Score | Good for        |
|------------|-----------------------------------|-------|-----------------|
| 3480       | Tartine craquante sarrasin        | A     | Breakfast       |
| 3485       | Yaourt nature entier              | B     | Snack           |
| 3481       | Chocolat noir 100% cacao          | D     | Dessert/Snack   |
| 3491       | Quinoa France                     | A     | Lunch/Dinner    |

### Weekly Trends Tip

Test user meals range from **2025-12-07 to 2026-03-06**. Set the weeks slider to **8-12 weeks** to see data. Login as `user_13` (189 meals) for the best charts.

### Users with Most Meal Data

| Username  | Meals | Best for demo                    |
|-----------|-------|----------------------------------|
| `user_11` | 195   | Richest meal history             |
| `user_13` | 189   | Good variety of meal types       |
| `user_8`  | 193   | High meal count                  |
| `reetika` | 0     | Empty - use for live meal logging |

## Starting the Platform

```bash
cd /Users/reegauta/Documents/Simplon/nutritrack

# Start everything
docker compose up -d

# Or rebuild if code changed
docker compose up -d --build fastapi streamlit

# Check all services
docker compose ps

# View logs
docker compose logs -f fastapi streamlit
```
