const db = require('../config/db');
const axios = require('axios');
require('dotenv').config();

// GET /api/jobs — list all jobs for user
exports.getJobs = async (req, res) => {
  try {
    const { status, search, page = 1, limit = 20 } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);
    let query = 'SELECT * FROM job_listings WHERE user_id = ?';
    const params = [req.user.id];

    if (status) { query += ' AND status = ?'; params.push(status); }
    if (search) { query += ' AND (title LIKE ? OR company LIKE ?)'; params.push(`%${search}%`, `%${search}%`); }

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
    params.push(parseInt(limit), offset);

    const [jobs] = await db.query(query, params);
    const [[{ total }]] = await db.query(
      'SELECT COUNT(*) as total FROM job_listings WHERE user_id = ?',
      [req.user.id]
    );

    return res.json({ success: true, jobs, total, page: parseInt(page), limit: parseInt(limit) });
  } catch (err) {
    console.error('getJobs error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/jobs/:id
exports.getJob = async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT * FROM job_listings WHERE id = ? AND user_id = ?',
      [req.params.id, req.user.id]
    );
    if (!rows.length) return res.status(404).json({ success: false, message: 'Job not found.' });
    return res.json({ success: true, job: rows[0] });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/jobs — manually add / paste a job URL
exports.addJob = async (req, res) => {
  try {
    const { title, company, location, job_url, description, salary_range, job_type, source } = req.body;
    if (!job_url) return res.status(400).json({ success: false, message: 'Job URL is required.' });

    const [result] = await db.query(
      `INSERT INTO job_listings
        (user_id, title, company, location, job_url, source, description, salary_range, job_type)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        req.user.id,
        title || 'Untitled Job',
        company || 'Unknown Company',
        location || 'Not specified',
        job_url,
        source || 'manual',
        description || null,
        salary_range || null,
        job_type || null
      ]
    );

    return res.status(201).json({ success: true, message: 'Job added.', job_id: result.insertId });
  } catch (err) {
    console.error('addJob error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/jobs/scrape — scrape a job URL via automation service
exports.scrapeJob = async (req, res) => {
  try {
    const { job_url } = req.body;
    if (!job_url) return res.status(400).json({ success: false, message: 'Job URL is required.' });

    let scraped = { title: 'Job from URL', company: '', location: '', description: '' };
    try {
      const response = await axios.post(
        `${process.env.AUTOMATION_SERVICE_URL}/scrape`,
        { url: job_url },
        { timeout: 30000 }
      );
      if (response.data?.success) scraped = { ...scraped, ...response.data.job };
    } catch (e) {
      console.warn('Scrape service unavailable, saving URL only:', e.message);
    }

    const [result] = await db.query(
      `INSERT INTO job_listings
        (user_id, title, company, location, job_url, source, description)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [req.user.id, scraped.title, scraped.company, scraped.location, job_url, 'scraped', scraped.description]
    );

    return res.json({ success: true, job_id: result.insertId, scraped });
  } catch (err) {
    console.error('scrapeJob error:', err);
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// POST /api/jobs/search — search jobs using automation service
exports.searchJobs = async (req, res) => {
  try {
    const { query, location, source, experience_level, job_type, easy_apply_only } = req.body;
    if (!query) return res.status(400).json({ success: false, message: 'Query is required.' });

    const response = await axios.post(
      `${process.env.AUTOMATION_SERVICE_URL}/search_jobs`,
      {
        query,
        location: location || 'Remote',
        source: source || 'all',
        experience_level: experience_level || '',
        job_type: job_type || '',
        easy_apply_only: !!easy_apply_only
      },
      { timeout: 90000 }
    );

    if (response.data?.success) {
      return res.json({ success: true, jobs: response.data.jobs });
    } else {
      return res.status(500).json({ success: false, message: response.data?.message || 'Search failed.' });
    }
  } catch (err) {
    console.error('searchJobs error:', err.message);
    return res.status(500).json({ success: false, message: 'Server error during search.' });
  }
};

// PATCH /api/jobs/:id/status
exports.updateStatus = async (req, res) => {
  try {
    const { status } = req.body;
    const allowed = ['pending', 'saved', 'applied', 'rejected', 'ignored'];
    if (!allowed.includes(status))
      return res.status(400).json({ success: false, message: 'Invalid status.' });
    await db.query(
      'UPDATE job_listings SET status = ? WHERE id = ? AND user_id = ?',
      [status, req.params.id, req.user.id]
    );
    return res.json({ success: true, message: 'Status updated.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// DELETE /api/jobs/:id
exports.deleteJob = async (req, res) => {
  try {
    await db.query('DELETE FROM job_listings WHERE id = ? AND user_id = ?', [req.params.id, req.user.id]);
    return res.json({ success: true, message: 'Job deleted.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};

// GET /api/jobs/stats
exports.getStats = async (req, res) => {
  try {
    const [rows] = await db.query(
      `SELECT
        COUNT(*) as total_jobs,
        SUM(status='applied') as applied,
        SUM(status='pending') as pending,
        SUM(status='saved') as saved,
        SUM(status='rejected') as rejected
       FROM job_listings WHERE user_id = ?`,
      [req.user.id]
    );
    const [appRows] = await db.query(
      `SELECT
        COUNT(*) as total_apps,
        SUM(status='submitted') as submitted,
        SUM(status='failed') as failed,
        SUM(status='review') as in_review
       FROM applications WHERE user_id = ?`,
      [req.user.id]
    );
    return res.json({ success: true, jobs: rows[0], applications: appRows[0] });
  } catch (err) {
    return res.status(500).json({ success: false, message: 'Server error.' });
  }
};
