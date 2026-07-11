const db = require('../config/db');
const axios = require('axios');
const { deriveSearchQuery, scoreJob, getUserSkills } = require('../utils/matcher');
require('dotenv').config();

/**
 * POST /api/agent/run
 * The AI agent:
 *   1. Reads the user's resume-derived profile (skills, experience, headline)
 *   2. Searches Indeed for matching jobs
 *   3. Scores every job against the resume (fit_score + matched/missing skills)
 *   4. Saves the shortlist and returns it, ranked best-first, for the user to approve
 *
 * Body (all optional — sensible defaults come from the profile):
 *   { query, location, source, min_score, limit, easy_apply_only }
 */
exports.runAgent = async (req, res) => {
  try {
    const [users] = await db.query('SELECT * FROM users WHERE id = ?', [req.user.id]);
    const [profiles] = await db.query('SELECT * FROM user_profiles WHERE user_id = ?', [req.user.id]);
    const user = users[0];
    const profile = profiles[0] || {};

    // Guard: the agent needs *something* to match against.
    const userSkills = getUserSkills(profile);
    if (userSkills.size === 0 && !profile.headline) {
      return res.status(400).json({
        success: false,
        message: 'Please upload your resume / fill your Profile first so the agent knows what to search for.',
      });
    }

    const query    = (req.body.query || deriveSearchQuery(user, profile)).trim();
    const location  = (req.body.location || user.location || 'Remote').trim();
    const source    = (req.body.source || 'indeed').toLowerCase();
    const minScore  = Number.isFinite(+req.body.min_score) ? +req.body.min_score : 40;
    const limit     = Math.min(parseInt(req.body.limit || 15, 10), 25);
    const easyApplyOnly = !!req.body.easy_apply_only;

    // Already-tracked job URLs for this user — passed as exclude_urls so the
    // automation service doesn't keep resurfacing the same jobs every run.
    const [trackedRows] = await db.query(
      'SELECT job_url FROM job_listings WHERE user_id = ?',
      [req.user.id]
    );
    const excludeUrls = trackedRows.map(r => r.job_url).filter(Boolean);

    // ── Step 1+2: ask the automation service to fetch job listings ──
    let rawJobs = [];
    let excludedAlreadyTracked = 0;
    try {
      const resp = await axios.post(
        `${process.env.AUTOMATION_SERVICE_URL}/search_jobs`,
        { query, location, source, easy_apply_only: easyApplyOnly, exclude_urls: excludeUrls },
        // LinkedIn/Indeed now visit each job's own page for its full
        // description (needed for accurate scoring), which is much slower
        // than scraping search cards alone — especially for source "all".
        { timeout: 240000 }
      );
      if (resp.data?.success) {
        rawJobs = resp.data.jobs || [];
        excludedAlreadyTracked = resp.data.excluded_already_tracked || 0;
      }
    } catch (e) {
      console.error('Agent: automation search failed:', e.message);
      return res.status(502).json({
        success: false,
        message: 'Job search service is unreachable. Make sure the Python automation service (port 5001) is running.',
      });
    }

    if (!rawJobs.length) {
      const message = excludedAlreadyTracked > 0
        ? `Found ${excludedAlreadyTracked} matching job${excludedAlreadyTracked === 1 ? '' : 's'} for "${query}" in "${location}", but you've already seen ${excludedAlreadyTracked === 1 ? 'it' : 'all of them'}. Try a broader location/query, uncheck Easy Apply only, or switch source to "All Sources".`
        : `No jobs came back for "${query}" in "${location}". The board may have blocked the request — try again or tweak the query.`;
      return res.json({
        success: true,
        query, location, source,
        matches: [],
        message,
      });
    }

    // ── Step 3: score every job, keep the ones above the threshold ──
    const scored = rawJobs
      .map(job => ({ job, ...scoreJob(profile, job) }))
      .filter(s => s.fit_score >= minScore)
      .sort((a, b) => b.fit_score - a.fit_score)
      .slice(0, limit);

    // ── Step 4: persist the shortlist as job_listings (dedupe by URL) ──
    const matches = [];
    for (const s of scored) {
      const { job } = s;
      const matchData = {
        fit_score: s.fit_score,
        matched_skills: s.matched,
        missing_skills: s.missing,
        easy_apply: !!job.easy_apply,
      };

      // Skip if we already tracked this exact job URL for this user.
      const [existing] = await db.query(
        'SELECT id, status FROM job_listings WHERE user_id = ? AND job_url = ? LIMIT 1',
        [req.user.id, job.job_url]
      );

      let jobId;
      if (existing.length) {
        jobId = existing[0].id;
        await db.query('UPDATE job_listings SET requirements = ? WHERE id = ?',
          [JSON.stringify(matchData), jobId]);
      } else {
        const [result] = await db.query(
          `INSERT INTO job_listings
            (user_id, title, company, location, job_url, source, description, job_type, requirements, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')`,
          [
            req.user.id,
            job.title || 'Untitled Job',
            job.company || 'Unknown Company',
            job.location || location,
            job.job_url,
            `ai_agent:${source}`,
            job.description || null,
            job.job_type || null,
            JSON.stringify(matchData),
          ]
        );
        jobId = result.insertId;
      }

      matches.push({
        job_id: jobId,
        title: job.title,
        company: job.company,
        location: job.location || location,
        job_url: job.job_url,
        description: job.description || '',
        already_tracked: existing.length > 0,
        ...matchData,
      });
    }

    return res.json({
      success: true,
      query, location, source,
      searched: rawJobs.length,
      shortlisted: matches.length,
      matches,
    });
  } catch (err) {
    console.error('runAgent error:', err);
    return res.status(500).json({ success: false, message: 'Server error while running the agent.' });
  }
};