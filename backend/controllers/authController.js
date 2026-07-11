const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../config/db');
require('dotenv').config();

const generateToken = (userId) =>
  jwt.sign({ id: userId }, process.env.JWT_SECRET, { expiresIn: process.env.JWT_EXPIRES_IN || '7d' });

// POST /api/auth/register
exports.register = async (req, res) => {
  try {
    const { full_name, email, password, phone, location } = req.body;
    if (!full_name || !email || !password)
      return res.status(400).json({ success: false, message: 'Name, email, and password are required.' });

    const [existing] = await db.query('SELECT id FROM users WHERE email = ?', [email]);
    if (existing.length > 0)
      return res.status(409).json({ success: false, message: 'Email already registered.' });

    const password_hash = await bcrypt.hash(password, 12);
    const [result] = await db.query(
      'INSERT INTO users (full_name, email, password_hash, phone, location) VALUES (?, ?, ?, ?, ?)',
      [full_name, email, password_hash, phone || null, location || null]
    );
    const userId = result.insertId;

    // Create empty profile row
    await db.query('INSERT INTO user_profiles (user_id) VALUES (?)', [userId]);

    const token = generateToken(userId);
    res.cookie('token', token, { httpOnly: true, maxAge: 7 * 24 * 60 * 60 * 1000, sameSite: 'lax' });

    return res.status(201).json({
      success: true,
      message: 'Registration successful.',
      token,
      user: { id: userId, full_name, email, theme_pref: 'dark' }
    });
  } catch (err) {
    console.error('Register error:', err);
    return res.status(500).json({ success: false, message: 'Server error during registration.' });
  }
};

// POST /api/auth/login
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password)
      return res.status(400).json({ success: false, message: 'Email and password are required.' });

    const [rows] = await db.query('SELECT * FROM users WHERE email = ?', [email]);
    if (rows.length === 0)
      return res.status(401).json({ success: false, message: 'Invalid email or password.' });

    const user = rows[0];
    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid)
      return res.status(401).json({ success: false, message: 'Invalid email or password.' });

    const token = generateToken(user.id);
    res.cookie('token', token, { httpOnly: true, maxAge: 7 * 24 * 60 * 60 * 1000, sameSite: 'lax' });

    return res.json({
      success: true,
      message: 'Login successful.',
      token,
      user: { id: user.id, full_name: user.full_name, email: user.email, theme_pref: user.theme_pref, profile_photo: user.profile_photo }
    });
  } catch (err) {
    console.error('Login error:', err);
    return res.status(500).json({ success: false, message: 'Server error during login.' });
  }
};

// POST /api/auth/logout
exports.logout = (req, res) => {
  res.clearCookie('token');
  return res.json({ success: true, message: 'Logged out successfully.' });
};

// GET /api/auth/me
exports.me = async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT id, full_name, email, phone, location, profile_photo, theme_pref, created_at FROM users WHERE id = ?',
      [req.user.id]
    );
    if (rows.length === 0)
      return res.status(404).json({ success: false, message: 'User not found.' });
    return res.json({ success: true, user: rows[0] });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// PATCH /api/auth/theme
exports.updateTheme = async (req, res) => {
  try {
    const { theme } = req.body;
    if (!['light', 'dark'].includes(theme))
      return res.status(400).json({ success: false, message: 'Theme must be light or dark.' });
    await db.query('UPDATE users SET theme_pref = ? WHERE id = ?', [theme, req.user.id]);
    return res.json({ success: true, theme });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// PATCH /api/auth/password
exports.changePassword = async (req, res) => {
  try {
    const { current_password, new_password } = req.body;
    const [rows] = await db.query('SELECT password_hash FROM users WHERE id = ?', [req.user.id]);
    const valid = await bcrypt.compare(current_password, rows[0].password_hash);
    if (!valid) return res.status(401).json({ success: false, message: 'Current password is incorrect.' });
    const hash = await bcrypt.hash(new_password, 12);
    await db.query('UPDATE users SET password_hash = ? WHERE id = ?', [hash, req.user.id]);
    return res.json({ success: true, message: 'Password updated successfully.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};
