"""
AutoJobApply — Flask Automation Microservice
Runs on port 5001. Called by the Node.js backend.

Endpoints:
  GET  /health           — Health check endpoint
  GET  /health/detailed  — Detailed health check with dependencies
  POST /scrape           — Scrape basic job info from a URL
  POST /analyze_form     — Detect form fields on a job application page
  POST /apply            — Fill and submit the job application form
  POST /search_jobs      — Search jobs across multiple platforms
"""

import os
import json
import traceback
import sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
from flask import Flask, request, jsonify
from flask_cors import CORS
from logger_config import logger
from form_filler import scrape_job_page, analyze_form_fields, fill_and_submit_form
from job_searcher import search_linkedin_jobs, search_indeed_jobs, search_ats_jobs, search_naukri_jobs

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health():
    """Basic health check endpoint."""
    return jsonify({
        "success": True,
        "message": "AutoJobApply Automation Service running ✅",
        "service": "automation",
        "status": "healthy"
    })


@app.route('/health/detailed', methods=['GET'])
def health_detailed():
    """Detailed health check with system information."""
    try:
        import playwright
        playwright_version = playwright.__version__
    except ImportError:
        playwright_version = "not installed"

    return jsonify({
        "success": True,
        "service": "automation",
        "status": "healthy",
        "version": "1.0.0",
        "python_version": sys.version,
        "dependencies": {
            "playwright": playwright_version,
            "flask": "installed"
        },
        "environment": {
            "port": os.environ.get('PORT', 5001),
            "form_agent_service": os.environ.get("FORM_AGENT_SERVICE_URL", "http://localhost:5006")
        }
    })


