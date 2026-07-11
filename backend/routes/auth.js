const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const {
  register, login, logout, me, updateTheme, changePassword
} = require('../controllers/authController');

router.post('/register', register);
router.post('/login', login);
router.post('/logout', auth, logout);
router.get('/me', auth, me);
router.patch('/theme', auth, updateTheme);
router.patch('/password', auth, changePassword);

module.exports = router;
