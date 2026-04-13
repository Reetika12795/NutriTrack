"""
NutriTrack Data Catalog Browser (C20 - Data Catalog Management)

Interactive Streamlit page that connects to MinIO, reads the
_catalog/metadata.json from each bucket, and presents datasets
in a searchable, browsable format with lineage, quality metrics,
governance info, and storage statistics.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import streamlit as st

# ---------------------------------------------------------------------------
# MinIO connection
# ---------------------------------------------------------------------------

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

CATALOG_BUCKETS = ["bronze", "silver", "gold", "backups"]


@st.cache_resource
def _get_minio_client():
    """Return a cached MinIO client instance."""
    from minio import Minio

    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def _read_catalog(client, bucket: str) -> dict | None:
    """Read _catalog/metadata.json from a bucket, return parsed dict or None."""
    try:
        response = client.get_object(bucket, "_catalog/metadata.json")
        data = json.loads(response.read().decode("utf-8"))
        response.close()
        response.release_conn()
        return data
    except Exception:
        return None


def _bucket_stats(client, bucket: str) -> dict:
    """Compute object count and total size for a bucket."""
    total_size = 0
    object_count = 0
    try:
        for obj in client.list_objects(bucket, recursive=True):
            if not obj.is_dir:
                object_count += 1
                total_size += obj.size or 0
    except Exception:
        pass
    return {"object_count": object_count, "total_size_bytes": total_size}


def _format_bytes(size_bytes: int) -> str:
    """Human-readable byte size."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    size = float(size_bytes)
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    return f"{size:.1f} {units[idx]}"


def _matches_search(text: str, query: str) -> bool:
    """Case-insensitive substring match."""
    return query.lower() in text.lower()


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Data Catalog", page_icon="", layout="wide")

# Role check: only analyst and admin can access the data catalog
user = st.session_state.get("user", {})
role = user.get("role", "")
if role not in ("analyst", "admin"):
    st.error("Access denied. This page is restricted to **analyst** and **admin** roles.")
    st.info("Please log in with an authorized account to view the data catalog.")
    st.stop()

st.title("Data Catalog Browser")
st.caption("C20 - Interactive data catalog for the NutriTrack data lake (MinIO)")

# -- Connection check -------------------------------------------------------
try:
    client = _get_minio_client()
    # Quick connectivity test
    client.list_buckets()
    connected = True
except Exception as exc:
    connected = False
    st.error(f"Cannot connect to MinIO at {MINIO_ENDPOINT}: {exc}")

if not connected:
    st.stop()

# -- Search bar -------------------------------------------------------------
search_query = st.text_input(
    "Search datasets",
    placeholder="Filter by dataset name, description, or format ...",
)

# -- Bucket tabs ------------------------------------------------------------
existing_buckets = [b for b in CATALOG_BUCKETS if client.bucket_exists(b)]

if not existing_buckets:
    st.warning("No buckets found in MinIO.")
    st.stop()

tabs = st.tabs([b.upper() for b in existing_buckets])

