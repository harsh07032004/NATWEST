import os
import pandas as pd
from src.core.schema import base_response
from src.models.utils import load_csv, apply_filters, resolve_secure_path


def descriptive_model(payload):
    """
    Descriptive analysis: What happened?
    Computes totals, breakdowns, trends and chart data from the Superstore dataset.
    """
    response = base_response()

    try:
        blueprint  = payload["data_blueprint"]
        schema     = blueprint["schema_mapping"]

        metric     = schema.get("metric_col", "Sales")
        date_col   = schema.get("date_col", "Order Date")
        dataset_path = blueprint["dataset"]

        # ── Resolve path ────────────────────────────────────────────
        final_path = resolve_secure_path(dataset_path)

        # ── Load & prepare ──────────────────────────────────────────
        df = load_csv(final_path, date_col)

        if df.empty:
            response["summary"] = "Dataset is empty."
            return response

        # Apply any explicit filters from the execution plan
        filters = blueprint.get("execution_scope", {}).get("filters", [])
        df = apply_filters(df, filters)

        # ── Time frame filtering ────────────────────────────────────
        time_frames  = blueprint["execution_scope"]["time_frames"]
        current_tf   = time_frames["current"]
        baseline_tf  = time_frames.get("baseline", None)

        current_df = df[
            (df[date_col] >= current_tf["start"]) &
            (df[date_col] <= current_tf["end"])
        ].copy()

        baseline_df = (
            df[
                (df[date_col] >= baseline_tf["start"]) &
                (df[date_col] <= baseline_tf["end"])
            ]
            if baseline_tf
            else pd.DataFrame(columns=df.columns)
        )

        # ── Key Metrics ─────────────────────────────────────────────
        current_total  = current_df[metric].sum()
        baseline_total = baseline_df[metric].sum() if not baseline_df.empty else 0

        if baseline_total == 0:
            change_pct = 0
            direction  = "stable"
        else:
            change_pct = ((current_total - baseline_total) / baseline_total) * 100
            direction  = "upward" if change_pct > 0 else ("downward" if change_pct < 0 else "stable")

        change_pct = round(change_pct, 2)

        response["key_metrics"] = [
            {"name": "current_sales",   "value": round(float(current_total), 2),  "unit": "USD", "type": "currency"},
            {"name": "baseline_sales",  "value": round(float(baseline_total), 2), "unit": "USD", "type": "currency"},
            {"name": "change_pct",      "value": change_pct,                       "unit": "%",   "type": "percentage"},
        ]

        if baseline_total == 0:
            response["warnings"].append("No baseline data found for the given date range.")
        elif abs(change_pct) > 200:
            response["warnings"].append(
                "Large percentage change detected — may be due to a low baseline value."
            )

        # ── Trend ───────────────────────────────────────────────────
        response["trend"] = {
            "direction":       direction,
            "pattern":         "sharp_change" if abs(change_pct) > 50 else "steady",
            "change_rate":     change_pct,
            "time_granularity": "monthly",
        }

        # ── Monthly time breakdown ──────────────────────────────────
        current_df["month"] = current_df[date_col].dt.to_period("M").astype(str)
        monthly = (
            current_df.groupby("month")[metric]
            .sum()
            .reset_index()
            .sort_values("month")
        )
        response["breakdown"]["time"] = [
            {"label": row["month"], "value": round(float(row[metric]), 2)}
            for _, row in monthly.iterrows()
        ]

        # ── Category breakdown ──────────────────────────────────────
        total = current_total if current_total != 0 else 1
        if "Category" in current_df.columns:
            cat_group = (
                current_df.groupby("Category")[metric]
                .sum()
                .reset_index()
                .sort_values(metric, ascending=False)
            )
            response["breakdown"]["category"] = [
                {
                    "label":      row["Category"],
                    "value":      round(float(row[metric]), 2),
                    "percentage": round((row[metric] / total) * 100, 2),
                }
                for _, row in cat_group.iterrows()
            ]

        # ── Sub-Category / Merchant breakdown ───────────────────────
        if "Sub-Category" in current_df.columns:
            subcat_group = (
                current_df.groupby("Sub-Category")[metric]
                .sum()
                .reset_index()
                .sort_values(metric, ascending=False)
                .head(10)
            )
            response["breakdown"]["merchant"] = [
                {"label": row["Sub-Category"], "value": round(float(row[metric]), 2)}
                for _, row in subcat_group.iterrows()
            ]

        # ── Region / Segment breakdown ──────────────────────────────
        for dim_col, dim_key in [("Region", "region"), ("Segment", "segment")]:
            if dim_col in current_df.columns:
                grp = (
                    current_df.groupby(dim_col)[metric]
                    .sum()
                    .reset_index()
                    .sort_values(metric, ascending=False)
                )
                response["breakdown"][dim_key] = [
                    {
                        "label":      row[dim_col],
                        "value":      round(float(row[metric]), 2),
                        "percentage": round((row[metric] / total) * 100, 2),
                    }
                    for _, row in grp.iterrows()
                ]

        # ── Chart data ──────────────────────────────────────────────
        response["chart_data"] = [
            {
                "chart_id":   "monthly_sales_trend",
                "chart_type": "line",
                "title":      "Monthly Sales Trend",
                "x_axis":     [r["label"] for r in response["breakdown"]["time"]],
                "series":     [{"name": "Sales", "values": [r["value"] for r in response["breakdown"]["time"]]}],
            },
            {
                "chart_id":   "category_breakdown",
                "chart_type": "bar",
                "title":      "Sales by Category",
                "x_axis":     [r["label"] for r in response["breakdown"]["category"]],
                "series":     [{"name": "Sales", "values": [r["value"] for r in response["breakdown"]["category"]]}],
            },
        ]

        # ── Recommendations ─────────────────────────────────────────
        recommendations = []
        for cat in response["breakdown"]["category"][:2]:
            recommendations.append({
                "action":   f"Focus on growing {cat['label']} ({cat['percentage']}% of sales)",
                "priority": "high" if cat["percentage"] > 40 else "medium",
                "reason":   f"{cat['label']} is a top revenue category",
            })
        response["recommendations"] = recommendations

        # ── Summary delegated to LLM ────────────────────────────────
        response["summary"] = ""
        response["summary_levels"] = {"simple": "", "medium": "", "advanced": ""}
        response["confidence"] = 0.92
        return response

    except Exception as e:
        response["status"]  = "error"
        response["message"] = str(e)
        return response