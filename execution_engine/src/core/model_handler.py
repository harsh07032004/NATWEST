from src.models.descriptive import descriptive_model
from src.models.diagnostic import diagnostic_model
from src.models.comparative import comparative_model
from src.models.predictive import predictive_model
from src.core.schema import base_response


# Maps query_type strings to their handler functions
MODEL_REGISTRY = {
    "descriptive": descriptive_model,
    "diagnostic":  diagnostic_model,
    "comparative": comparative_model,
    "predictive":  predictive_model,
}

VALID_TYPES = set(MODEL_REGISTRY.keys())


def model_handler(payload):
    """
    Central router: receives the JSON execution plan from the Node.js orchestrator,
    dispatches to ALL applicable analytical models, and merges their results into
    a single unified response.

    Supports multi-type queries:
      query_type can be a string ("descriptive") OR an array (["descriptive", "diagnostic"]).
    """
    intent_block = payload.get("analytical_intent", {})
    raw_types    = intent_block.get("query_type", "descriptive")
    intent       = intent_block.get("intent", "")

    # ── Normalize to a list ──────────────────────────────────────────
    if isinstance(raw_types, str):
        query_types = [raw_types.strip().lower()]
    elif isinstance(raw_types, list):
        query_types = [t.strip().lower() for t in raw_types if isinstance(t, str)]
    else:
        query_types = ["descriptive"]

    # Validate — reject unknown types early
    invalid = [t for t in query_types if t not in VALID_TYPES]
    if invalid:
        return {
            "status":  "error",
            "message": f"Unsupported query_type(s): {invalid}. "
                       f"Must be from: {sorted(VALID_TYPES)}."
        }

    if not query_types:
        query_types = ["descriptive"]

    # Initialize envelope with all types
    response = base_response(query_type=query_types, intent=intent)

    # ── Run each model and merge ─────────────────────────────────────
    model_errors = []
    min_confidence = 1.0

    for qtype in query_types:
        model_fn = MODEL_REGISTRY[qtype]

        try:
            res = model_fn(payload)
        except Exception as e:
            model_errors.append(f"{qtype}: {str(e)}")
            continue

        if not res:
            continue

        # If a model itself returned an error status, log it and skip merging
        if res.get("status") == "error":
            model_errors.append(f"{qtype}: {res.get('message', 'Unknown error')}")
            continue

        # ── Merge model result into the envelope ─────────────────────
        _merge_result(response, res)

        # Track the lowest confidence across all models
        if res.get("confidence") is not None:
            min_confidence = min(min_confidence, float(res["confidence"]))

    # ── Post-merge cleanup ───────────────────────────────────────────

    # If ALL models failed, return an error
    if len(model_errors) == len(query_types):
        return {
            "status":  "error",
            "message": f"All models failed: {'; '.join(model_errors)}"
        }

    # Append partial errors as warnings
    if model_errors:
        for err in model_errors:
            response["warnings"].append(f"Partial failure — {err}")

    # Deduplicate recommendations
    seen_recs = set()
    unique_recs = []
    for r in response.get("recommendations", []):
        action = r.get("action", r) if isinstance(r, dict) else r
        if action not in seen_recs:
            seen_recs.add(action)
            unique_recs.append(r)
    response["recommendations"] = unique_recs

    # Deduplicate warnings
    response["warnings"] = list(dict.fromkeys(response.get("warnings", [])))

    # Deduplicate chart_data by chart_id
    seen_charts = set()
    unique_charts = []
    for c in response.get("chart_data", []):
        cid = c.get("chart_id", id(c))
        if cid not in seen_charts:
            seen_charts.add(cid)
            unique_charts.append(c)
    response["chart_data"] = unique_charts

    # Final status and confidence
    response["status"]     = "success"
    response["confidence"] = round(min_confidence, 2) if min_confidence < 1.0 else 0.90

    return response