for tab, bucket_name in zip(tabs, existing_buckets):
    with tab:
        # -- Storage statistics -------------------------------------------------
        stats = _bucket_stats(client, bucket_name)
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Bucket", bucket_name)
        col_s2.metric("Objects", f"{stats['object_count']:,}")
        col_s3.metric("Total Size", _format_bytes(stats["total_size_bytes"]))

        st.divider()

        # -- Catalog metadata ---------------------------------------------------
        catalog = _read_catalog(client, bucket_name)
        if catalog is None:
            st.info(f"No _catalog/metadata.json found in **{bucket_name}** bucket.")
            continue

        # Show last-updated timestamp
        last_updated = catalog.get("last_updated", "unknown")
        st.caption(f"Catalog last updated: **{last_updated}**")

        # -- Architecture overview (shown once in the first bucket) -------------
        arch = catalog.get("architecture")
        if arch:
            with st.expander("Architecture Overview", expanded=False):
                st.markdown(f"**Principle:** {arch.get('principle', 'N/A')}")
                col_a1, col_a2 = st.columns(2)
                dw = arch.get("data_warehouse", {})
                dl = arch.get("data_lake", {})
                with col_a1:
                    st.subheader("Data Warehouse")
                    for k, v in dw.items():
                        st.markdown(f"- **{k}**: {v}")
                with col_a2:
                    st.subheader("Data Lake")
                    for k, v in dl.items():
                        st.markdown(f"- **{k}**: {v}")

        # -- Datasets -----------------------------------------------------------
        datasets = catalog.get("datasets", {})
        if not datasets:
            st.info("No datasets listed in catalog metadata.")
            continue

        # Filter datasets belonging to this bucket
        bucket_datasets = {name: meta for name, meta in datasets.items() if name.startswith(f"{bucket_name}/")}

        # Apply search filter
        if search_query:
            bucket_datasets = {
                name: meta
                for name, meta in bucket_datasets.items()
                if _matches_search(name, search_query)
                or _matches_search(meta.get("description", ""), search_query)
                or _matches_search(meta.get("format", ""), search_query)
                or _matches_search(meta.get("source", ""), search_query)
            }

        if not bucket_datasets:
            if search_query:
                st.info(f'No datasets matching "{search_query}" in {bucket_name}.')
            else:
                st.info(f"No datasets cataloged for the {bucket_name} layer.")
            continue

        st.subheader(f"Datasets ({len(bucket_datasets)})")

        for ds_name, ds_meta in sorted(bucket_datasets.items()):
            description = ds_meta.get("description", "No description")
            fmt = ds_meta.get("format", "N/A")
            freq = ds_meta.get("update_frequency", "N/A")

            with st.expander(f"{ds_name}  |  {fmt}  |  {freq}", expanded=False):
                # ---- Basic info ----
                st.markdown(f"**Description:** {description}")
                st.markdown(f"**Format:** {fmt}")
                st.markdown(f"**Update frequency:** {freq}")

                if ds_meta.get("source"):
                    st.markdown(f"**Source:** {ds_meta['source']}")
                if ds_meta.get("owner"):
                    st.markdown(f"**Owner:** {ds_meta['owner']}")

                # ---- Schema ----
                schema = ds_meta.get("schema")
                if schema:
                    st.markdown("---")
                    st.markdown("**Schema**")
                    if isinstance(schema, str):
                        st.code(schema, language="text")
                    elif isinstance(schema, dict):
                        import pandas as pd

                        schema_df = pd.DataFrame([{"Column": col, "Type": dtype} for col, dtype in schema.items()])
                        st.dataframe(schema_df, use_container_width=True, hide_index=True)
                    elif isinstance(schema, list):
                        import pandas as pd

                        st.dataframe(
                            pd.DataFrame(schema),
                            use_container_width=True,
                            hide_index=True,
                        )

                # ---- Lineage ----
                lineage = ds_meta.get("lineage")
                if lineage:
                    st.markdown("---")
                    st.markdown("**Lineage (data sources)**")
                    if isinstance(lineage, list):
                        for src in lineage:
                            st.markdown(f"- {src}")
                    elif isinstance(lineage, str):
                        st.markdown(lineage)

                # ---- Quality ----
                quality = ds_meta.get("quality")
                if quality:
                    st.markdown("---")
                    st.markdown(f"**Quality:** {quality}")

                # ---- Purpose ----
                purpose = ds_meta.get("purpose")
                if purpose:
                    st.markdown(f"**Purpose:** {purpose}")

                # ---- Why not in DW ----
                why = ds_meta.get("why_not_in_dw")
                if why:
                    st.markdown("---")
                    st.info(f"Why this is in the Lake (not the DW): {why}")

                # ---- Consumers ----
                consumers = ds_meta.get("consumers")
                if consumers:
                    st.markdown("---")
                    st.markdown("**Consumers:**")
                    if isinstance(consumers, list):
                        for c in consumers:
                            st.markdown(f"- {c}")
                    else:
                        st.markdown(str(consumers))

        # -- Governance section -------------------------------------------------
        governance = catalog.get("governance")
        if governance:
            with st.expander("Governance & RGPD", expanded=False):
                # RGPD compliance
                rgpd = governance.get("rgpd_compliance")
                if rgpd is not None:
                    st.markdown(f"**RGPD Compliant:** {'Yes' if rgpd else 'No'}")

                personal = governance.get("personal_data_datasets")
                if personal:
                    st.markdown("**Personal Data:**")
                    if isinstance(personal, list):
                        for item in personal:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(str(personal))

                # Retention policy
                retention = governance.get("retention_policy")
                if retention and isinstance(retention, dict):
                    st.markdown("---")
                    st.markdown("**Retention Policy:**")
                    import pandas as pd

                    ret_df = pd.DataFrame(
                        [{"Layer": layer, "Retention": period} for layer, period in retention.items()]
                    )
                    st.dataframe(ret_df, use_container_width=True, hide_index=True)

                # Access groups
                access = governance.get("access_groups")
                if access and isinstance(access, dict):
                    st.markdown("---")
                    st.markdown("**Access Groups (C21 - Governance):**")
                    for group, permissions in access.items():
                        perms_text = ", ".join(permissions) if isinstance(permissions, list) else str(permissions)
                        st.markdown(f"- **{group}**: {perms_text}")

# -- Global lineage diagram -------------------------------------------------
st.divider()
st.subheader("Data Lineage Overview")

# Try to read lineage from the gold bucket catalog (most complete)
gold_catalog = _read_catalog(client, "gold") if "gold" in existing_buckets else None
if gold_catalog is None and existing_buckets:
    gold_catalog = _read_catalog(client, existing_buckets[0])

if gold_catalog:
    lineage_info = gold_catalog.get("lineage", {})
    if lineage_info and isinstance(lineage_info, dict):
        st.markdown("**ETL Lineage Map:**")
        for flow, desc in lineage_info.items():
            st.markdown(f"- **{flow}**: {desc}")
    else:
        st.info("No lineage information available in the catalog.")

    # Architecture principle summary
    arch_info = gold_catalog.get("architecture", {})
    if arch_info:
        st.caption(f"Architecture principle: {arch_info.get('principle', 'N/A')}")
else:
    st.info("No catalog metadata available to show lineage.")

# -- Footer -----------------------------------------------------------------
st.divider()
st.caption(
    f"Data Catalog Browser | Connected to MinIO at {MINIO_ENDPOINT} | "
    f"Page loaded at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
)
