import os
import pandas as pd
from src.core.schema import base_response
from src.models.utils import load_csv, apply_filters


def comparative_model(payload):
    """
    Comparative analysis: How do segments/categories/regions compare?
    Groups Superstore data by a user-specified dimension and ranks them.
    """
    response = base_response()

    try:
        blueprint       = payload["data_blueprint"]
        schema          = blueprint["schema_mapping"]
        metric          = schema.get("metric_col", "Sales")
        date_col        = schema.get("date_col", "Order Date")
        dataset_path    = blueprint["dataset"]
        comparison_type = payload["analytical_intent"].get("comparison_type", "Category")

        # ── Resolve path ────────────────────────────────────────────
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        final_path = os.path.join(project_root, dataset_path)
        if not os.path.exists(final_path):
            final_path = os.path.join(project_root, "data", dataset_path)

        # ── Load & prepare ──────────────────────────────────────────
        df = load_csv(final_path, date_col)

        filters = blueprint.get("execution_scope", {}).get("filters", [])
        df = apply_filters(df, filters)

        # ── Time frame filtering ────────────────────────────────────
        current_tf = blueprint["execution_scope"]["time_frames"]["current"]
        current_df = df[
            (df[date_col] >= current_tf["start"]) &
            (df[date_col] <= current_tf["end"])
        ].copy()

        # ── Pick comparison column ──────────────────────────────────
        # Accept user-specified column or fall back to Category
        available_dims = ["Category", "Sub-Category", "Segment", "Region", "Ship Mode", "State"]
        col = (
            comparison_type
            if comparison_type in current_df.columns
            else next((d for d in available_dims if d in current_df.columns), "Category")
        )

        # ── Group & rank ────────────────────────────────────────────
        grouped = (
            current_df.groupby(col)[metric]
            .sum()
            .reset_index()
            .sort_values(metric, ascending=False)
        )
        total = grouped[metric].sum() or 1

        response["breakdown"]["category"] = [
            {
                "label":      str(row[col]),
                "value":      round(float(row[metric]), 2),
                "percentage": round((row[metric] / total) * 100, 2),
            }
            for _, row in grouped.iterrows()
        ]

        # ── Top-2 comparison ─────────────────────────────────────────
        top = response["breakdown"]["category"]
        if len(top) < 2:
            response["summary"] = "Not enough groups for comparison."
            return response

        val1     = top[0]["value"]
        val2     = top[1]["value"]
        diff_pct = round(((val1 - val2) / val2) * 100, 2) if val2 != 0 else 0

        response["comparison"] = {
            "dimension":      col,
            "items":          [{"label": top[0]["label"], "value": val1},
                               {"label": top[1]["label"], "value": val2}],
            "winner":         top[0]["label"],
            "difference_pct": diff_pct,
        }

        # ── Key Metrics ─────────────────────────────────────────────
        response["key_metrics"] = [
            {"name": "total_sales",     "value": round(float(total), 2),    "unit": "USD", "type": "currency"},
            {"name": "top_group_sales", "value": val1,                       "unit": "USD", "type": "currency"},
            {"name": "top_group_share", "value": top[0]["percentage"],       "unit": "%",   "type": "percentage"},
        ]

        # ── Trend ───────────────────────────────────────────────────
        response["trend"] = {
            "direction":      "stable",
            "pattern":        "comparison_based",
            "change_rate":    diff_pct,
            "time_granularity": "contextual",
        }

        # ── Chart data ──────────────────────────────────────────────
        response["chart_data"] = [
            {
                "chart_id":   f"{col.lower().replace(' ', '_')}_comparison",
                "chart_type": "bar",
                "title":      f"Sales by {col}",
                "x_axis":     [r["label"] for r in response["breakdown"]["category"]],
                "series":     [{"name": "Sales", "values": [r["value"] for r in response["breakdown"]["category"]]}],
            }
        ]

        response["summary"]        = ""
        response["summary_levels"] = {"simple": "", "medium": "", "advanced": ""}
        response["confidence"]     = 0.90
        response["status"]         = "success"
        return response

    except Exception as e:
        response["status"]  = "error"
        response["message"] = str(e)
        return response