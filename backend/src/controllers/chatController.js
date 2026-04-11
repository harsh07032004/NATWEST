const Conversation = require('../models/Conversation');

const createConversation = async (req, res) => {
  try {
    const record = req.body;
    await Conversation.findOneAndUpdate(
      { conversation_id: record.conversation_id },
      {
        $set: {
          user_id: record.user_id,
          user_type: record.user_type,
          dataset_ref: record.dataset_ref,
          title: record.title,
          created_at: record.created_at
        }
      },
      { upsert: true, returnDocument: 'after' }
    );
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error saving conversation:', error);
    res.status(500).json({ error: error.message });
  }
};

const listConversations = async (req, res) => {
  try {
    const records = await Conversation.find({ user_id: req.params.userId })
      .sort({ created_at: -1 });
    res.status(200).json(records);
  } catch (error) {
    console.error('Error fetching conversations:', error);
    res.status(500).json({ error: error.message });
  }
};

const saveTurn = async (req, res) => {
  try {
    const { conversation_id, message } = req.body;
    await Conversation.findOneAndUpdate(
      { conversation_id: conversation_id },
      { $push: { messages: message } },
      { upsert: true, returnDocument: 'after' }
    );
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error saving message:', error);
    res.status(500).json({ error: error.message });
  }
};

const getHistory = async (req, res) => {
  try {
    const conv = await Conversation.findOne({ conversation_id: req.params.convId }).lean();
    if (!conv) {
      return res.status(200).json({ messages: [] });
    }
    return res.status(200).json({
      messages: conv.messages,
      user_type: conv.user_type,
      dataset_ref: conv.dataset_ref
    });
  } catch (error) {
    console.error('Error fetching history:', error);
    res.status(500).json({ error: error.message });
  }
};

module.exports = { createConversation, listConversations, saveTurn, getHistory };
