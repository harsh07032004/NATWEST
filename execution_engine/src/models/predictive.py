import os
import numpy as np
import pandas as pd
from src.core.schema import base_response
from src.models.utils import load_csv, apply_filters


def predictive_model(payload):
    """
    Predictive analysis: What will happen next?
    Fits a linear trend to monthly Superstore sales and forecasts the next period.
    """
    response = base_response()

    if not payload.get("computation_tasks", {}).get("run_forecasting", False):
        response["prediction"] = {}
        return response

    try:
        blueprint    = payload["data_blueprint"]
        schema       = blueprint["schema_mapping"]
        metric       = schema.get("metric_col", "Sales")
        date_col     = schema.get("date_col", "Order Date")
        dataset_path = blueprint["dataset"]

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

        df = df.sort_values(by=date_col)

        # Aggregate to monthly to smooth noise
        df["month"] = df[date_col].dt.to_period("M")
        monthly = df.groupby("month")[metric].sum().reset_index()
        monthly["t"] = np.arange(len(monthly))

        if monthly.empty:
            response["prediction"] = {}
            response["summary"]    = "No data available for prediction."
            response["confidence"] = 0.0
            return response

        y = monthly[metric].values

        # ── Minimum data guard ──────────────────────────────────────
        if len(monthly) < 3:
            predicted = float(np.mean(y))
            response["prediction"] = {
                "predicted_value": round(predicted, 2),
                "lower_bound":     round(max(0, predicted * 0.9), 2),
                "upper_bound":     round(predicted * 1.1, 2),
                "confidence":      0.5,
                "horizon":         "next month",
            }
            response["confidence"] = 0.5
            return response

        # ── Linear Regression ────────────────────────────────────────
        x = monthly["t"].values
        try:
            a, b = np.polyfit(x, y, 1)
        except Exception:
            predicted = float(np.mean(y))
            response["prediction"] = {
                "predicted_value": round(predicted, 2),
                "lower_bound":     round(max(0, predicted * 0.9), 2),
                "upper_bound":     round(predicted * 1.1, 2),
                "confidence":      0.6,
                "horizon":         "next month",
            }
            response["confidence"] = 0.6
            return response

        next_t    = len(monthly)
        predicted = float(a * next_t + b)

        # ── Confidence interval ─────────────────────────────────────
        std_dev = float(np.std(y))
        lower   = max(0, predicted - std_dev)
        upper   = predicted + std_dev

        # ── Confidence score ─────────────────────────────────────────
        variance = float(np.var(y))
        mean_val = float(np.mean(y))
        if variance < mean_val:
            confidence = 0.90
        elif variance < 2 * mean_val:
            confidence = 0.75
        else:
            confidence = 0.60

        if abs(a) < 0.01:
            confidence -= 0.1   # weak trend penalty

        confidence = round(max(0.50, min(confidence, 0.95)), 2)

        # ── Next period label ─────────────────────────────────────────
        last_period = monthly["month"].iloc[-1]
        next_period = str(last_period + 1)

        response["prediction"] = {
            "predicted_value": round(predicted, 2),
            "lower_bound":     round(lower, 2),
            "upper_bound":     round(upper, 2),
            "confidence":      confidence,
            "horizon":         next_period,
            "trend_slope":     round(float(a), 4),
            "direction":       "increase" if a > 0 else "decrease",
        }

        # ── Chart data ────────────────────────────────────────────────
        monthly_labels = [str(p) for p in monthly["month"]]
        actual_values  = [round(float(v), 2) for v in y]

        response["chart_data"] = [
            {
                "chart_id":   "sales_forecast",
                "chart_type": "line",
                "title":      "Monthly Sales & Forecast",
                "x_axis":     monthly_labels + [next_period],
                "series":     [
                    {
                        "name":   "Actual Sales",
                        "values": actual_values + [None],
                    },
                    {
                        "name":   "Forecast",
                        "values": [None] * len(actual_values) + [round(predicted, 2)],
                    },
                ],
            }
        ]

        response["summary"]        = ""
        response["summary_levels"] = {"simple": "", "medium": "", "advanced": ""}
        response["confidence"]     = confidence
        return response

    except Exception as e:
        response["status"]  = "error"
        response["message"] = str(e)
        return response