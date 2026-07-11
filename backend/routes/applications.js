const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const {
  getApplications, getApplication, prepareApplication,
  updateApplication, submitApplication, getStatus, deleteApplication,
  autoSubmitApplication, generateAIAnswers
} = require('../controllers/applicationsController');

router.get('/', auth, getApplications);
router.get('/:id', auth, getApplication);
router.post('/prepare', auth, prepareApplication);
router.post('/auto-submit', auth, autoSubmitApplication);   // NEW: AI auto-submit (no review)
router.put('/:id', auth, updateApplication);
router.post('/:id/submit', auth, submitApplication);
router.post('/:id/ai-answers', auth, generateAIAnswers);    // NEW: Generate AI answers for review page
router.get('/:id/status', auth, getStatus);
router.delete('/:id', auth, deleteApplication);

module.exports = router;
