const express = require('express');
const router = express.Router();
const { submitQuestionnaire } = require('../controllers/questionnaireController');

router.post('/', submitQuestionnaire);

module.exports = router;
