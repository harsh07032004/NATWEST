const { generateExecutionPlan } = require("../services/orchestratorService");
const axios = require("axios");

// Retry function
const callExecutionEngine = async (url, payload, retries = 3) => {
  try {
    const response = await axios.post(url, payload, { timeout: 20000 });
    return response;
  } catch (error) {
    if (retries > 0) {
      console.log(`🔁 Retrying engine... attempts left: ${retries}`);
      await new Promise((res) => setTimeout(res, 3000));
      return callExecutionEngine(url, payload, retries - 1);
    }
    throw error;
  }
};

const processQuery = async (req, res) => {
  try {
    console.log("🔥 /api/query HIT");
    console.log("BODY:", req.body);

    const { query, dataset_ref, target_schema, language = "en" } = req.body;

    if (!query) {
      console.log("❌ Query missing");
      return res.status(400).json({ message: "Query text is required" });
    }

    console.log("⚙️ Generating execution plan...");
    const mlPayload = await generateExecutionPlan(
      query,
      dataset_ref,
      target_schema,
      language,
    );

    console.log("✅ Plan generated");

    const engineUrl = process.env.EXECUTION_ENGINE_URL;

    if (!engineUrl) {
      console.error("❌ EXECUTION_ENGINE_URL missing");
      return res.status(500).json({
        message: "Execution Engine URL not configured",
      });
    }

    let pureMathData;

    try {
      console.log("🌐 Calling Engine:", `${engineUrl}/compute`);

      const mathResponse = await callExecutionEngine(
        `${engineUrl}/compute`,
        mlPayload,
      );

      console.log("✅ Engine response received");

      pureMathData = mathResponse.data;
    } catch (mathError) {
      console.error("🔥 FULL ENGINE ERROR:", mathError);

      return res.status(503).json({
        message: "Execution Engine is waking up, please try again...",
      });
    }

    res.status(200).json(pureMathData);
  } catch (error) {
    console.error("🔥 SERVER ERROR:", error);

    res.status(500).json({
      message: "Server Error processing query",
      error: error.message,
    });
  }
};

module.exports = { processQuery };
