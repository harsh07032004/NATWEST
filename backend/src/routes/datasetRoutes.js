const express = require("express");
const axios = require("axios");

const router = express.Router();

/**
 * @route   POST /api/dataset/profile
 * @desc    Proxies schema profiling request to Python execution engine
 */
router.post("/profile", async (req, res) => {
  try {
    console.log("🔥 /api/dataset/profile HIT");
    console.log("📦 Request Body:", req.body);

    const { dataset_ref } = req.body;

    // ✅ Validate input
    if (!dataset_ref) {
      console.log("❌ dataset_ref missing");
      return res.status(400).json({
        error: "dataset_ref is required",
      });
    }

    // ✅ Get execution engine URL dynamically
    const engineUrl = process.env.EXECUTION_ENGINE_URL;

    if (!engineUrl) {
      console.error("❌ EXECUTION_ENGINE_URL is missing in environment");
      return res.status(500).json({
        error: "Execution Engine URL not configured",
      });
    }

    const endpoint = `${engineUrl}/analyze_schema`;

    console.log("🌐 Calling Execution Engine:", endpoint);

    // ✅ Call Python execution engine
    const pythonRes = await axios.post(
      endpoint,
      { dataset_ref },
      { timeout: 20000 },
    );

    console.log("✅ Engine response received");

    // ✅ Send response back to frontend
    return res.status(200).json(pythonRes.data);
  } catch (error) {
    console.error("🔥 DATASET PROFILE ERROR:");

    // Detailed error logging
    if (error.response) {
      console.error("Response Data:", error.response.data);
      console.error("Status:", error.response.status);
    } else if (error.request) {
      console.error("No response received from engine");
    } else {
      console.error("Error Message:", error.message);
    }

    return res.status(500).json({
      error: "Failed to profile dataset",
      details: error.response?.data || error.message,
    });
  }
});

module.exports = router;
