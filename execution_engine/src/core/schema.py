def base_response(query_type=None, intent=""):
    """
    Standard envelope for all execution engine responses.
    Every model merges its results into this structure.
    """
    return {
        "query_type": query_type if query_type is not None else [],
        "intent": intent,
        "status": "success",
        "summary": "",
        "summary_levels": {
            "simple": "",
            "medium": "",
            "advanced": ""
        },
        "key_metrics": [],
        "trend": {},
        "breakdown": {
            "category": [],   # Category dimension
            "merchant": [],   # Sub-Category dimension (reused key for compatibility)
            "time": [],       # Monthly time series
            "region": [],     # Region dimension
            "segment": [],    # Segment dimension
        },
        "diagnostics": {
            "causes": [],
            "anomalies": []
        },
        "prediction": {},
        "comparison": {},
        "chart_data": [],
        "recommendations": [],
        "confidence": 0,
        "limitations": [],
        "warnings": []
    }