@app.route('/search_jobs', methods=['POST'])
def search():
    """
    Search jobs on a public board.
    Body: { "query": "Software Engineer", "location": "Remote", "source": "indeed",
            "experience_level": "fresher", "job_type": "full-time",
            "easy_apply_only": true, "exclude_urls": ["https://...", ...] }
    source can be "indeed" (default), "linkedin", "ats" (Greenhouse + Lever), or
    "all" (searches every source above and merges/dedupes the results).
    experience_level: "", "fresher", "entry", "mid", "senior"
    job_type: "", "full-time", "part-time", "contract", "internship"
    easy_apply_only (Indeed only): when true, only returns jobs that use Indeed's
    own native "Easily apply" flow, skipping ones that redirect to the company's
    own site — so every result returned can actually be auto-applied end-to-end.
    exclude_urls: job_url values to skip — pass in the URLs you've already shown
    the user (e.g. already tracked in job_listings) so repeated runs surface
    fresh jobs instead of the same top results every time.
    """
    data = request.json or {}
    query = data.get('query', 'Software Engineer')
    location = data.get('location', 'Remote')
    source = (data.get('source') or 'all').lower()
    experience_level = (data.get('experience_level') or '').lower()
    job_type = (data.get('job_type') or '').lower()
    easy_apply_only = bool(data.get('easy_apply_only', False))
    exclude_urls = set(data.get('exclude_urls') or [])

    actual_query = query
    q_lower = actual_query.lower()
    if experience_level == 'fresher' and 'fresher' not in q_lower and 'intern' not in q_lower:
        actual_query += " fresher"
    elif experience_level == 'entry' and not any(k in q_lower for k in ('entry', 'junior', 'associate')):
        actual_query += " entry level"
    elif experience_level == 'senior' and not any(k in q_lower for k in ('senior', 'lead', 'manager', 'principal')):
        actual_query += " senior"
    try:
        excluded_count = 0
        if source == 'all':
            jobs = []
            seen_urls = set()
            for fn in (search_ats_jobs, search_indeed_jobs, search_linkedin_jobs, search_naukri_jobs):
                try:
                    if fn is search_indeed_jobs:
                        found, indeed_excluded = fn(actual_query, location, easy_apply_only=easy_apply_only,
                                                     exclude_urls=exclude_urls, experience_level=experience_level,
                                                     job_type=job_type)
                        excluded_count += indeed_excluded
                    elif fn is search_naukri_jobs:
                        found, naukri_excluded = fn(actual_query, location, exclude_urls=exclude_urls, 
                                                     experience_level=experience_level, job_type=job_type)
                        excluded_count += naukri_excluded
                    elif fn is search_linkedin_jobs:
                        found = fn(actual_query, location, experience_level=experience_level, job_type=job_type)
                    else:
                        found = fn(actual_query, location, experience_level=experience_level, job_type=job_type)
                    for job in found:
                        url = job.get('job_url')
                        if not url or url in seen_urls:
                            continue
                        if url in exclude_urls:
                            excluded_count += 1
                            continue
                        seen_urls.add(url)
                        jobs.append(job)
                except Exception as e:
                    print(f"'all' source: {fn.__name__} failed: {e}")
        elif source == 'linkedin':
            raw = search_linkedin_jobs(actual_query, location, experience_level=experience_level, job_type=job_type)
            jobs = [j for j in raw if j.get('job_url') not in exclude_urls]
            excluded_count = len(raw) - len(jobs)
        elif source in ('ats', 'greenhouse', 'lever'):
            raw = search_ats_jobs(actual_query, location, experience_level=experience_level, job_type=job_type)
            jobs = [j for j in raw if j.get('job_url') not in exclude_urls]
            excluded_count = len(raw) - len(jobs)
        elif source == 'naukri':
            jobs, excluded_count = search_naukri_jobs(actual_query, location, 
                                                       exclude_urls=exclude_urls, experience_level=experience_level,
                                                       job_type=job_type)
        else:
            jobs, excluded_count = search_indeed_jobs(actual_query, location, easy_apply_only=easy_apply_only,
                                                       exclude_urls=exclude_urls, experience_level=experience_level,
                                                       job_type=job_type)
        return jsonify({"success": True, "jobs": jobs, "source": source, "excluded_already_tracked": excluded_count})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Scrape job metadata (title, company, description) from a public job URL.
    Body: { "url": "https://..." }
    """
    data = request.json or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400

    try:
        job_info = scrape_job_page(url)
        return jsonify({"success": True, "job": job_info})
    except Exception as e:
        logger.error(f"Error in /scrape endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/analyze_form', methods=['POST'])
def analyze_form():
    """
    Detect visible form fields on a job application page.
    Body: { "url": "https://..." }
    Returns list of detected fields with their labels/types.
    """
    data = request.json or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400

    try:
        fields = analyze_form_fields(url)
        return jsonify({"success": True, "fields": fields})
    except Exception as e:
        logger.error(f"Error in /analyze_form endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/apply', methods=['POST'])
def apply_job():
    """
    Fill and submit a job application form using Playwright.
    Body: {
        "session_id": int,
        "application_id": int,
        "user_id": int,
        "job_id": int,
        "job_url": str,
        "form_data": { first_name, last_name, email, phone, ... },
        "custom_qa": [ { question, answer, type }, ... ],
        "cover_letter": str,
        "resume_path": str (optional),
        "resume_text": str (optional)
    }
    user_id/job_id are used to attribute any questions escalated to the
    Human-in-the-Loop Review Queue (form_agent) while the browser is paused.
    resume_text: the applicant's parsed resume text — passed through to AI
    answer generation (generate_ai_answer) so unmapped questions get
    answered from real resume content, not just the structured form_data
    fields (name/email/experience_years/skills).
    """
    data = request.json or {}
    job_url     = data.get('job_url', '')
    form_data   = data.get('form_data', {})
    custom_qa   = data.get('custom_qa', [])
    cover_letter = data.get('cover_letter', '')
    resume_path  = data.get('resume_path', None)
    resume_text  = data.get('resume_text', '') or ''
    user_id      = data.get('user_id', None)
    job_id       = data.get('job_id', None)
    session_id   = data.get('session_id', None)

    if not job_url:
        return jsonify({"success": False, "message": "job_url is required"}), 400

    try:
        logger.info(f"Starting job application for user {user_id}, job {job_id}, session {session_id}")
        result = fill_and_submit_form(
            url=job_url,
            form_data=form_data,
            custom_qa=custom_qa,
            cover_letter=cover_letter,
            resume_path=resume_path,
            user_id=user_id,
            job_id=job_id,
            resume_text=resume_text
            # session_id=session_id omitted to enforce direct use of persistent profile
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /apply endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    port = 5001
    logger.info(f"\n🤖 AutoJobApply Automation Service starting on http://localhost:{port}\n")
    # threaded=True: /apply can now legitimately block for many minutes while
    # paused on a login wall or a review-queue answer — without this, that one
    # long request would freeze /health and every other concurrent request.
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)