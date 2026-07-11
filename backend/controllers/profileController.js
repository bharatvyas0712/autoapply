const db = require('../config/db');
const path = require('path');
const fs = require('fs');

// Helper to safely parse JSON fields
const safeJSON = (val) => {
  if (!val) return null;
  if (typeof val === 'object') return val;
  try { return JSON.parse(val); } catch { return null; }
};

// GET /api/profile
exports.getProfile = async (req, res) => {
  try {
    const [users] = await db.query(
      'SELECT id, full_name, email, phone, location, profile_photo, theme_pref FROM users WHERE id = ?',
      [req.user.id]
    );
    const [profiles] = await db.query(
      'SELECT * FROM user_profiles WHERE user_id = ?',
      [req.user.id]
    );
    if (!users.length) return res.status(404).json({ success: false, message: 'User not found.' });

    const profile = profiles[0] || {};
    const jsonFields = ['skills', 'work_history', 'education', 'certifications', 'languages', 'custom_answers'];
    jsonFields.forEach(f => { if (profile[f]) profile[f] = safeJSON(profile[f]); });

    return res.json({ success: true, user: users[0], profile });
  } catch (err) {
    console.error('getProfile error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// PUT /api/profile
exports.updateProfile = async (req, res) => {
  try {
    const {
      full_name, phone, location,
      headline, summary, linkedin_url, github_url, portfolio_url,
      skills, experience_years, current_salary, expected_salary,
      work_history, education, certifications, languages,
      job_type_pref, willing_to_relocate, notice_period_days, custom_answers
    } = req.body;

    // Update users table
    await db.query(
      'UPDATE users SET full_name = ?, phone = ?, location = ? WHERE id = ?',
      [full_name, phone || null, location || null, req.user.id]
    );

    // Upsert profile
    const stringify = (val) => val ? JSON.stringify(val) : null;
    await db.query(`
      INSERT INTO user_profiles
        (user_id, headline, summary, linkedin_url, github_url, portfolio_url,
         skills, experience_years, current_salary, expected_salary,
         work_history, education, certifications, languages,
         job_type_pref, willing_to_relocate, notice_period_days, custom_answers)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON DUPLICATE KEY UPDATE
        headline=VALUES(headline), summary=VALUES(summary),
        linkedin_url=VALUES(linkedin_url), github_url=VALUES(github_url),
        portfolio_url=VALUES(portfolio_url), skills=VALUES(skills),
        experience_years=VALUES(experience_years), current_salary=VALUES(current_salary),
        expected_salary=VALUES(expected_salary), work_history=VALUES(work_history),
        education=VALUES(education), certifications=VALUES(certifications),
        languages=VALUES(languages), job_type_pref=VALUES(job_type_pref),
        willing_to_relocate=VALUES(willing_to_relocate),
        notice_period_days=VALUES(notice_period_days),
        custom_answers=VALUES(custom_answers)
    `, [
      req.user.id, headline, summary, linkedin_url, github_url, portfolio_url,
      stringify(skills), experience_years || 0, current_salary || null, expected_salary || null,
      stringify(work_history), stringify(education), stringify(certifications),
      stringify(languages), job_type_pref || 'full-time',
      willing_to_relocate ? 1 : 0, notice_period_days || 0, stringify(custom_answers)
    ]);

    return res.json({ success: true, message: 'Profile updated successfully.' });
  } catch (err) {
    console.error('updateProfile error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/profile/photo
exports.uploadPhoto = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ success: false, message: 'No photo uploaded.' });
    const photoUrl = `/uploads/${req.user.id}/${req.file.filename}`;
    await db.query('UPDATE users SET profile_photo = ? WHERE id = ?', [photoUrl, req.user.id]);
    return res.json({ success: true, photo_url: photoUrl });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/profile/resume
exports.uploadResume = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ success: false, message: 'No resume uploaded.' });

    const resumeUrl = `/uploads/${req.user.id}/${req.file.filename}`;
    let parsedText = '';
    let parsedData = {};

    // Parse PDF
    if (req.file.mimetype === 'application/pdf') {
      try {
        const { PDFParse } = require('pdf-parse');
        const dataBuffer = fs.readFileSync(req.file.path);
        const pdfData = await new PDFParse({ data: dataBuffer }).getText();
        parsedText = pdfData.text;
        parsedData = extractResumeData(parsedText);
      } catch (e) {
        console.warn('PDF parse warning:', e.message);
      }
    }

    await db.query(
      'UPDATE user_profiles SET resume_url = ?, resume_text = ? WHERE user_id = ?',
      [resumeUrl, parsedText, req.user.id]
    );

    return res.json({ success: true, resume_url: resumeUrl, parsed: parsedData, text: parsedText });
  } catch (err) {
    console.error('uploadResume error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// Simple resume field extractor
function extractResumeData(text) {
  const data = {};
  // Email
  const emailMatch = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  if (emailMatch) data.email = emailMatch[0];
  // Phone
  const phoneMatch = text.match(/(\+?\d[\d\s\-().]{8,15}\d)/);
  if (phoneMatch) data.phone = phoneMatch[0].trim();
  // Skills (common tech keywords)
  const skillKeywords = ['javascript','python','java','react','node','sql','html','css','docker',
    'kubernetes','aws','git','mongodb','express','typescript','angular','vue','c++','c#',
    'flutter','django','spring','mysql','postgresql','redis','graphql','rest','api'];
  const lowerText = text.toLowerCase();
  data.skills = skillKeywords.filter(s => lowerText.includes(s));
  // Experience years
  const expMatch = text.match(/(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)/i);
  if (expMatch) data.experience_years = parseInt(expMatch[1]);
  return data;
}
