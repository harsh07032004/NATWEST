const { generateExecutionPlan } = require("../services/orchestratorService");
const axios = require("axios");

// Retry function
const callExecutionEngine = async (url, payload) => {
  const MAX_RETRIES = 4;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      console.log(`🚀 Attempt ${attempt}: Calling Execution Engine`);

      const response = await axios.post(url, payload, {
        timeout: 60000, // 60 sec (IMPORTANT)
      });

      return response;
    } catch (error) {
      console.error(`❌ Attempt ${attempt} failed`);

      if (attempt === MAX_RETRIES) {
        throw error;
      }

      console.log("⏳ Waiting 15 seconds before retry...");
      await new Promise((res) => setTimeout(res, 15000));
    }
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
      console.error("🔥 ENGINE ERROR DETAILS:", {
        message: mathError.message,
        code: mathError.code,
        response: mathError.response?.data,
      });

      return res.status(503).json({
        message: "Execution Engine error",
        details: mathError.response?.data || mathError.message,
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
