from src.models.descriptive import descriptive_model
from src.models.diagnostic import diagnostic_model
from src.models.comparative import comparative_model
from src.models.predictive import predictive_model
from src.core.schema import base_response


def model_handler(payload):
    """
    Central router: receives the JSON execution plan from the Node.js orchestrator,
    dispatches to the correct analytical model, and returns a clean unified response.
    """
    intent_block = payload.get("analytical_intent", {})
    query_type   = intent_block.get("query_type", "")
    intent       = intent_block.get("intent", "")

    # Initialize envelope with identity fields
    response = base_response(query_type=query_type, intent=intent)

    # ── Route to the correct model ───────────────────────────────────
    if query_type == "descriptive":
        res = descriptive_model(payload)
    elif query_type == "diagnostic":
        res = diagnostic_model(payload)
    elif query_type == "comparative":
        res = comparative_model(payload)
    elif query_type == "predictive":
        res = predictive_model(payload)
    else:
        return {
            "status":  "error",
            "message": f"Unsupported query_type: '{query_type}'. "
                       f"Must be one of: descriptive, diagnostic, comparative, predictive."
        }

    # ── Merge model result into the envelope ─────────────────────────
    if res:
        # If the model itself returned an error, pass it through immediately
        if res.get("status") == "error":
            return res

        # Avoid overwriting the envelope's identity fields
        for key in ["query_type", "intent"]:
            res.pop(key, None)

        response.update(res)

    # ── Final deduplication cleanup ──────────────────────────────────
    response["recommendations"] = list({
        r["action"]: r for r in response.get("recommendations", [])
    }.values())

    response["warnings"] = list(set(response.get("warnings", [])))

    # Ensure status and confidence are always set
    response["status"]     = response.get("status", "success")
    response["confidence"] = response.get("confidence", 0.90)

    return response