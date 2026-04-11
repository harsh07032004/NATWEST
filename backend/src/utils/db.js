const mongoose = require('mongoose');

const connectDB = async () => {
    const uri = process.env.MONGODB_URI;

    if (!uri) {
        console.error('[DB] MONGODB_URI is not defined. Check your backend/.env file.');
        console.error('[DB] The server will start, but database operations will fail.');
        return;
    }

    try {
        const conn = await mongoose.connect(uri);
        console.log(`MongoDB Connected: ${conn.connection.name} (host: ${conn.connection.host})`);
    } catch (error) {
        if (error.message.includes('ENOTFOUND') || error.message.includes('getaddrinfo')) {
            console.error('[DB] DNS resolution failed. Check your MONGODB_URI hostname or your network connection.');
        } else if (error.message.includes('Authentication failed') || error.message.includes('auth')) {
            console.error('[DB] Authentication failed. Check your username/password in MONGODB_URI.');
        } else if (error.message.includes('ETIMEDOUT') || error.message.includes('timed out')) {
            console.error('[DB] Connection timed out. Whitelist your IP in MongoDB Atlas → Network Access.');
        } else {
            console.error(`[DB] Connection failed: ${error.message}`);
        }
        console.error('[DB] The server will start, but database operations will fail.');
    }
};

module.exports = connectDB;