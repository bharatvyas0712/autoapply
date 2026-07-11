const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { runAgent } = require('../controllers/agentController');

router.post('/run', auth, runAgent);

module.exports = router;
