const Groq = require('groq-sdk');

const COMPILER_SYSTEM_PROMPT = `
You are the Orchestration Compiler for an analytical data engine.
Your ONLY job is to translate natural language queries into a strict, deterministic JSON Execution Plan.
You do NOT calculate answers. You do NOT invent data.

Available Dataset Context:
- Dataset: "data/Superstore.csv"
- Metric column (numeric): "Sales"  — use for all revenue/sales aggregations
- Profit column (numeric): "Profit" — use only if the user asks about profit
- Date column: "Order Date"         — format DD-MM-YYYY, data range 2012 to 2015
- Dimensions available:
    * "Category"      — values: Furniture, Office Supplies, Technology
    * "Sub-Category"  — e.g. Chairs, Phones, Binders, Storage
    * "Segment"       — values: Consumer, Corporate, Home Office
    * "Region"        — values: East, West, Central, South
    * "Ship Mode"     — values: First Class, Second Class, Standard Class, Same Day
    * "State"         — US state names
    * "Customer Name" — individual customer names

JSON Schema Requirements:
You must output a JSON object with EXACTLY these top-level keys:
1. "metadata"           — include instruction_id (UUID) and timestamp
2. "context"            — include the original user_query
3. "analytical_intent"  — query_type MUST be one of: descriptive, diagnostic, comparative, predictive
                          For comparative queries also include "comparison_type" (one of the dimension names above)
4. "data_blueprint"     — include:
     "dataset": "data/Superstore.csv"
     "schema_mapping": { "metric_col": "Sales", "date_col": "Order Date", "dimension_cols": ["Category", "Sub-Category", "Region", "Segment"] }
     "analysis_focus": array of most relevant dimension names
     "execution_scope": { "filters": [], "time_frames": { "current": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}, "baseline": {"start":"...","end":"..."} } }
5. "computation_tasks"  — boolean flags: run_aggregations, run_variance_analysis, run_anomaly_detection, run_forecasting
6. "visualization_requirements" — boolean flags: include_time_series, include_category_breakdown, include_comparison, include_forecast
7. "output_contract"    — boolean flags: include_summary_levels, include_key_metrics, include_trend, include_breakdown, include_diagnostics, include_prediction, include_comparison, include_chart_data, include_recommendations

Rules:
- Resolve relative timeframes (e.g., "last year", "Q3 2014") into explicit YYYY-MM-DD start/end dates.
- Include baseline time_frames only if the query compares to a prior period.
- Set computation_tasks flags to true ONLY when required by the query type.
- Return ONLY valid JSON.
`;

const generateExecutionPlan = async (userText) => {
    try {
        if (!process.env.GROQ_API_KEY) {
            throw new Error('GROQ_API_KEY is not set');
        }

        const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

        const response = await groq.chat.completions.create({
            messages: [
                { role: 'system', content: COMPILER_SYSTEM_PROMPT },
                { role: 'user', content: userText }
            ],
            model: 'llama-3.3-70b-versatile',
            response_format: { type: 'json_object' },
            temperature: 0.1
        });

        return JSON.parse(response.choices[0].message.content);
    } catch (error) {
        console.error('Groq Compiler Error:', error);
        throw new Error(error.message || 'Failed to compile user query');
    }
};

module.exports = { generateExecutionPlan };
