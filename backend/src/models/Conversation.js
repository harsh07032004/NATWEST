const mongoose = require('mongoose');

const messageSchema = new mongoose.Schema({
  message_id: { type: String, required: true },
  role: { type: String, enum: ['user', 'assistant'], required: true },
  user_query: { type: String, required: true },
  query_type: [String],
  ml_output: mongoose.Schema.Types.Mixed,
  simplified_response: { type: String, default: '' },
  timestamp: { type: String, required: true },
}, { _id: false });

const conversationSchema = new mongoose.Schema({
  conversation_id: { type: String, required: true, unique: true },
  user_id: { type: String, required: true },
  user_type: { type: String, required: true },
  dataset_ref: { type: String },
  title: String,
  created_at: { type: String },
  messages: [messageSchema],
});

conversationSchema.index({ user_id: 1 });
module.exports = mongoose.model('Conversation', conversationSchema, 'user_conversations');
