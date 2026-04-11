const express = require('express');
const router = express.Router();
const { createConversation, listConversations, saveTurn, getHistory } = require('../controllers/chatController');

router.post('/conversations', createConversation);
router.get('/conversations/:userId', listConversations);
router.post('/turns', saveTurn);
router.get('/history/:convId', getHistory);

module.exports = router;