def _merge_result(envelope, res):
    """
    Intelligently merges a single model's output into the shared envelope.
    - Lists are appended (key_metrics, chart_data, recommendations, warnings, limitations)
    - Nested dicts are deep-merged (breakdown, diagnostics)
    - Singletons are overwritten only if newly non-empty (trend, prediction, comparison)
    - summary and summary_levels are concatenated
    """

    # ── List fields: append ──────────────────────────────────────────
    for key in ("key_metrics", "chart_data", "recommendations", "warnings", "limitations"):
        existing = envelope.get(key, [])
        incoming = res.get(key, [])
        if isinstance(existing, list) and isinstance(incoming, list):
            envelope[key] = existing + incoming

    # ── Breakdown: deep-merge each sub-dimension list ────────────────
    env_bd = envelope.get("breakdown", {})
    res_bd = res.get("breakdown", {})
    if isinstance(res_bd, dict):
        for dim_key in ("category", "merchant", "time", "region", "segment"):
            existing_list = env_bd.get(dim_key, [])
            incoming_list = res_bd.get(dim_key, [])
            if isinstance(existing_list, list) and isinstance(incoming_list, list):
                # Deduplicate by label
                seen = {item.get("label") for item in existing_list}
                for item in incoming_list:
                    if item.get("label") not in seen:
                        existing_list.append(item)
                        seen.add(item.get("label"))
                env_bd[dim_key] = existing_list
        envelope["breakdown"] = env_bd

    # ── Diagnostics: merge causes and anomalies ──────────────────────
    env_diag = envelope.get("diagnostics", {})
    res_diag = res.get("diagnostics", {})
    if isinstance(res_diag, dict):
        # Causes
        env_causes = env_diag.get("causes", [])
        res_causes = res_diag.get("causes", [])
        if isinstance(env_causes, list) and isinstance(res_causes, list):
            seen_causes = {c.get("cause") for c in env_causes}
            for c in res_causes:
                if c.get("cause") not in seen_causes:
                    env_causes.append(c)
                    seen_causes.add(c.get("cause"))
            env_diag["causes"] = env_causes

        # Anomalies
        env_anomalies = env_diag.get("anomalies", [])
        res_anomalies = res_diag.get("anomalies", [])
        if isinstance(env_anomalies, list) and isinstance(res_anomalies, list):
            env_diag["anomalies"] = env_anomalies + res_anomalies

        envelope["diagnostics"] = env_diag

    # ── Trend: overwrite only if the envelope has no trend yet ────────
    res_trend = res.get("trend", {})
    if res_trend and (not envelope.get("trend") or not envelope["trend"].get("direction")):
        envelope["trend"] = res_trend

    # ── Prediction: overwrite only if envelope has none ───────────────
    res_pred = res.get("prediction", {})
    if res_pred and not envelope.get("prediction"):
        envelope["prediction"] = res_pred

    # ── Comparison: overwrite only if envelope has none ───────────────
    res_comp = res.get("comparison", {})
    if res_comp and not envelope.get("comparison"):
        envelope["comparison"] = res_comp

    # ── Summary: concatenate non-empty summaries ─────────────────────
    res_summary = res.get("summary", "")
    if res_summary:
        existing = envelope.get("summary", "")
        if existing:
            envelope["summary"] = f"{existing} {res_summary}"
        else:
            envelope["summary"] = res_summary

    # ── Summary levels: concatenate each level ───────────────────────
    res_levels = res.get("summary_levels", {})
    env_levels = envelope.get("summary_levels", {"simple": "", "medium": "", "advanced": ""})
    if isinstance(res_levels, dict):
        for level in ("simple", "medium", "advanced"):
            incoming = res_levels.get(level, "")
            if incoming:
                existing = env_levels.get(level, "")
                env_levels[level] = f"{existing} {incoming}".strip() if existing else incoming
        envelope["summary_levels"] = env_levels

    # Avoid propagating identity fields from individual models
    for key in ("query_type", "intent", "status"):
        res.pop(key, None)