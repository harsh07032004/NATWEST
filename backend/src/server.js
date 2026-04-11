const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });

const express = require('express');
const cors = require('cors');
const connectDB = require('./utils/db');
const userRoutes = require('./routes/userRoutes');
const queryRoutes = require('./routes/queryRoutes');
const chatRoutes = require('./routes/chatRoutes');
const questionnaireRoutes = require('./routes/questionnaireRoutes');

const app = express();

// Middleware (must be registered BEFORE routes)
app.use(cors({ origin: ['http://localhost:5173', 'http://localhost:3000'] }));
app.use(express.json());

// Routes
app.use('/api/users', userRoutes);
app.use('/api/query', queryRoutes);
app.use('/chat', chatRoutes);
app.use('/api/questionnaire', questionnaireRoutes);

// Health-check route
app.get('/', (req, res) => {
    res.send('Talk to Data Backend is running!');
});

// Connect to MongoDB, then start listening
const PORT = process.env.PORT || 5000;
connectDB().then(() => {
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
});
