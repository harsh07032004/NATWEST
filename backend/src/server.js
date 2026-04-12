const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const express = require("express");
const cors = require("cors");

const connectDB = require("./utils/db");

const userRoutes = require("./routes/userRoutes");
const queryRoutes = require("./routes/queryRoutes");
const chatRoutes = require("./routes/chatRoutes");
const questionnaireRoutes = require("./routes/questionnaireRoutes");
const uploadRoutes = require("./routes/uploadRoutes");
const datasetRoutes = require("./routes/datasetRoutes");

const app = express();

// ================== ✅ CORS CONFIG (FIXED FOR PRODUCTION) ==================

const allowedOrigins = [
  /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/,
  "https://talktodata-mt63.onrender.com", // 👈 YOUR FRONTEND URL
];

const CORS_OPTIONS = {
  origin: (origin, callback) => {
    // Allow no-origin requests (Postman, curl)
    if (!origin) return callback(null, true);

    const isAllowed = allowedOrigins.some((o) =>
      o instanceof RegExp ? o.test(origin) : o === origin,
    );

    if (isAllowed) {
      return callback(null, true);
    }

    return callback(new Error(`CORS: origin ${origin} not allowed`));
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
};

app.use(cors(CORS_OPTIONS));

// ================== ✅ MIDDLEWARE ==================

app.use(express.json());

// ================== ✅ ROUTES ==================

app.use("/api/users", userRoutes);
app.use("/api/query", queryRoutes);
app.use("/chat", chatRoutes);
app.use("/api/questionnaire", questionnaireRoutes);
app.use("/api/upload", uploadRoutes);
app.use("/api/dataset", datasetRoutes);

// ================== ✅ HEALTH CHECK ==================

app.get("/", (req, res) => {
  res.send("Talk to Data Backend is running!");
});

// ================== ✅ START SERVER ==================

const PORT = process.env.PORT || 5000;

connectDB()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error("Database connection failed:", err);
  });
