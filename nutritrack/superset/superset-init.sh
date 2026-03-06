#!/bin/bash
set -e

echo "=== Superset initialization ==="

# Upgrade metadata DB schema
superset db upgrade

# Create admin user (idempotent — skips if exists)
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@nutritrack.local \
    --password admin || true

# Initialize Superset (roles, permissions)
superset init

# Register NutriTrack DW datasource (idempotent — updates if exists)
superset set-database-uri \
    --database_name "NutriTrack DW" \
    --uri "postgresql+psycopg2://superset:superset@postgres:5432/nutritrack" \
    || true

# =============================================================
# RBAC: Create custom roles and users (C14, C21)
# =============================================================
echo "=== Configuring RBAC roles and users ==="

python3 -c "
from superset.app import create_app
app = create_app()
with app.app_context():
    from superset.extensions import security_manager, db
    sm = security_manager
    session = db.session

    # --- Create roles ---
    gamma = sm.find_role('Gamma')
    sql_lab = sm.find_role('sql_lab')

    for role_name in ['Analyst', 'Nutritionist']:
        role = sm.find_role(role_name)
        if role is None:
            role = sm.add_role(role_name)
            print(f'Created role: {role_name}')
        else:
            print(f'Role already exists: {role_name}')

        # Copy Gamma permissions (read-only dashboard viewer)
        if gamma:
            existing = set(pv.id for pv in role.permissions)
            for pv in gamma.permissions:
                if pv.id not in existing:
                    role.permissions.append(pv)

    # Give Analyst SQL Lab access
    analyst = sm.find_role('Analyst')
    if analyst and sql_lab:
        existing = set(pv.id for pv in analyst.permissions)
        for pv in sql_lab.permissions:
            if pv.id not in existing:
                analyst.permissions.append(pv)
        print(f'Analyst role: {len(analyst.permissions)} permissions (Gamma + SQL Lab)')

    nutritionist = sm.find_role('Nutritionist')
    if nutritionist:
        print(f'Nutritionist role: {len(nutritionist.permissions)} permissions (Gamma)')

    session.commit()

    # --- Create demo users ---
    users = [
        ('analyst', 'Data', 'Analyst', 'analyst@nutritrack.local', 'analyst', 'Analyst'),
        ('nutritionist', 'Marie', 'Nutritionniste', 'nutritionist@nutritrack.local', 'nutritionist', 'Nutritionist'),
    ]
    for username, first, last, email, password, role_name in users:
        user = sm.find_user(username=username)
        if user is None:
            role = sm.find_role(role_name)
            sm.add_user(username, first, last, email, role, password=password)
            print(f'Created user: {username} (role: {role_name})')
        else:
            print(f'User already exists: {username}')

    session.commit()
    print('RBAC configuration complete')
" || echo "RBAC setup encountered errors (non-fatal)"

echo "=== Superset initialization complete ==="
echo "  admin / admin                -> Full access + SQL Lab"
echo "  analyst / analyst            -> All dashboards + SQL Lab (read-only data)"
echo "  nutritionist / nutritionist  -> Dashboards only (no SQL Lab)"

# Start the webserver
exec superset run -h 0.0.0.0 -p 8088 --with-threads
