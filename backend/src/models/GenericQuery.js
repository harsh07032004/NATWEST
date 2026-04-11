const mongoose = require('mongoose');

const genericQuerySchema = new mongoose.Schema({
  query_text: { type: String, required: true },
  query_type: [String],
  intent: String,
  usage_count: { type: Number, default: 0 },
  created_at: { type: Date, default: Date.now },
});

module.exports = mongoose.model('GenericQuery', genericQuerySchema, 'generic_queries');
