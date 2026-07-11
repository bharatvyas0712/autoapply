const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const upload = require('../middleware/upload');
const {
  getProfile, updateProfile, uploadPhoto, uploadResume
} = require('../controllers/profileController');

router.get('/', auth, getProfile);
router.put('/', auth, updateProfile);
router.post('/photo', auth, upload.single('photo'), uploadPhoto);
router.post('/resume', auth, upload.single('resume'), uploadResume);

module.exports = router;
