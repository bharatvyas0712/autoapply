const db = require('../config/db');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

class AsyncQueue {
  constructor() {
    this.queue = [];
    this.isProcessing = false;
  }
  async add(task) {
    return new Promise((resolve, reject) => {
      this.queue.push({ task, resolve, reject });
      if (!this.isProcessing) this.process();
    });
  }
  async process() {
    this.isProcessing = true;
    while (this.queue.length > 0) {
      const { task, resolve, reject } = this.queue.shift();
      try {
        const result = await task();
        resolve(result);
      } catch (err) {
        reject(err);
      }
    }
    this.isProcessing = false;
  }
}
const autoSubmitQueue = new AsyncQueue();

// GET /api/applications
exports.getApplications = async (req, res) => {
  try {
    const { status, page = 1, limit = 20 } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);
    let query = `
      SELECT a.*, j.title, j.company, j.location, j.job_url, j.job_type
      FROM applications a
      JOIN job_listings j ON a.job_id = j.id
      WHERE a.user_id = ?`;
    const params = [req.user.id];
    if (status) { query += ' AND a.status = ?'; params.push(status); }
    query += ' ORDER BY a.created_at DESC LIMIT ? OFFSET ?';
    params.push(parseInt(limit), offset);
    const [apps] = await db.query(query, params);
    const [[{ total }]] = await db.query('SELECT COUNT(*) as total FROM applications WHERE user_id = ?', [req.user.id]);
    return res.json({ success: true, applications: apps, total, page: parseInt(page) });
  } catch (err) {
    console.error('getApplications error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/applications/:id
exports.getApplication = async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT a.*, j.title, j.company, j.job_url, j.description
       FROM applications a JOIN job_listings j ON a.job_id = j.id
       WHERE a.id = ? AND a.user_id = ?`,
      [req.params.id, req.user.id]
    );
    if (!rows.length) return res.status(404).json({ success: false, message: 'Application not found.' });
    const app = rows[0];
    if (app.form_data && typeof app.form_data === 'string') app.form_data = JSON.parse(app.form_data);
    if (app.custom_qa && typeof app.custom_qa === 'string') app.custom_qa = JSON.parse(app.custom_qa);
    return res.json({ success: true, application: app });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/applications/prepare — fetch form fields from job URL (pre-fill for review)
exports.prepareApplication = async (req, res) => {
  try {
    const { job_id } = req.body;
    if (!job_id) return res.status(400).json({ success: false, message: 'job_id is required.' });

    // Get job details
    const [jobs] = await db.query('SELECT * FROM job_listings WHERE id = ? AND user_id = ?', [job_id, req.user.id]);
    if (!jobs.length) return res.status(404).json({ success: false, message: 'Job not found.' });
    const job = jobs[0];

    // Get user profile for auto-fill
    const [users] = await db.query('SELECT * FROM users WHERE id = ?', [req.user.id]);
    const [profiles] = await db.query('SELECT * FROM user_profiles WHERE user_id = ?', [req.user.id]);
    const user = users[0];
    const profile = profiles[0] || {};

    // Build pre-filled form data from profile
    const formData = {
      first_name: (user.full_name || '').split(' ')[0],
      last_name: (user.full_name || '').split(' ').slice(1).join(' '),
      full_name: user.full_name,
      email: user.email,
      phone: user.phone || '',
      location: user.location || '',
      linkedin: profile.linkedin_url || '',
      github: profile.github_url || '',
      portfolio: profile.portfolio_url || '',
      experience_years: profile.experience_years || 0,
      current_salary: profile.current_salary || '',
      expected_salary: profile.expected_salary || '',
      notice_period: profile.notice_period_days || 0,
      willing_to_relocate: profile.willing_to_relocate ? 'Yes' : 'No',
      resume_url: profile.resume_url || '',
      skills: profile.skills || [],
      cover_letter: generateCoverLetter(user, profile, job),
    };

    // Common Q&A defaults
    const commonQA = [
      { question: 'Are you legally authorized to work in this country?', answer: 'Yes', type: 'yesno' },
      { question: 'Do you require visa sponsorship?', answer: 'No', type: 'yesno' },
      { question: 'Are you willing to work on-site?', answer: profile.willing_to_relocate ? 'Yes' : 'No', type: 'yesno' },
      { question: 'How many years of experience do you have?', answer: String(profile.experience_years || 0), type: 'text' },
      { question: 'What is your expected salary?', answer: String(profile.expected_salary || ''), type: 'text' },
      { question: 'What is your notice period?', answer: `${profile.notice_period_days || 0} days`, type: 'text' },
    ];

    // Try to get real form fields from automation service
    let automationFields = [];
    try {
      const resp = await axios.post(
        `${process.env.AUTOMATION_SERVICE_URL}/analyze_form`,
        { url: job.job_url },
        { timeout: 30000 }
      );
      if (resp.data?.success) automationFields = resp.data.fields || [];
    } catch (e) {
      console.warn('Automation service unavailable for form analysis:', e.message);
    }

    // Create draft application
    const [result] = await db.query(
      `INSERT INTO applications (user_id, job_id, form_data, custom_qa, cover_letter, status)
       VALUES (?, ?, ?, ?, ?, 'review')`,
      [req.user.id, job_id, JSON.stringify(formData), JSON.stringify(commonQA), formData.cover_letter]
    );

    return res.json({
      success: true,
      application_id: result.insertId,
      form_data: formData,
      qa: commonQA,
      automation_fields: automationFields,
      job
    });
  } catch (err) {
    console.error('prepareApplication error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// PUT /api/applications/:id — user edits the form before submit
exports.updateApplication = async (req, res) => {
  try {
    const { form_data, custom_qa, cover_letter, review_notes } = req.body;
    await db.query(
      `UPDATE applications SET form_data = ?, custom_qa = ?, cover_letter = ?, review_notes = ?, status = 'review'
       WHERE id = ? AND user_id = ?`,
      [JSON.stringify(form_data), JSON.stringify(custom_qa), cover_letter, review_notes, req.params.id, req.user.id]
    );
    return res.json({ success: true, message: 'Application updated.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/applications/:id/submit — trigger Playwright automation
exports.submitApplication = async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT a.*, j.job_url FROM applications a JOIN job_listings j ON a.job_id = j.id WHERE a.id = ? AND a.user_id = ?',
      [req.params.id, req.user.id]
    );
    if (!rows.length) return res.status(404).json({ success: false, message: 'Application not found.' });
    const app = rows[0];

    // Mark as submitting
    await db.query('UPDATE applications SET status = ? WHERE id = ?', ['submitting', app.id]);

    // Create automation session
    const [sessResult] = await db.query(
      'INSERT INTO automation_sessions (user_id, application_id) VALUES (?, ?)',
      [req.user.id, app.id]
    );
    const sessionId = sessResult.insertId;

    // Respond immediately — automation runs async
    res.json({ success: true, message: 'Submission started.', session_id: sessionId, application_id: app.id });

    // Trigger automation service async
    const formData = typeof app.form_data === 'string' ? JSON.parse(app.form_data) : app.form_data;
    const customQA = typeof app.custom_qa === 'string' ? JSON.parse(app.custom_qa) : app.custom_qa;

    // Resume text so AI answer generation (unmapped questions) can answer
    // from real resume content, not just structured profile fields.
    const [profileRows] = await db.query(
      'SELECT resume_text FROM user_profiles WHERE user_id = ?',
      [req.user.id]
    );
    const resumeText = profileRows[0]?.resume_text || '';

    autoSubmitQueue.add(async () => {
    try {
      const response = await axios.post(
        `${process.env.AUTOMATION_SERVICE_URL}/apply`,
        {
          session_id: sessionId,
          application_id: app.id,
          user_id: req.user.id,
          job_id: app.job_id,
          job_url: app.job_url,
          form_data: formData,
          custom_qa: customQA,
          cover_letter: app.cover_letter,
          // Absolute path to the stored resume. resume_url already starts with
          // "/uploads/...", and the actual file lives under backend/uploads/...
          // The Python service runs from a different cwd, so it needs an absolute path.
          resume_path: formData?.resume_url
            ? path.join(__dirname, '..', formData.resume_url)
            : null,
          resume_text: resumeText
        },
        // The automation can now legitimately pause for minutes at a time
        // (manual login wall, or waiting on a Review Queue answer), so the
        // old 2-minute timeout would mark a perfectly healthy in-progress
        // run as "failed". Default to 1 hour; override via env if needed.
        { timeout: parseInt(process.env.AUTOMATION_APPLY_TIMEOUT_MS, 10) || 3600000 }
      );

      const status = response.data?.success ? 'submitted' : 'failed';
      await db.query(
        'UPDATE applications SET status = ?, screenshot_url = ?, submitted_at = NOW() WHERE id = ?',
        [status, response.data?.screenshot || null, app.id]
      );
      await db.query(
        'UPDATE automation_sessions SET completed_at = NOW(), steps_completed = ?, steps_total = ?, session_log = ? WHERE id = ?',
        [response.data?.steps_done || 0, response.data?.steps_total || 0, JSON.stringify(response.data?.log || []), sessionId]
      );
      // Update job status
      if (status === 'submitted') {
        await db.query('UPDATE job_listings SET status = ? WHERE id = ?', ['applied', app.job_id]);
      }
    } catch (automErr) {
      console.error('Automation failed:', automErr.message);
      await db.query(
        'UPDATE applications SET status = ?, error_message = ? WHERE id = ?',
        ['failed', automErr.message, app.id]
      );
      await db.query(
        'UPDATE automation_sessions SET completed_at = NOW(), error_message = ? WHERE id = ?',
        [automErr.message, sessionId]
      );
    }
    });
  } catch (err) {
    console.error('submitApplication error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/applications/:id/status — poll automation status
exports.getStatus = async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT a.status, a.error_message, a.screenshot_url, a.submitted_at,
              s.steps_completed, s.steps_total, s.session_log, s.error_message as sess_error
       FROM applications a
       LEFT JOIN automation_sessions s ON s.application_id = a.id
       WHERE a.id = ? AND a.user_id = ?
       ORDER BY s.started_at DESC LIMIT 1`,
      [req.params.id, req.user.id]
    );
    if (!rows.length) return res.status(404).json({ success: false, message: 'Not found.' });
    return res.json({ success: true, ...rows[0] });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// DELETE /api/applications/:id
exports.deleteApplication = async (req, res) => {
  try {
    await db.query('DELETE FROM applications WHERE id = ? AND user_id = ?', [req.params.id, req.user.id]);
    return res.json({ success: true, message: 'Application deleted.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

function generateCoverLetter(user, profile, job) {
  return `Dear Hiring Manager,

I am writing to express my strong interest in the ${job.title || 'position'} at ${job.company || 'your company'}. With ${profile.experience_years || 0} years of experience and a passion for delivering high-quality work, I am confident in my ability to contribute meaningfully to your team.

${profile.summary || 'I bring a strong foundation of technical skills and a proven track record of success.'}

I am particularly excited about this opportunity because it aligns perfectly with my career goals and expertise. I would welcome the chance to discuss how my background and skills can benefit ${job.company || 'your organization'}.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
${user.full_name}
${user.email}
${user.phone || ''}`;
}

// ── Helper: Groq API call ──────────────────────────────────────────────────
async function callGroqAI(prompt) {
  const GROQ_API_KEY = process.env.GROQ_API_KEY;
  const GROQ_MODEL   = process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';
  if (!GROQ_API_KEY) return null;
  try {
    const resp = await axios.post(
      'https://api.groq.com/openai/v1/chat/completions',
      {
        model: GROQ_MODEL,
        max_tokens: 500,
        temperature: 0.4,
        messages: [{ role: 'user', content: prompt }]
      },
      {
        headers: { Authorization: `Bearer ${GROQ_API_KEY}`, 'Content-Type': 'application/json' },
        timeout: 20000
      }
    );
    return resp.data?.choices?.[0]?.message?.content?.trim() || null;
  } catch (e) {
    console.warn('Groq API error:', e.message);
    return null;
  }
}

// ── Helper: Build applicant context string for Groq ───────────────────────
function buildApplicantContext(user, profile, job, resumeText) {
  const skills = Array.isArray(profile.skills)
    ? profile.skills.join(', ')
    : (profile.skills || '');
  return `
Name: ${user.full_name || ''}
Email: ${user.email || ''}
Phone: ${user.phone || ''}
Location: ${user.location || ''}
Experience: ${profile.experience_years || 0} years
Expected Salary: ${profile.expected_salary || 'Open to discussion'}
Notice Period: ${profile.notice_period_days || 0} days
Willing to Relocate: ${profile.willing_to_relocate ? 'Yes' : 'No'}
Skills: ${skills}
LinkedIn: ${profile.linkedin_url || ''}
GitHub: ${profile.github_url || ''}
Job Title Applied: ${job.title || ''}
Company: ${job.company || ''}
Resume: ${(resumeText || '').slice(0, 2000)}
`.trim();
}

// ── POST /api/applications/:id/ai-answers ─────────────────────────────────
// Groq se Q&A answers generate karo aur DB mein save karo
exports.generateAIAnswers = async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT a.*, j.title, j.company, j.description
       FROM applications a JOIN job_listings j ON a.job_id = j.id
       WHERE a.id = ? AND a.user_id = ?`,
      [req.params.id, req.user.id]
    );
    if (!rows.length) return res.status(404).json({ success: false, message: 'Application not found.' });
    const app = rows[0];

    const [profileRows] = await db.query('SELECT * FROM user_profiles WHERE user_id = ?', [req.user.id]);
    const [userRows]    = await db.query('SELECT * FROM users WHERE id = ?', [req.user.id]);
    const profile = profileRows[0] || {};
    const user    = userRows[0] || {};

    const formData  = typeof app.form_data === 'string' ? JSON.parse(app.form_data) : (app.form_data || {});
    const customQA  = typeof app.custom_qa === 'string' ? JSON.parse(app.custom_qa) : (app.custom_qa || []);
    const context   = buildApplicantContext(user, profile, app, profile.resume_text || '');

    // Generate AI answer for each Q&A item
    const updatedQA = [];
    for (const qa of customQA) {
      const prompt = `You are an expert AI Job Application Assistant.
Your role is to automatically answer job application questions using ONLY the information available in the candidate's resume/profile.

Instructions:
1. Carefully analyze the candidate's resume/profile before answering any question.
2. Always generate answers that are:
   - Professional
   - Human-like
   - Concise unless a detailed answer is required
   - Grammatically correct
   - Relevant to the job application
3. Never invent or hallucinate information that is not present in the resume.
4. If the application asks about skills, projects, education, certifications, internships, achievements, or work experience, use the resume as the primary source.
5. If a question requires an opinion or motivation (for example, "Why do you want to work here?"), generate a natural and professional answer based on:
   - Candidate's background
   - Candidate's career goals
6. Tailor every answer to match the required skills and responsibilities if possible.
7. If multiple answers are possible, choose the one that best aligns with the candidate's resume.
8. For salary expectations:
   - If the resume/profile contains expected salary, use it.
   - Otherwise answer: "Negotiable based on the role and overall compensation package."
9. For notice period:
   - If the candidate is a fresher (0 years of experience), answer: "Immediate"
   - Otherwise use resume/profile information.
10. For experience:
    - Calculate only from the resume.
    - Never exaggerate.
11. For technical questions:
    - Explain only technologies that appear in the resume.
    - Do not claim knowledge of technologies not listed.
12. For yes/no questions:
    - Return only "Yes" or "No".
13. For dropdown selections:
    - Return only the most appropriate option text.
    - Do not include explanations.
14. For text fields:
    - Return plain text only.
    - Do not use Markdown, bullet points, or special formatting.
15. If the answer cannot be determined from the resume (excluding expected/current salary and notice period, which MUST follow the defaults in rules 8 and 9):
    - First check whether it can be reasonably inferred (e.g. assume authorized to work = "Yes", assume visa sponsorship not required = "No", 18 or older = "Yes").
    - If not, return exactly: "Not specified in resume"
16. Never mention that you are an AI.
17. Never mention the resume in your response.
18. Keep answers natural so they appear to be written by the candidate.
19. If the question asks for a count, duration, or numeric value in specific units (for example: "How many years of experience...", "What is your notice period in days?", "Expected salary in LPA", etc.), return ONLY the number/digits. Do not append words like "years", "months", "days", "LPA", etc.

CANDIDATE PROFILE:
${context}

QUESTION: ${qa.question}

Output Rules:
- Return ONLY the answer.
- No explanations.
- No extra comments.
- No labels.
- No Markdown.
- No quotation marks unless required.`;
      const aiAnswer = await callGroqAI(prompt);
      updatedQA.push({ ...qa, answer: aiAnswer || qa.answer || '', ai_generated: !!aiAnswer });
    }

    // Optionally regenerate cover letter
    let coverLetter = app.cover_letter;
    if (req.body.regenerate_cover_letter) {
      const clPrompt = `Write a professional, concise cover letter (3 paragraphs) for this job application.
Use ONLY facts from the applicant profile. Output ONLY the letter text.

APPLICANT PROFILE:
${context}`;
      const aiCL = await callGroqAI(clPrompt);
      if (aiCL) coverLetter = aiCL;
    }

    // Save back to DB
    await db.query(
      'UPDATE applications SET custom_qa = ?, cover_letter = ? WHERE id = ? AND user_id = ?',
      [JSON.stringify(updatedQA), coverLetter, req.params.id, req.user.id]
    );

    return res.json({ success: true, qa: updatedQA, cover_letter: coverLetter });
  } catch (err) {
    console.error('generateAIAnswers error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// ── POST /api/applications/auto-submit ────────────────────────────────────
// One-click: prepare + Groq AI answers + submit — bina review page ke
exports.autoSubmitApplication = async (req, res) => {
  try {
    const { job_id } = req.body;
    if (!job_id) return res.status(400).json({ success: false, message: 'job_id is required.' });

    const [jobs]     = await db.query('SELECT * FROM job_listings WHERE id = ? AND user_id = ?', [job_id, req.user.id]);
    if (!jobs.length) return res.status(404).json({ success: false, message: 'Job not found.' });
    const job = jobs[0];

    const [users]    = await db.query('SELECT * FROM users WHERE id = ?', [req.user.id]);
    const [profiles] = await db.query('SELECT * FROM user_profiles WHERE user_id = ?', [req.user.id]);
    const user    = users[0];
    const profile = profiles[0] || {};
    const resumeText = profile.resume_text || '';

    // Build form data from profile
    const formData = {
      first_name:          (user.full_name || '').split(' ')[0],
      last_name:           (user.full_name || '').split(' ').slice(1).join(' '),
      full_name:           user.full_name,
      email:               user.email,
      phone:               user.phone || '',
      location:            user.location || '',
      linkedin:            profile.linkedin_url || '',
      github:              profile.github_url || '',
      portfolio:           profile.portfolio_url || '',
      experience_years:    profile.experience_years || 0,
      current_salary:      profile.current_salary || '',
      expected_salary:     profile.expected_salary || '',
      notice_period:       profile.notice_period_days || 0,
      willing_to_relocate: profile.willing_to_relocate ? 'Yes' : 'No',
      resume_url:          profile.resume_url || '',
      skills:              profile.skills || [],
    };

    const context = buildApplicantContext(user, profile, job, resumeText);

    // AI-generate cover letter
    const clPrompt = `Write a professional, concise cover letter (3 paragraphs max) for this job.
Use ONLY facts from the applicant profile. Output ONLY the letter text.

APPLICANT PROFILE:
${context}`;
    const aiCoverLetter = await callGroqAI(clPrompt) || generateCoverLetter(user, profile, job);

    // Pre-generate Q&A answers via Groq
    const baseQA = [
      { question: 'Are you legally authorized to work in this country?', type: 'yesno' },
      { question: 'Do you require visa sponsorship?',                    type: 'yesno' },
      { question: 'Are you willing to work on-site?',                    type: 'yesno' },
      { question: 'Are you willing to relocate?',                        type: 'yesno' },
      { question: 'Are you 18 years of age or older?',                   type: 'yesno' },
      { question: 'How many years of experience do you have?',           type: 'text'  },
      { question: 'What is your expected salary?',                       type: 'text'  },
      { question: 'What is your notice period?',                         type: 'text'  },
    ];

    const answeredQA = [];
    for (const qa of baseQA) {
      const prompt = `You are an expert AI Job Application Assistant.
Your role is to automatically answer job application questions using ONLY the information available in the candidate's resume/profile.

Instructions:
1. Carefully analyze the candidate's resume/profile before answering any question.
2. Always generate answers that are:
   - Professional
   - Human-like
   - Concise unless a detailed answer is required
   - Grammatically correct
   - Relevant to the job application
3. Never invent or hallucinate information that is not present in the resume.
4. If the application asks about skills, projects, education, certifications, internships, achievements, or work experience, use the resume as the primary source.
5. If a question requires an opinion or motivation (for example, "Why do you want to work here?"), generate a natural and professional answer based on:
   - Candidate's background
   - Candidate's career goals
6. Tailor every answer to match the required skills and responsibilities if possible.
7. If multiple answers are possible, choose the one that best aligns with the candidate's resume.
8. For salary expectations:
   - If the resume/profile contains expected salary, use it.
   - Otherwise answer: "Negotiable based on the role and overall compensation package."
9. For notice period:
   - If the candidate is a fresher (0 years of experience), answer: "Immediate"
   - Otherwise use resume/profile information.
10. For experience:
    - Calculate only from the resume.
    - Never exaggerate.
11. For technical questions:
    - Explain only technologies that appear in the resume.
    - Do not claim knowledge of technologies not listed.
12. For yes/no questions:
    - Return only "Yes" or "No".
13. For dropdown selections:
    - Return only the most appropriate option text.
    - Do not include explanations.
14. For text fields:
    - Return plain text only.
    - Do not use Markdown, bullet points, or special formatting.
15. If the answer cannot be determined from the resume (excluding expected/current salary and notice period, which MUST follow the defaults in rules 8 and 9):
    - First check whether it can be reasonably inferred (e.g. assume authorized to work = "Yes", assume visa sponsorship not required = "No", 18 or older = "Yes").
    - If not, return exactly: "Not specified in resume"
16. Never mention that you are an AI.
17. Never mention the resume in your response.
18. Keep answers natural so they appear to be written by the candidate.
19. If the question asks for a count, duration, or numeric value in specific units (for example: "How many years of experience...", "What is your notice period in days?", "Expected salary in LPA", etc.), return ONLY the number/digits. Do not append words like "years", "months", "days", "LPA", etc.

CANDIDATE PROFILE:
${context}

QUESTION: ${qa.question}

Output Rules:
- Return ONLY the answer.
- No explanations.
- No extra comments.
- No labels.
- No Markdown.
- No quotation marks unless required.`;
      const aiAnswer = await callGroqAI(prompt);
      answeredQA.push({ ...qa, answer: aiAnswer || (qa.type === 'yesno' ? 'Yes' : ''), ai_generated: true });
    }

    // Create application in 'submitting' status (skip review entirely)
    const [result] = await db.query(
      `INSERT INTO applications (user_id, job_id, form_data, custom_qa, cover_letter, status)
       VALUES (?, ?, ?, ?, ?, 'submitting')`,
      [req.user.id, job_id, JSON.stringify(formData), JSON.stringify(answeredQA), aiCoverLetter]
    );
    const applicationId = result.insertId;

    // Create automation session
    const [sessResult] = await db.query(
      'INSERT INTO automation_sessions (user_id, application_id) VALUES (?, ?)',
      [req.user.id, applicationId]
    );
    const sessionId = sessResult.insertId;

    // Respond immediately — automation runs async
    res.json({
      success: true,
      message: '🤖 AI auto-apply started! Playwright is filling the form...',
      application_id: applicationId,
      session_id: sessionId
    });

    // Trigger automation service async
    const resumePath = formData.resume_url ? path.join(__dirname, '..', formData.resume_url) : null;
    autoSubmitQueue.add(async () => {
    try {
      const response = await axios.post(
        `${process.env.AUTOMATION_SERVICE_URL}/apply`,
        {
          session_id:     sessionId,
          application_id: applicationId,
          user_id:        req.user.id,
          job_id:         job_id,
          job_url:        job.job_url,
          form_data:      formData,
          custom_qa:      answeredQA,
          cover_letter:   aiCoverLetter,
          resume_path:    resumePath,
          resume_text:    resumeText
        },
        { timeout: parseInt(process.env.AUTOMATION_APPLY_TIMEOUT_MS, 10) || 3600000 }
      );
      const status = response.data?.success ? 'submitted' : 'failed';
      await db.query(
        'UPDATE applications SET status = ?, screenshot_url = ?, submitted_at = NOW() WHERE id = ?',
        [status, response.data?.screenshot || null, applicationId]
      );
      await db.query(
        'UPDATE automation_sessions SET completed_at = NOW(), steps_completed = ?, steps_total = ?, session_log = ? WHERE id = ?',
        [response.data?.steps_done || 0, response.data?.steps_total || 0, JSON.stringify(response.data?.log || []), sessionId]
      );
      if (status === 'submitted') {
        await db.query('UPDATE job_listings SET status = ? WHERE id = ?', ['applied', job_id]);
      }
    } catch (automErr) {
      console.error('Auto-submit automation failed:', automErr.message);
      await db.query(
        'UPDATE applications SET status = ?, error_message = ? WHERE id = ?',
        ['failed', automErr.message, applicationId]
      );
      await db.query(
        'UPDATE automation_sessions SET completed_at = NOW(), error_message = ? WHERE id = ?',
        [automErr.message, sessionId]
      );
    }
    });
  } catch (err) {
    console.error('autoSubmitApplication error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/applications/:id/tailor
// Analyze gaps in candidate resume against the job description & suggest improvements and tailored cover letter
exports.tailorApplication = async (req, res) => {
  try {
    const { id } = req.params;
    // Just return a dummy response for now so the UI doesn't break
    res.json({
      success: true,
      analysis: "This is a placeholder for the tailor application feature. Your resume looks good but you might want to add more keywords related to the job description.",
      tailored_cover_letter: "Dear Hiring Manager,\\n\\nI am very interested in this position.\\n\\nSincerely,\\nApplicant"
    });
  } catch (err) {
    console.error('tailorApplication error:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/applications/sessions/:sessionId/log
// Callback for live log updates (no auth for internal microservice call)
exports.updateSessionLog = async (req, res) => {
  try {
    const { sessionId } = req.params;
    const { log, steps_done, steps_total } = req.body;
    await require('../config/db').query(
      'UPDATE automation_sessions SET session_log = ?, steps_completed = ?, steps_total = ? WHERE id = ?',
      [JSON.stringify(log || []), steps_done || 0, steps_total || 0, sessionId]
    );
    res.json({ success: true });
  } catch (err) {
    console.error('updateSessionLog error:', err);
    res.status(500).json({ success: false, message: 'Server error.' });
  }
};
