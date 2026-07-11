const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const {
  getJobs, getJob, addJob, scrapeJob, searchJobs, updateStatus, deleteJob, getStats
} = require('../controllers/jobsController');

router.get('/stats', auth, getStats);
router.get('/', auth, getJobs);
router.get('/:id', auth, getJob);
router.post('/', auth, addJob);
router.post('/scrape', auth, scrapeJob);
router.post('/search', auth, searchJobs);
router.patch('/:id/status', auth, updateStatus);
router.delete('/:id', auth, deleteJob);

module.exports = router;
