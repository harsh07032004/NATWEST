import os
import pandas as pd
from src.core.schema import base_response
from src.models.utils import load_csv, apply_filters


def diagnostic_model(payload):
    """
    Diagnostic analysis: Why did it happen?
    Performs root-cause analysis and anomaly detection on the Superstore dataset.
    """
    response = base_response()

    try:
        blueprint  = payload["data_blueprint"]
        schema     = blueprint["schema_mapping"]

        metric     = schema.get("metric_col", "Sales")
        date_col   = schema.get("date_col", "Order Date")
        dataset_path = blueprint["dataset"]
        dimensions = schema.get("dimension_cols", ["Category", "Sub-Category", "Region"])

        # ── Resolve path ────────────────────────────────────────────
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        final_path = os.path.join(project_root, dataset_path)
        if not os.path.exists(final_path):
            final_path = os.path.join(project_root, "data", dataset_path)

        # ── Load & prepare ──────────────────────────────────────────
        df = load_csv(final_path, date_col)

        if df.empty:
            response["summary"] = "Dataset is empty."
            return response

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

        change_pct = (
            round(((current_total - baseline_total) / baseline_total) * 100, 2)
            if baseline_total != 0 else 0
        )
        direction = "upward" if change_pct > 0 else ("downward" if change_pct < 0 else "stable")

        response["key_metrics"] = [
            {"name": "current_sales",  "value": round(float(current_total), 2),  "unit": "USD"},
            {"name": "baseline_sales", "value": round(float(baseline_total), 2), "unit": "USD"},
            {"name": "change_pct",     "value": change_pct,                       "unit": "%"},
        ]

        response["trend"] = {
            "direction": direction,
            "pattern":   "diagnostic_based",
            "change_rate": change_pct,
        }

        if abs(change_pct) > 200:
            response["warnings"].append(
                "Significant percentage change detected — interpret with caution due to low baseline."
            )

        # ── Root Cause Analysis ─────────────────────────────────────
        causes = []

        if not baseline_df.empty:
            for col in dimensions:
                if col not in current_df.columns:
                    continue

                cur_grp  = current_df.groupby(col)[metric].sum().reset_index()
                base_grp = baseline_df.groupby(col)[metric].sum().reset_index()

                merged = pd.merge(cur_grp, base_grp, on=col, how="left",
                                  suffixes=("_cur", "_base"))
                merged[f"{metric}_base"] = merged[f"{metric}_base"].fillna(0)
                merged["delta"] = merged[f"{metric}_cur"] - merged[f"{metric}_base"]
                merged = merged.sort_values("delta", ascending=False)

                total_delta = merged["delta"].abs().sum() or 1

                for _, row in merged.head(3).iterrows():
                    if abs(row["delta"]) < 1:
                        continue
                    causes.append({
                        "cause":            str(row[col]),
                        "dimension":        col,
                        "impact":           "high" if abs(row["delta"]) > 0.3 * abs(current_total) else "medium",
                        "contribution_pct": round((abs(row["delta"]) / total_delta) * 100, 2),
                        "direction":        "increase" if row["delta"] > 0 else "decrease",
                        "evidence":         f"{row[col]} contributed ${round(float(row['delta']), 2)} change",
                    })

        # Deduplicate causes by cause label
        seen = set()
        unique_causes = []
        for c in causes:
            key = c["cause"]
            if key not in seen:
                seen.add(key)
                unique_causes.append(c)

        response["diagnostics"]["causes"] = unique_causes

        # ── Anomaly Detection ───────────────────────────────────────
        anomalies = []
        if payload.get("computation_tasks", {}).get("run_anomaly_detection", False):
            mean = current_df[metric].mean()
            std  = current_df[metric].std() or 1
            threshold = mean + 2 * std

            anomaly_rows = current_df[current_df[metric] > threshold]
            for _, row in anomaly_rows.iterrows():
                anomalies.append({
                    "label":    row.get("Product Name", row.get("Sub-Category", "Unknown")),
                    "category": row.get("Category", ""),
                    "value":    round(float(row[metric]), 2),
                    "date":     str(row[date_col].date()),
                    "severity": "high" if row[metric] > mean + 3 * std else "medium",
                })

        response["diagnostics"]["anomalies"] = anomalies

        response["summary"]        = ""
        response["summary_levels"] = {"simple": "", "medium": "", "advanced": ""}
        response["confidence"]     = 0.92
        return response

    except Exception as e:
        response["status"]  = "error"
        response["message"] = str(e)
        return response