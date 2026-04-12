const { generateExecutionPlan } = require("../services/orchestratorService");
const axios = require("axios");

// ✅ Retry function (ADD THIS)
const callExecutionEngine = async (url, payload, retries = 3) => {
  try {
    const response = await axios.post(url, payload, { timeout: 20000 });
    return response;
  } catch (error) {
    if (retries > 0) {
      console.log(`Retrying engine... attempts left: ${retries}`);
      await new Promise((res) => setTimeout(res, 3000)); // wait 3 sec
      return callExecutionEngine(url, payload, retries - 1);
    }
    throw error;
  }
};

/**
 * Orchestrates the full query pipeline
 */
const processQuery = async (req, res) => {
  try {
    const { query, dataset_ref, target_schema, language = "en" } = req.body;

    if (!query) {
      return res.status(400).json({ message: "Query text is required" });
    }

    const mlPayload = await generateExecutionPlan(
      query,
      dataset_ref,
      target_schema,
      language,
    );

    let pureMathData;

    try {
      // ✅ Use ENV instead of localhost
      const engineUrl = process.env.EXECUTION_ENGINE_URL;

      const mathResponse = await callExecutionEngine(
        `${engineUrl}/compute`,
        mlPayload,
      );

      pureMathData = mathResponse.data;
    } catch (mathError) {
      console.error("Engine error:", mathError.message);

      return res.status(503).json({
        message: "Execution Engine is waking up, please try again...",
      });
    }

    res.status(200).json(pureMathData);
  } catch (error) {
    console.error(error);
    res.status(500).json({
      message: "Server Error processing query",
      error: error.message,
    });
  }
};

module.exports = { processQuery };
