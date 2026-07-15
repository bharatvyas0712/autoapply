"""
AutoJobApply — Playwright Form Filler Engine

Handles:
  1. Scraping job metadata (title, company, description)
  2. Analyzing application form fields
  3. Filling and submitting application forms automatically

Supports: Greenhouse, Lever, Workday, generic job portals
"""

import os
import re
import time
import json
import base64
import shutil
import threading
import traceback
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from logger_config import logger
from retry_utils import retry_with_backoff, retry_operation
FORM_AGENT_SERVICE_URL = os.environ.get("FORM_AGENT_SERVICE_URL", "http://localhost:5006")
HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG — all pause/timeout knobs are env-configurable, no hardcoded magic numbers
# ──────────────────────────────────────────────────────────────────────────────
LOGIN_WAIT_TIMEOUT_SECONDS = int(os.environ.get("AUTOJOBAPPLY_LOGIN_WAIT_SECONDS", 60))          # 1 min
LOGIN_POLL_INTERVAL_SECONDS = int(os.environ.get("AUTOJOBAPPLY_LOGIN_POLL_INTERVAL_SECONDS", 3))
FIELD_REVIEW_TIMEOUT_SECONDS = int(os.environ.get("AUTOJOBAPPLY_FIELD_REVIEW_TIMEOUT_SECONDS", 900))  # 15 min
REVIEW_POLL_INTERVAL_SECONDS = int(os.environ.get("AUTOJOBAPPLY_REVIEW_POLL_INTERVAL_SECONDS", 5))

# The shared persistent Chrome profile (see get_shared_profile_dir/launch_logged_in_context
# below) can only be driven by one browser process at a time — a second concurrent
# launch against the same user_data_dir corrupts the browser connection instead of
# cleanly failing. The Flask app runs threaded (so /health etc. stay responsive during
# a long pause), so this lock serializes actual browser runs: a second /apply call
# waits its turn instead of racing the first one for the same profile.
# Now using per-user profile locks for parallel applications.
_profile_locks = {}
_profile_locks_lock = threading.Lock()

def _get_profile_lock(user_id: int = None, session_id: int = None) -> threading.Lock:
    """
    Get or create a lock for a browser profile.
    When session_id is given, the lock is session-scoped — enabling parallel
    applications for the same user with full profile isolation.
    Falls back to user-level locking when session_id is absent.
    """
    if session_id:
        profile_key = f"session_{session_id}"
    elif user_id:
        profile_key = f"user_{user_id}"
    else:
        profile_key = "default"
    with _profile_locks_lock:
        if profile_key not in _profile_locks:
            _profile_locks[profile_key] = threading.Lock()
        return _profile_locks[profile_key]


# ──────────────────────────────────────────────────────────────────────────────
# SCRAPE JOB METADATA
# ──────────────────────────────────────────────────────────────────────────────
@retry_with_backoff(max_attempts=3, base_delay=2.0, retryable_exceptions=(PlaywrightTimeoutError, Exception))
def scrape_job_page(url: str) -> dict:
    """
    Visit a job posting URL and extract: title, company, location, description.
    """
    logger.info(f"Scraping job page: {url}")
    result = {
        "title": "Job from URL",
        "company": "",
        "location": "",
        "description": "",
        "job_type": "",
        "salary_range": ""
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        page = ctx.new_page()

        try:
            page.goto(
                    url,
                    timeout=60000,
                    wait_until="domcontentloaded"
                    )

            page.wait_for_timeout(3000)
            

            # Try common selectors for different job platforms
            title_selectors = [
                'h1', '[data-automation="job-detail-title"]',
                '.job-title', '.posting-headline h2', '[class*="JobTitle"]',
                'h2.title', '[itemprop="title"]'
            ]
            for sel in title_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        result["title"] = el.inner_text().strip()
                        logger.debug(f"Found title: {result['title']}")
                        break
                except Exception:
                    continue

            company_selectors = [
                '[data-automation="job-detail-company"]', '.company-name',
                '[class*="CompanyName"]', '[itemprop="hiringOrganization"]',
                '.employer-name', '.posting-categories .sort-by-team'
            ]
            for sel in company_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        result["company"] = el.inner_text().strip()
                        logger.debug(f"Found company: {result['company']}")
                        break
                except Exception:
                    continue

            location_selectors = [
                '[data-automation="job-detail-location"]', '.location',
                '[class*="Location"]', '[itemprop="jobLocation"]',
                '.job-location'
            ]
            for sel in location_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        result["location"] = el.inner_text().strip()
                        logger.debug(f"Found location: {result['location']}")
                        break
                except Exception:
                    continue

            desc_selectors = [
                '.job-description', '[data-automation="jobDescriptionHTMLOutput"]',
                '#job-description', '.description__text', '[class*="JobDescription"]',
                'article', '.posting-description'
            ]
            for sel in desc_selectors:
                try:
                    el = page.query_selector(sel)
                    if el:
                        text = el.inner_text().strip()
                        if len(text) > 50:
                            result["description"] = text[:2000]
                            logger.debug(f"Found description (length: {len(text)})")
                            break
                except Exception:
                    continue

        except PlaywrightTimeoutError:
            logger.warning(f"Page timeout while scraping: {url}")
            result["description"] = "Page timed out — metadata may be incomplete."
        except Exception as e:
            logger.error(f"Error scraping job page: {str(e)}")
            raise
        finally:
            browser.close()

    logger.info(f"Successfully scraped job: {result['title']} at {result['company']}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# ANALYZE FORM FIELDS
# ──────────────────────────────────────────────────────────────────────────────
@retry_with_backoff(max_attempts=3, base_delay=2.0, retryable_exceptions=(PlaywrightTimeoutError, Exception))
def analyze_form_fields(url: str) -> list:
    """
    Detect the form fields present on a job application page.
    Returns list of: { label, type, name, required, options }
    """
    logger.info(f"Analyzing form fields for: {url}")
    fields = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        page = ctx.new_page()

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Extract all input, select, textarea elements
            form_elements = page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="search"]), select, textarea');
                    const results = [];
                    elements.forEach(el => {
                        let label = '';
                        // Try to find associated label
                        if (el.id) {
                            const lab = document.querySelector(`label[for="${el.id}"]`);
                            if (lab) label = lab.innerText.trim();
                        }
                        if (!label && el.placeholder) label = el.placeholder;
                        if (!label && el.name) label = el.name.replace(/[_-]/g, ' ');
                        if (!label && el.getAttribute('aria-label')) label = el.getAttribute('aria-label');
                        
                        const options = [];
                        if (el.tagName === 'SELECT') {
                            el.querySelectorAll('option').forEach(opt => {
                                if (opt.value) options.push({ value: opt.value, text: opt.text });
                            });
                        }
                        
                        results.push({
                            label: label,
                            type: el.type || el.tagName.toLowerCase(),
                            name: el.name || el.id || '',
                            required: el.required,
                            options: options
                        });
                    });
                    return results;
                }
            """)

            fields = [f for f in form_elements if f.get('label') or f.get('name')]
            logger.info(f"Detected {len(fields)} form fields")

        except PlaywrightTimeoutError:
            logger.warning(f"Timeout analyzing form fields for: {url}")
        except Exception as e:
            logger.error(f"Error analyzing form fields: {str(e)}")
            raise
        finally:
            browser.close()

    return fields


# ──────────────────────────────────────────────────────────────────────────────
class OneClickApplySuccess(Exception):
    """Raised when a job board 1-click apply completes without needing a form."""
    pass

# ──────────────────────────────────────────────────────────────────────────────
# FILL AND SUBMIT FORM
# ──────────────────────────────────────────────────────────────────────────────
def fill_and_submit_form(
    url: str,
    form_data: dict,
    custom_qa: list,
    cover_letter: str,
    resume_path: str = None,
    user_id: int = None,
    job_id: int = None,
    resume_text: str = "",
    session_id: int = None
) -> dict:
    """
    Thin wrapper that serializes access to the user's browser profile (see
    _get_profile_lock) before handing off to the real implementation below —
    only one real browser run can use the same profile at a time.
    Different users can run in parallel with separate profiles.
    """
    profile_lock = _get_profile_lock(user_id=user_id, session_id=session_id)
    wait_start = time.time()
    if profile_lock.locked():
        logger.info(f"Another application for user {user_id or 'default'} is using the browser profile — waiting for it to finish...")
    with profile_lock:
        waited = time.time() - wait_start
        if waited > 1:
            logger.info(f"Acquired the browser profile for user {user_id or 'default'} after waiting {waited:.0f}s.")
        return _fill_and_submit_form_impl(
            url, form_data, custom_qa, cover_letter, resume_path, user_id, job_id, resume_text, session_id
        )


def _fill_and_submit_form_impl(
    url: str,
    form_data: dict,
    custom_qa: list,
    cover_letter: str,
    resume_path: str = None,
    user_id: int = None,
    job_id: int = None,
    resume_text: str = "",
    session_id: int = None
) -> dict:
    """
    Navigate to the job application URL and:
    1. Fill all detected text fields using keyword matching
    2. Handle Yes/No radio buttons and dropdowns
    3. Upload resume if a file path is provided
    4. Submit the form
    5. Capture a screenshot

    Fields with no confident keyword match (and checkboxes/radio groups with no
    match) are escalated to the Human-in-the-Loop Review Queue (form_agent's
    ReviewQueue over HTTP) and the browser is paused in place until you answer
    via review.html or a configurable timeout elapses.
    """
    log = []
    screenshot_b64 = None
    steps_done = 0
    steps_total = 10

    def add_log(msg, status="ok"):
        log_entry = {"time": datetime.now().isoformat(), "message": msg, "status": status}
        log.append(log_entry)
        if status == "ok":
            logger.info(msg)
        elif status == "warn":
            logger.warning(msg)
        elif status == "error":
            logger.error(msg)
        else:
            logger.debug(msg)

        if session_id:
            try:
                backend_url = os.environ.get("BACKEND_API_URL", "http://localhost:3000")
                requests.post(
                    f"{backend_url}/api/applications/sessions/{session_id}/log",
                    json={
                        "log_entry": log_entry,
                        "steps_completed": steps_done,
                        "steps_total": steps_total
                    },
                    timeout=5
                )
            except Exception as e:
                logger.warning(f"Failed to push log to backend: {e}")

    with sync_playwright() as p:
        # Use the ONE shared, logged-in profile so we reuse the sessions you
        # already established on LinkedIn / Indeed / etc. — no re-login.
        ctx = launch_logged_in_context(p, headless=HEADLESS, slow_mo=300, user_id=user_id, session_id=session_id)
        page = ctx.new_page()

        did_manual_login = False
        try:
            add_log(f"Opening URL: {url}")
            page.goto(
                url,
                timeout=60000,
                wait_until="domcontentloaded"
            )
            page.wait_for_timeout(3000)
            steps_done = 1
            add_log("Page loaded successfully.")

            # ── Check for CAPTCHA ───────────────────────────────────────────
            if _detect_captcha(page):
                add_log("CAPTCHA/anti-bot challenge detected! Application blocked.", "error")
                return {"success": False, "status": "captcha_blocked", "message": "CAPTCHA challenge detected - manual intervention required", "log": log, "steps_done": steps_done, "steps_total": steps_total}

            # ── Check for Login Wall ───────────────────────────────────────
            def wait_for_login(target_page):
                """Returns True once clear to proceed, False if the login wait timed out."""
                if not _is_login_wall(target_page):
                    return True
                add_log(
                    f"Login page detected! Waiting up to {LOGIN_WAIT_TIMEOUT_SECONDS}s "
                    f"for you to log in manually in this window...", "warn"
                )
                elapsed = 0
                while elapsed < LOGIN_WAIT_TIMEOUT_SECONDS:
                    target_page.wait_for_timeout(LOGIN_POLL_INTERVAL_SECONDS * 1000)
                    elapsed += LOGIN_POLL_INTERVAL_SECONDS
                    # Update status for frontend
                    add_log(f"Waiting for manual login... (elapsed {elapsed}s / {LOGIN_WAIT_TIMEOUT_SECONDS}s)", "info")
                    if not _is_login_wall(target_page):
                        add_log("Login detected complete — resuming form fill.")
                        target_page.wait_for_timeout(2000)
                        return "manual_login"
                add_log(f"Timeout reached after {LOGIN_WAIT_TIMEOUT_SECONDS}s waiting for manual login.", "error")
                return False

            login_res = wait_for_login(page)
            if not login_res:
                return {"success": False, "status": "login_timeout", "message": "Manual login required but timed out.", "log": log, "steps_done": steps_done, "steps_total": steps_total}
            
            if login_res == "manual_login":
                did_manual_login = True

            # ── Reach the real application form ────────────────────────────
            # Job-board URLs (LinkedIn "jobs/view/...", Indeed "viewjob?...") land
            # on the job DESCRIPTION page, not the application form — the form is
            # behind an Apply/Easy Apply click, sometimes opening in a new tab.
            # Direct ATS links (Greenhouse/Lever) already ARE the form, so this is
            # a no-op for those (detected by already having fillable fields).
            
            # Check if this is a known multi-step wizard URL (LinkedIn/Indeed/Naukri)
            url_lower = url.lower()
            is_multi_step_url = any(pattern in url_lower for pattern in KNOWN_LISTING_URL_PATTERNS)
            
            try:
                page = _click_apply_and_switch(ctx, page, add_log, is_multi_step=is_multi_step_url)
            except OneClickApplySuccess:
                return {"success": True, "message": "Naukri 1-click apply was successful!", "log": log, "steps_done": steps_total, "steps_total": steps_total}
            
            if not wait_for_login(page):
                return {"success": False, "message": "Manual login required but timed out.", "log": log, "steps_done": steps_done, "steps_total": steps_total}
            
            # Check for CAPTCHA after clicking Apply
            if _detect_captcha(page):
                add_log("CAPTCHA/anti-bot challenge detected after clicking Apply! Application blocked.", "error")
                return {"success": False, "status": "captcha_blocked", "message": "CAPTCHA challenge detected - manual intervention required", "log": log, "steps_done": steps_done, "steps_total": steps_total}
            
            # Handle multi-step wizard for LinkedIn/Indeed/Naukri
            if is_multi_step_url and _is_multi_step_wizard(page):
                add_log("Detected multi-step modal wizard (LinkedIn / Indeed / Naukri) - entering wizard mode")
                wizard_success = _fill_multi_step_wizard(page, form_data, custom_qa, cover_letter, resume_path, add_log, user_id, job_id, resume_text)
                if not wizard_success:
                    add_log("Multi-step wizard failed - proceeding with standard form fill", "warn")
                else:
                    add_log("Multi-step wizard completed successfully")
                    # After wizard, we should be on the final submit/review page
                    # Continue with standard submission logic

            # ── Field Detection Context ─────────────────────────────────────
            # If the application form is embedded inside an iframe (like on many
            # company sites using Greenhouse/Lever), we drive that iframe instead
            # of the main page context.
            form_context = get_form_context(page)

            # ── Field Detection Inventory ──────────────────────────────────
            _log_field_inventory(form_context, add_log)

            # ── Fill Text/Email/Tel/Number Inputs ─────────────────────────
            add_log("Filling standard text fields...")
            field_map = build_field_map(form_data, cover_letter)

            # type="search" is excluded: job boards (Greenhouse, LinkedIn, Indeed, Naukri, ...)
            # all carry their own site-search box unrelated to the application —
            # without this it gets mistaken for an unmapped application question.
            inputs = form_context.query_selector_all('input:not([type="hidden"]):not([type="submit"]):not([type="file"]):not([type="search"]), textarea')
            for inp in inputs:
                try:
                    if not inp.is_visible():
                        continue
                    label_text = get_field_label(form_context, inp).lower()
                    if any(x in label_text for x in ('recaptcha', 'captcha', 'csrf')):
                        continue
                    field_type = (inp.get_attribute('type') or 'text').lower()
                    
                    if field_type in ('checkbox', 'radio', 'button', 'reset'):
                        continue

                    matched_value = match_field_value(label_text, inp.get_attribute('name') or '', inp.get_attribute('placeholder') or '', field_map)

                    if matched_value == "__SKIP__":
                        add_log(f"  Explicitly skipping '{label_text}'")
                        continue
                    elif matched_value is not None and matched_value != "":
                        inp.scroll_into_view_if_needed()
                        inp.click(click_count=3)
                        inp.type(str(matched_value), delay=40)
                        add_log(f"  Filled: '{label_text}' → '{str(matched_value)[:50]}'")
                    elif label_text.strip():
                        add_log(f"  Unmapped field: '{label_text}' -> pausing for your review")
                        answer = _resolve_via_review_queue(page, add_log, user_id, job_id, label_text, form_data, resume_text)
                        if answer:
                            inp.scroll_into_view_if_needed()
                            inp.click(click_count=3)
                            inp.type(str(answer), delay=40)
                            add_log(f"  Resumed — filled '{label_text}' with your answer.")
                        else:
                            add_log(f"  Leaving '{label_text}' blank and continuing.", "warn")
                except Exception as e:
                    add_log(f"  Skipped input: {str(e)}", "warn")
            steps_done = 3

            # ── Handle Select Dropdowns ───────────────────────────────────
            add_log("Handling dropdowns...")
            selects = form_context.query_selector_all('select')
            for sel in selects:
                try:
                    if not sel.is_visible():
                        continue
                    label_text = get_field_label(form_context, sel).lower()
                    name_attr  = (sel.get_attribute('name') or '').lower()
                    
                    if any(k in label_text or k in name_attr for k in ['country', 'citizenship', 'location']):
                        # Try to select a sensible default
                        try_select_option(form_context, sel, ['United States', 'US', 'India', 'Other'], add_log)
                    elif any(k in label_text or k in name_attr for k in ['experience', 'year']):
                        try_select_option(form_context, sel, [str(form_data.get('experience_years', '1')), '1-3 years', '1+ year'], add_log)
                    elif any(k in label_text or k in name_attr for k in ['gender']):
                        try_select_option(form_context, sel, ['Prefer not to say', 'Not specified', 'Other'], add_log)
                    elif any(k in label_text or k in name_attr for k in ['ethnicity', 'race']):
                        try_select_option(form_context, sel, ['Decline to self identify', 'Prefer not to say'], add_log)
                    elif any(k in label_text or k in name_attr for k in ['disability']):
                        try_select_option(form_context, sel, ['No', 'I do not have a disability', 'Not disabled'], add_log)
                    elif any(k in label_text or k in name_attr for k in ['veteran']):
                        try_select_option(form_context, sel, ['No', 'I am not a protected veteran', 'Not a veteran'], add_log)
                    elif label_text.strip():
                        options = sel.query_selector_all('option')
                        opt_texts = [o.inner_text().strip() for o in options if o.get_attribute('value')]
                        if opt_texts:
                            prompt = f"{label_text} (Options: {', '.join(opt_texts)})"
                            add_log(f"  Unmapped select: '{label_text}' -> asking AI")
                            answer = _resolve_via_review_queue(page, add_log, user_id, job_id, prompt, form_data, resume_text)
                            if answer:
                                try_select_option(form_context, sel, [answer], add_log)
                            else:
                                add_log(f"  Leaving '{label_text}' unset.", "warn")
                except Exception as e:
                    add_log(f"  Skipped select: {str(e)}", "warn")
            steps_done = 5

            # ── Handle Standalone Checkboxes ──────────────────────────────
            add_log("Handling checkboxes...")
            consent_keywords = ['agree', 'consent', 'terms', 'privacy policy', 'acknowledge', 'confirm that']
            checkboxes = form_context.query_selector_all('input[type="checkbox"]')
            for cb in checkboxes:
                try:
                    if not cb.is_visible():
                        continue
                    label_text = get_field_label(form_context, cb).lower().strip()
                    if any(kw in label_text for kw in ('email updates', 'job alert', 'subscribe', 'newsletter', 'receive updates', 'send me')):
                        add_log(f"  Skipping marketing/alert checkbox: '{label_text}'")
                        continue
                    if cb.is_checked():
                        continue
                    if any(kw in label_text for kw in consent_keywords):
                        cb.check(force=True)
                        add_log(f"  Checked consent box: '{label_text}'")
                    elif label_text:
                        add_log(f"  Unmapped checkbox: '{label_text}' -> pausing for your review")
                        answer = _resolve_via_review_queue(page, add_log, user_id, job_id, f"Check this box? {label_text}", form_data, resume_text)
                        if answer and answer.strip().lower() in ('yes', 'y', 'true', 'check', 'checked'):
                            cb.check(force=True)
                            add_log(f"  Resumed — checked '{label_text}' per your answer.")
                        else:
                            add_log(f"  Leaving '{label_text}' unchecked and continuing.", "warn")
                except Exception as e:
                    add_log(f"  Skipped checkbox: {str(e)}", "warn")

            # ── Handle Custom Q&A (Yes/No Radios) ────────────────────────
            add_log("Answering Yes/No questions from Q&A defaults...")
            for qa_item in custom_qa:
                question = (qa_item.get('question') or '').lower()
                answer   = (qa_item.get('answer') or 'No').strip()
                try:
                    # Find radio buttons matching this question
                    radios = form_context.query_selector_all('input[type="radio"]')
                    for radio in radios:
                        if not radio.is_visible():
                            continue
                        radio_label = get_field_label(form_context, radio).strip()
                        parent_text = ''
                        try:
                            parent = radio.evaluate('el => el.closest("fieldset, .form-group, [role=group]")?.innerText || ""')
                            parent_text = parent.lower()
                        except Exception:
                            pass

                        if any(kw in parent_text or kw in question for kw in _question_keywords(question)):
                            if radio_label.lower() in (answer.lower(), answer.lower()[:2]):
                                radio.check(force=True)
                                add_log(f"  Answered: '{qa_item.get('question', '')[:60]}' → {answer}")
                                break
                except Exception as e:
                    add_log(f"  QA skip: {str(e)}", "warn")

            # ── Escalate Radio Groups Left Unanswered by custom_qa ────────
            add_log("Checking for unanswered radio groups...")
            try:
                all_radios = form_context.query_selector_all('input[type="radio"]')
                groups = {}
                for radio in all_radios:
                    if not radio.is_visible():
                        continue
                    name_attr = radio.get_attribute('name') or ''
                    if not name_attr:
                        continue
                    groups.setdefault(name_attr, []).append(radio)

                for name_attr, radios in groups.items():
                    try:
                        if any(r.is_checked() for r in radios):
                            continue
                        group_label = _get_radio_group_label(radios[0]) or name_attr
                        option_labels = [get_field_label(form_context, r).strip() for r in radios]
                        question_text = f"{group_label} (options: {', '.join(o for o in option_labels if o)})"
                        add_log(f"  Unanswered radio group: '{group_label}' -> pausing for your review")
                        answer = _resolve_via_review_queue(page, add_log, user_id, job_id, question_text, form_data, resume_text)
                        if answer:
                            chosen = None
                            for r, opt_label in zip(radios, option_labels):
                                if opt_label and (opt_label.lower() in answer.lower() or answer.lower() in opt_label.lower()):
                                    chosen = r
                                    break
                            if chosen:
                                chosen.check(force=True)
                                add_log(f"  Resumed — selected '{group_label}' option per your answer.")
                            else:
                                add_log(f"  Could not match your answer to an option for '{group_label}'; leaving unset.", "warn")
                        else:
                            add_log(f"  Leaving radio group '{group_label}' unset and continuing.", "warn")
                    except Exception as e:
                        add_log(f"  Radio group skip: {str(e)}", "warn")
            except Exception as e:
                add_log(f"  Radio group scan skipped: {str(e)}", "warn")

            steps_done = 7

            # ── Upload Resume ─────────────────────────────────────────────
            if resume_path and os.path.exists(resume_path):
                add_log(f"Uploading resume: {resume_path}")
                try:
                    file_inputs = form_context.query_selector_all('input[type="file"]')
                    if file_inputs:
                        file_inputs[0].set_input_files(resume_path)
                        page.wait_for_timeout(1500)
                        add_log("  Resume uploaded successfully.")
                    else:
                        add_log("  No file input found on page.", "warn")
                except Exception as e:
                    add_log(f"  Resume upload failed: {str(e)}", "warn")
            steps_done = 8

            # ── Take Screenshot before Submit ─────────────────────────────
            add_log("Taking pre-submission screenshot...")
            screenshot_bytes = page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Save screenshot to disk
            ss_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'uploads', 'screenshots')
            os.makedirs(ss_dir, exist_ok=True)
            ss_filename = f"app_{int(time.time())}.png"
            ss_path = os.path.join(ss_dir, ss_filename)
            with open(ss_path, 'wb') as f:
                f.write(screenshot_bytes)
            screenshot_url = f"/uploads/screenshots/{ss_filename}"
            steps_done = 9

            # ── Check for Captcha & Manual Pause ──────────────────────────
            try:
                captcha_detected = len(page.query_selector_all('iframe[src*="recaptcha"], iframe[title*="recaptcha"], .g-recaptcha, iframe[src*="hcaptcha"]')) > 0
                if not captcha_detected and form_context != page:
                    captcha_detected = len(form_context.query_selector_all('iframe[src*="recaptcha"], iframe[title*="recaptcha"], .g-recaptcha, iframe[src*="hcaptcha"]')) > 0
                
                if captcha_detected:
                    add_log("Detected reCAPTCHA/Captcha. Please solve it manually. Click 'CONTINUE AUTOMATION' at the top when done.", "warn")
                    page.evaluate("""
                        let btn = document.createElement('button');
                        btn.innerHTML = 'CONTINUE AUTOMATION';
                        btn.id = 'automation-resume-btn';
                        btn.style.position = 'fixed';
                        btn.style.top = '10px';
                        btn.style.left = '50%';
                        btn.style.transform = 'translateX(-50%)';
                        btn.style.zIndex = '9999999';
                        btn.style.padding = '15px 30px';
                        btn.style.fontSize = '20px';
                        btn.style.fontWeight = 'bold';
                        btn.style.background = '#e74c3c';
                        btn.style.color = 'white';
                        btn.style.border = '2px solid white';
                        btn.style.borderRadius = '8px';
                        btn.style.cursor = 'pointer';
                        btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
                        btn.onclick = function() { window.automationResumed = true; btn.remove(); };
                        document.body.appendChild(btn);
                        window.automationResumed = false;
                    """)
                    
                    # Wait up to 3 minutes for user to click
                    for _ in range(180):
                        if page.evaluate("window.automationResumed"):
                            break
                        page.wait_for_timeout(1000)
                    add_log("Resuming after manual Captcha check.")
            except Exception as e:
                add_log(f"Captcha detection error: {str(e)}", "warn")

            # ── Click Submit Button ───────────────────────────────────────
            add_log("Looking for submit button...")
            submit_sel = find_submit_button(form_context)
            if submit_sel:
                add_log("  Submit button found — clicking.")
                try:
                    # Avoid strict mode violation by resolving to a single visible locator
                    btn_locator = form_context.locator(submit_sel)
                    target_locator = None
                    for i in range(btn_locator.count()):
                        loc = btn_locator.nth(i)
                        if loc.is_visible():
                            target_locator = loc
                            break
                    if not target_locator:
                        target_locator = btn_locator.first

                    target_locator.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    target_locator.click(timeout=10000)
                    page.wait_for_timeout(4000)
                    add_log("  Form submitted!")
                    steps_done = 10
                except Exception as e:
                    add_log(f"  Click failed: {str(e)} — attempting fallback JS click...", "warn")
                    try:
                        # Re-locate to ensure we evaluate on a single visible element
                        btn_locator = form_context.locator(submit_sel)
                        target_locator = None
                        for i in range(btn_locator.count()):
                            loc = btn_locator.nth(i)
                            if loc.is_visible():
                                target_locator = loc
                                break
                        if not target_locator:
                            target_locator = btn_locator.first

                        target_locator.scroll_into_view_if_needed()
                        target_locator.evaluate("el => el.click()")
                        page.wait_for_timeout(4000)
                        add_log("  Form submitted via fallback JS click!")
                        steps_done = 10
                    except Exception as js_err:
                        add_log(f"  Fallback JS click failed: {str(js_err)}", "error")
                        raise js_err
            else:
                add_log("  No submit button found automatically. Manual submit required.", "warn")

        

            return {
                "success": True,
                "log": log,
                "steps_done": steps_done,
                "steps_total": steps_total,
                "screenshot": screenshot_url if screenshot_url else None
            }

        except PlaywrightTimeoutError as e:
            add_log(f"Page timed out: {str(e)}", "error")
            logger.error(f"Playwright timeout: {str(e)}")
            return {"success": False, "message": f"Timeout: {str(e)}", "log": log, "steps_done": steps_done, "steps_total": steps_total}

        except Exception as e:
            traceback_str = traceback.format_exc()
            add_log(f"Unhandled error: {str(e)}", "error")
            logger.error(f"Unhandled error in form filling: {str(e)}\n{traceback_str}")
            return {"success": False, "message": str(e), "log": log, "steps_done": steps_done, "steps_total": steps_total}

        finally:
            # Always close the persistent context so the browser process is
            # released and the profile lock on `playwright_profile` is freed —
            # otherwise every subsequent /apply call fails ("profile in use").
            try:
                ctx.close()
            except Exception:
                pass

            # Clean up ephemeral session profile directory to avoid disk accumulation.
            # Persistent user profiles (user_id only) are intentionally kept.
            if session_id:
                session_profile = get_shared_profile_dir(user_id=user_id, session_id=session_id)
                if did_manual_login and user_id:
                    # The user logged in manually during this ephemeral session!
                    # Sync the new cookies/session back to the persistent user profile.
                    try:
                        user_profile = os.path.join(project_root, "browser_profiles", f"user_{user_id}")
                        shutil.rmtree(user_profile, ignore_errors=True)
                        shutil.copytree(session_profile, user_profile)
                        logger.info(f"Saved manual login: copied session profile back to user profile")
                    except Exception as e:
                        logger.warning(f"Failed to save manual login back to user profile: {e}")
                
                try:
                    shutil.rmtree(session_profile, ignore_errors=True)
                    logger.info(f"Cleaned up ephemeral session profile: {session_profile}")
                except Exception as e:
                    logger.warning(f"Failed to clean up session profile {session_profile}: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def get_shared_profile_dir(user_id: int = None, session_id: int = None) -> str:
    """
    Absolute path to a persistent browser profile.

    Priority:
      1. AUTOJOBAPPLY_PROFILE_DIR env-override (shared/debug use)
      2. session_id  → ephemeral per-job profile  (browser_profiles/session_<id>/)
                       Gives full isolation so N jobs for the same user run in
                       parallel without fighting over the same profile lock.
      3. user_id     → persistent per-user profile (browser_profiles/user_<id>/)
                       Reuses login cookies across jobs — user logs in once.
      4. fallback    → legacy shared profile (browser_profile/)

    When a session profile is used, the caller is responsible for deleting it
    after the session ends (done in the `finally` block of _fill_and_submit_form_impl).
    """
    override = os.environ.get("AUTOJOBAPPLY_PROFILE_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return override

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if session_id:
        # Ephemeral per-session profile — seed it from the user profile if available
        # so existing login sessions carry over for this one run.
        session_path = os.path.join(project_root, "browser_profiles", f"session_{session_id}")
        if not os.path.exists(session_path):
            if user_id:
                user_path = os.path.join(project_root, "browser_profiles", f"user_{user_id}")
                if os.path.exists(user_path):
                    try:
                        shutil.copytree(user_path, session_path)
                        logger.info(f"Seeded session profile from user profile: {user_path} → {session_path}")
                    except Exception as e:
                        logger.warning(f"Could not seed session profile from user profile: {e}")
                        os.makedirs(session_path, exist_ok=True)
                else:
                    os.makedirs(session_path, exist_ok=True)
            else:
                os.makedirs(session_path, exist_ok=True)
        return session_path

    if user_id:
        path = os.path.join(project_root, "browser_profiles", f"user_{user_id}")
    else:
        path = os.path.join(project_root, "browser_profile")

    os.makedirs(path, exist_ok=True)
    return path


def launch_logged_in_context(p, headless: bool = HEADLESS, slow_mo: int = 0, user_id: int = None, session_id: int = None):
    """
    Launch a persistent browser context.
    - When session_id is given, uses an ephemeral session-scoped profile
      (seeded from the user profile if available) for full parallel isolation.
    - Otherwise falls back to the persistent per-user profile.
    Prefers installed Google Chrome; falls back to bundled Chromium.
    """
    user_data_dir = get_shared_profile_dir(user_id=user_id, session_id=session_id)
    profile_directory = os.environ.get("AUTOJOBAPPLY_PROFILE_DIRECTORY")  # e.g. "Profile 1"
    extra_args = [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
    ]
    if profile_directory and not session_id:  # don't override directory for ephemeral sessions
        extra_args.append(f'--profile-directory={profile_directory}')
    common = dict(
        user_data_dir=user_data_dir,
        headless=headless,
        slow_mo=slow_mo,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        args=extra_args,
    )
    try:
        return p.chromium.launch_persistent_context(channel="chrome", **common)
    except Exception:
        # Chrome not installed / not found — fall back to bundled Chromium.
        return p.chromium.launch_persistent_context(**common)


def build_field_map(form_data: dict, cover_letter: str) -> dict:
    """Map keyword patterns to form data values."""
    def clean_val(val, default=""):
        if val is None:
            return default
        val_str = str(val).strip()
        if val_str.lower() in ("none", "null", "undefined"):
            return default
        return val_str

    return {
        ('first name', 'firstname', 'given name'):     clean_val(form_data.get('first_name')),
        ('last name', 'lastname', 'surname', 'family'): clean_val(form_data.get('last_name')),
        ('full name', 'name'):                          clean_val(form_data.get('full_name')),
        ('email',):                                     clean_val(form_data.get('email')),
        ('phone', 'mobile', 'telephone', 'cell'):       clean_val(form_data.get('phone')),
        ('city', 'location', 'address'):                clean_val(form_data.get('location')),
        ('linkedin',):                                  clean_val(form_data.get('linkedin')),
        ('github',):                                    clean_val(form_data.get('github')),
        ('portfolio', 'website', 'personal site'):      clean_val(form_data.get('portfolio')),
        ('years of experience', 'experience years', 'years experience'): clean_val(form_data.get('experience_years'), "0"),
        ('current salary', 'current ctc', 'current compensation'): clean_val(form_data.get('current_salary')),
        ('expected salary', 'expected ctc', 'desired salary'): clean_val(form_data.get('expected_salary')),
        ('notice period', 'notice'):                    clean_val(form_data.get('notice_period'), "0"),
        ('cover letter', 'cover note', 'why do you want'):  cover_letter[:3000] if cover_letter else '',
        ('company', 'current company', 'employer', 'organization'): clean_val(form_data.get('current_company'), "__SKIP__"),
        ('job title', 'current title', 'current role', 'headline'): clean_val(form_data.get('headline'), "__SKIP__"),
    }


def match_field_value(label: str, name: str, placeholder: str, field_map: dict):
    """Return the best matching value from field_map for a given label/name/placeholder."""
    combined = f"{label} {name} {placeholder}".lower()
    best_match = None
    best_len = 0
    for keywords, value in field_map.items():
        for kw in keywords:
            if kw in combined and len(kw) > best_len:
                best_match = value
                best_len = len(kw)
    
    if best_match is not None:
        val_str = str(best_match).strip()
        if not val_str or val_str.lower() in ("none", "null", "undefined"):
            return None
            
    return best_match


def get_field_label(page, el) -> str:
    """Try to get a human-readable label for a form element."""
    try:
        el_id = el.get_attribute('id')
        if el_id:
            label = page.query_selector(f'label[for="{el_id}"]')
            if label:
                return label.inner_text().strip()
        
        # aria-label
        aria = el.get_attribute('aria-label')
        if aria:
            return aria

        # Implicit label wrapping (<label>...<input>... text</label>), common for
        # checkboxes/radios that have no "for"/"id" pairing at all.
        try:
            wrapping = el.evaluate("e => e.closest('label')?.innerText?.trim() || ''")
            if wrapping:
                return wrapping
        except Exception:
            pass

        placeholder = el.get_attribute('placeholder')
        if placeholder:
            return placeholder

        name = el.get_attribute('name') or ''
        return name.replace('_', ' ').replace('-', ' ')
    except Exception:
        return ''


def _get_radio_group_label(radio) -> str:
    """Best-effort label for an entire radio group (fieldset legend / group container text)."""
    try:
        return radio.evaluate(
            'el => el.closest("fieldset, .form-group, [role=group]")?.innerText || ""'
        ).strip()
    except Exception:
        return ''


def _is_login_wall(page) -> bool:
    """Detects a login/sign-in wall: password field, OTP field, or a login/signin URL."""
    try:
        if page.query_selector('input[type="password"]'):
            return True
        if page.query_selector('input[name*="otp" i], input[placeholder*="verification code" i], input[placeholder*="otp" i]'):
            return True
    except Exception:
        pass
    url = (page.url or '').lower()
    return "login" in url or "signin" in url


def _detect_captcha(page) -> bool:
    """
    Detects CAPTCHA/anti-bot pages on job boards.
    Returns True if a CAPTCHA challenge is detected.
    """
    try:
        page_content = page.inner_text().lower()
        
        # Check for common CAPTCHA indicators
        captcha_indicators = [
            'verify you are human',
            'verify you are not a robot',
            'captcha',
            'recaptcha',
            'hcaptcha',
            'are you a human',
            'security check',
            'please complete the security check'
        ]
        
        if any(indicator in page_content for indicator in captcha_indicators):
            return True
        
        # Check for CAPTCHA iframe
        captcha_frames = page.query_selector_all('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="captcha"]')
        if captcha_frames:
            return True
            
        # Check for Cloudflare challenge
        if 'cloudflare' in page_content and 'challenge' in page_content:
            return True
            
    except Exception:
        pass
    
    return False


# URL patterns for known job-board LISTING pages (not the application form
# itself). These always need an Apply/Easy Apply click — checked before, and
# instead of, the generic field-count heuristic below, because real listing
# pages like LinkedIn are SPAs full of incidental inputs (nav search box,
# messaging widget, etc.) that make a raw "count the inputs" check unreliable.
KNOWN_LISTING_URL_PATTERNS = [
    'linkedin.com/jobs/view',
    'indeed.com/viewjob',
    'indeed.com/rc/clk',
    'indeed.com/pagead',
    'naukri.com/job-listings',
]


def _looks_like_form_page(page) -> bool:
    """
    Heuristic: does the current page already show a fillable application form,
    or is it still a job-listing/description page that needs an Apply/Easy
    Apply click first? Known listing-page URLs (LinkedIn, Indeed) are always
    treated as "not a form yet" regardless of incidental inputs elsewhere on
    the page. For everything else, fall back to counting inputs/textareas —
    a real application form has several; a bare listing page has none.
    """
    url = (page.url or '').lower()
    if any(p in url for p in KNOWN_LISTING_URL_PATTERNS):
        return False

    try:
        count = page.evaluate(
            '() => document.querySelectorAll('
            '\'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="search"]), textarea\''
            ').length'
        )
        return count >= 2
    except Exception:
        return True  # fail open — don't get stuck trying to click Apply forever


def _find_apply_button(page):
    """
    Looks for an Apply/Easy Apply button, tolerating late-hydrating SPA pages
    (LinkedIn/Indeed/Naukri render the button asynchronously after initial load).
    Selectors are tried instantly first (no wait); only if none are present
    yet do we wait once (combined, not per-selector — waiting per selector
    would multiply into tens of seconds of dead time).
    """
    apply_selectors = [
        'button:has-text("Apply on company site")',
        'a:has-text("Apply on company site")',
        'button:has-text("Apply On Company Site")',
        'a:has-text("Apply On Company Site")',
        'button:has-text("Company Site")',
        'a:has-text("Company Site")',
        'button.apply-message',
        'button#apply-button',
        'button[aria-label*="Easy Apply" i]',
        'button:has-text("Easy Apply")',
        'a:has-text("Easy Apply")',
        '.jobs-apply-button',
        'button[aria-label*="Apply now" i]',
        'button:has-text("Apply now")',
        'a:has-text("Apply now")',
        '[data-testid="apply-button"]',
        'button:has-text("Apply")',
        'a:has-text("Apply")',
    ]

    for sel in apply_selectors:
        try:
            elements = page.query_selector_all(sel)
            for candidate in elements:
                if candidate and candidate.is_visible():
                    return candidate
        except Exception:
            continue

    # Nothing visible yet — the button may still be hydrating. Wait once for
    # any of them together, then re-sweep to see which one actually landed.
    try:
        page.wait_for_selector(", ".join(apply_selectors), timeout=6000, state="visible")
    except Exception:
        return None

    for sel in apply_selectors:
        try:
            elements = page.query_selector_all(sel)
            for candidate in elements:
                if candidate and candidate.is_visible():
                    return candidate
        except Exception:
            continue
    return None


def _is_multi_step_wizard(page) -> bool:
    """
    Detect if the current page is a multi-step modal wizard (LinkedIn Easy Apply,
    Indeed Apply modal, Naukri Apply modal). Returns True if we detect navigation buttons like
    "Next", "Continue", "Review" that indicate a multi-step flow.
    """
    try:
        # Check for multi-step navigation buttons
        nav_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button:has-text("Continue to next step")',
            'button:has-text("Review")',
            'button:has-text("Submit application")',
            '[data-testid="next-button"]',
            '[data-testid="continue-button"]',
        ]
        
        for sel in nav_selectors:
            if page.query_selector(sel):
                return True
    except Exception:
        pass
    return False


def _find_next_button(page):
    """Find the Next/Continue button in a multi-step wizard."""
    next_selectors = [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'button:has-text("Continue to next step")',
        '[data-testid="next-button"]',
        '[data-testid="continue-button"]',
    ]
    
    for sel in next_selectors:
        try:
            elements = page.query_selector_all(sel)
            for btn in elements:
                if btn and btn.is_visible():
                    return btn
        except Exception:
            continue
    return None


def _is_submit_or_review_page(page) -> bool:
    """Check if we're on the final submit/review step."""
    submit_selectors = [
        'button:has-text("Submit application")',
        'button:has-text("Submit")',
        'button:has-text("Review")',
        '[data-testid="submit-button"]',
    ]
    
    for sel in submit_selectors:
        try:
            if page.query_selector(sel):
                return True
        except Exception:
            continue
    return False


def _fill_multi_step_wizard(page, form_data: dict, custom_qa: list, cover_letter: str, resume_path: str, add_log, user_id: int = None, job_id: int = None, resume_text: str = "") -> bool:
    """
    Handle multi-step modal wizards (LinkedIn Easy Apply, Indeed Apply modal, Naukri).
    Loops through steps until we reach the submit/review page.
    
    Returns:
        bool: True if completed successfully, False if failed
    """
    max_steps = 6
    current_step = 0
    
    while current_step < max_steps:
        current_step += 1
        add_log(f"Multi-step wizard: Processing step {current_step}/{max_steps}")
        
        # Check if we've reached the final submit/review page
        if _is_submit_or_review_page(page):
            add_log("Reached final submit/review page - wizard complete")
            return True
        
        # Detect and fill fields on current step
        _log_field_inventory(page, add_log)
        
        # Fill text fields
        field_map = build_field_map(form_data, cover_letter)
        inputs = page.query_selector_all('input:not([type="hidden"]):not([type="submit"]):not([type="file"]):not([type="search"]), textarea')
        for inp in inputs:
            try:
                if not inp.is_visible():
                    continue
                label_text = get_field_label(page, inp).lower()
                if any(x in label_text for x in ('recaptcha', 'captcha', 'csrf')):
                    continue
                field_type = (inp.get_attribute('type') or 'text').lower()
                
                if field_type in ('checkbox', 'radio', 'button', 'reset'):
                    continue
                
                matched_value = match_field_value(label_text, inp.get_attribute('name') or '', inp.get_attribute('placeholder') or '', field_map)
                
                if matched_value == "__SKIP__":
                    add_log(f"  Step {current_step}: Explicitly skipping '{label_text}'")
                    continue
                elif matched_value is not None and matched_value != "":
                    inp.scroll_into_view_if_needed()
                    inp.click(click_count=3)
                    inp.type(str(matched_value), delay=40)
                    add_log(f"  Step {current_step}: Filled '{label_text}'")
                elif label_text.strip():
                    answer = _resolve_via_review_queue(page, add_log, user_id, job_id, label_text, form_data, resume_text)
                    if answer:
                        inp.scroll_into_view_if_needed()
                        inp.click(click_count=3)
                        inp.type(str(answer), delay=40)
                        add_log(f"  Step {current_step}: Filled '{label_text}' with review answer")
            except Exception as e:
                add_log(f"  Step {current_step}: Skipped input: {str(e)}", "warn")
        
        # Handle dropdowns
        selects = page.query_selector_all('select')
        for sel in selects:
            try:
                if not sel.is_visible():
                    continue
                label_text = get_field_label(page, sel).lower()
                name_attr = (sel.get_attribute('name') or '').lower()
                
                if any(k in label_text or k in name_attr for k in ['country', 'citizenship', 'location']):
                    try_select_option(page, sel, ['United States', 'US', 'India', 'Other'], add_log)
                elif any(k in label_text or k in name_attr for k in ['experience', 'year']):
                    try_select_option(page, sel, [str(form_data.get('experience_years', '1')), '1-3 years', '1+ year'], add_log)
                elif any(k in label_text or k in name_attr for k in ['gender']):
                    try_select_option(page, sel, ['Prefer not to say', 'Not specified', 'Other'], add_log)
                elif any(k in label_text or k in name_attr for k in ['ethnicity', 'race']):
                    try_select_option(page, sel, ['Decline to self identify', 'Prefer not to say'], add_log)
                elif any(k in label_text or k in name_attr for k in ['disability']):
                    try_select_option(page, sel, ['No', 'I do not have a disability', 'Not disabled'], add_log)
                elif any(k in label_text or k in name_attr for k in ['veteran']):
                    try_select_option(page, sel, ['No', 'I am not a protected veteran', 'Not a veteran'], add_log)
                elif label_text.strip():
                    options = sel.query_selector_all('option')
                    opt_texts = [o.inner_text().strip() for o in options if o.get_attribute('value')]
                    if opt_texts:
                        prompt = f"{label_text} (Options: {', '.join(opt_texts)})"
                        add_log(f"  Step {current_step}: Unmapped select: '{label_text}' -> asking AI")
                        answer = _resolve_via_review_queue(page, add_log, user_id, job_id, prompt, form_data, resume_text)
                        if answer:
                            try_select_option(page, sel, [answer], add_log)
                        else:
                            add_log(f"  Step {current_step}: Leaving '{label_text}' unset.", "warn")
            except Exception as e:
                add_log(f"  Step {current_step}: Skipped select: {str(e)}", "warn")
        
        # Handle checkboxes
        consent_keywords = ['agree', 'consent', 'terms', 'privacy policy', 'acknowledge', 'confirm that']
        checkboxes = page.query_selector_all('input[type="checkbox"]')
        for cb in checkboxes:
            try:
                if not cb.is_visible():
                    continue
                label_text = get_field_label(page, cb).lower().strip()
                if any(kw in label_text for kw in ('email updates', 'job alert', 'subscribe', 'newsletter', 'receive updates', 'send me')):
                    add_log(f"  Step {current_step}: Skipping marketing/alert checkbox: '{label_text}'")
                    continue
                if cb.is_checked():
                    continue
                if any(kw in label_text for kw in consent_keywords):
                    cb.check(force=True)
                    add_log(f"  Step {current_step}: Checked consent box")
                elif label_text:
                    add_log(f"  Step {current_step}: Unmapped checkbox: '{label_text}' -> asking AI")
                    answer = _resolve_via_review_queue(page, add_log, user_id, job_id, f"Check this box? {label_text}", form_data, resume_text)
                    if answer and answer.strip().lower() in ('yes', 'y', 'true', 'check', 'checked'):
                        cb.check(force=True)
                        add_log(f"  Step {current_step}: Checked '{label_text}' per AI answer")
            except Exception as e:
                add_log(f"  Step {current_step}: Skipped checkbox: {str(e)}", "warn")

        # Handle Radio Button Groups
        add_log(f"  Step {current_step}: Scanning for radio groups...")
        try:
            all_radios = page.query_selector_all('input[type="radio"]')
            groups = {}
            for radio in all_radios:
                if not radio.is_visible():
                    continue
                name_attr = radio.get_attribute('name') or ''
                if not name_attr:
                    continue
                groups.setdefault(name_attr, []).append(radio)

            for name_attr, radios in groups.items():
                try:
                    if any(r.is_checked() for r in radios):
                        continue
                    group_label = _get_radio_group_label(radios[0]) or name_attr
                    option_labels = [get_field_label(page, r).strip() for r in radios]
                    question_text = f"{group_label} (options: {', '.join(o for o in option_labels if o)})"
                    add_log(f"  Step {current_step}: Unanswered radio group: '{group_label}' -> asking AI")
                    answer = _resolve_via_review_queue(page, add_log, user_id, job_id, question_text, form_data, resume_text)
                    if answer:
                        chosen = None
                        for r, opt_label in zip(radios, option_labels):
                            if opt_label and (opt_label.lower() in answer.lower() or answer.lower() in opt_label.lower()):
                                chosen = r
                                break
                        if chosen:
                            chosen.check(force=True)
                            add_log(f"  Step {current_step}: Selected '{group_label}' option per AI answer")
                        else:
                            add_log(f"  Step {current_step}: Could not match AI answer '{answer}' to options; leaving unset", "warn")
                    else:
                        add_log(f"  Step {current_step}: Leaving radio group '{group_label}' unset", "warn")
                except Exception as e:
                    add_log(f"  Step {current_step}: Radio group skip: {str(e)}", "warn")
        except Exception as e:
            add_log(f"  Step {current_step}: Radio group scan skipped: {str(e)}", "warn")
        
        # Find and click Next/Continue button
        next_btn = None
        for retry in range(3):
            next_btn = _find_next_button(page)
            if next_btn:
                break
            page.wait_for_timeout(1000)
            
        if not next_btn:
            # If we still don't find it, check if we see any submit/review indicators.
            # Otherwise, if we are still on the form step, it might have been a temporary lag.
            if _is_submit_or_review_page(page):
                add_log(f"Step {current_step}: No Next button found, but submit/review page detected - wizard complete")
                return True
            else:
                add_log(f"Step {current_step}: Next button not found and not on submit page. Auto-close prevention: waiting 3s...", "warn")
                page.wait_for_timeout(3000)
                next_btn = _find_next_button(page)
                if not next_btn:
                    add_log(f"Step {current_step}: Still no Next button. Wizard may be complete or blocked. Proceeding.", "warn")
                    return True
        
        try:
            add_log(f"Step {current_step}: Clicking Next/Continue button")
            next_btn.scroll_into_view_if_needed()
            next_btn.click()
            page.wait_for_timeout(2000)
        except Exception as e:
            add_log(f"Step {current_step}: Failed to click Next button: {str(e)}", "warn")
            return False
    
    add_log(f"Multi-step wizard: Reached max steps ({max_steps}) - proceeding to submit", "warn")
    return True


def _click_apply_and_switch(ctx, page, add_log, is_multi_step: bool = False):
    """
    Clicks an Apply/Easy Apply button to get from a job listing page to the
    real application form. The form may render in place (LinkedIn Easy Apply,
    Indeed Apply modal, Naukri) or open in a new tab (external ATS, e.g. "Responses
    managed off LinkedIn"). Returns the page to keep using — possibly a new one.
    A no-op (returns page unchanged) if the current page already looks like a
    form, so direct ATS links (Greenhouse/Lever) are unaffected.
    
    If is_multi_step is True, this is for LinkedIn/Indeed/Naukri modal wizards.
    """
    if _looks_like_form_page(page):
        return page

    add_log("This looks like a job listing page, not the application form yet — looking for an Apply button...")
    btn = _find_apply_button(page)

    if not btn:
        add_log("  No Apply button found — proceeding to fill this page as-is.", "warn")
        return page

    try:
        btn_text = (btn.inner_text() or "Apply").strip()
    except Exception:
        btn_text = "Apply"

    pages_before = len(ctx.pages)
    try:
        btn.scroll_into_view_if_needed()
        btn.click()
    except Exception as e:
        add_log(f"  Could not click '{btn_text}': {str(e)}", "warn")
        return page

    page.wait_for_timeout(3000)
    
    target_page = page
    if len(ctx.pages) > pages_before:
        target_page = ctx.pages[-1]
        add_log(f"  Clicked '{btn_text}' — a new tab opened for the application, switching to it.")
        try:
            target_page.wait_for_load_state("domcontentloaded", timeout=30000)
            target_page.wait_for_timeout(2000)
        except Exception:
            pass

    # Check if Naukri 1-click apply succeeded instantly
    if "naukri.com" in target_page.url.lower():
        if "myapply/saveapply" in target_page.url.lower():
            add_log("Naukri 1-click apply was successful (via success URL)!")
            raise OneClickApplySuccess()
            
        try:
            success_toast = target_page.query_selector('text="Applied successfully" i, text="Successfully applied" i, text="successfully applied to" i, .apply-message:has-text("Applied")')
            applied_btn = target_page.query_selector('button:has-text("Applied"), a:has-text("Applied"), div[class*="apply"]:has-text("Applied"), span[class*="apply"]:has-text("Applied"), div[id*="apply"]:has-text("Applied")')
            
            if success_toast or applied_btn:
                add_log("Naukri 1-click apply was successful!")
                raise OneClickApplySuccess()
        except OneClickApplySuccess:
            raise
        except Exception as e:
            add_log(f"Naukri 1-click apply check error: {str(e)}", "warn")

    if target_page != page:
        return target_page

    add_log(f"  Clicked '{btn_text}' — application form should now be visible on this page.")
    target_page.wait_for_timeout(1000)
    return target_page


def get_form_context(page):
    """
    Returns the frame (either page or a child iframe) that contains the application form.
    Heuristic: The frame with the most visible input/textarea elements.
    """
    # Wait up to 5 seconds for the form to render in some frame if initially empty
    for attempt in range(5):
        best_frame = page
        max_inputs = 0
        
        try:
            main_inputs = len([el for el in page.query_selector_all('input:not([type="hidden"]), textarea') if el.is_visible()])
            if main_inputs > 0:
                max_inputs = main_inputs
        except Exception:
            pass
            
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                inputs = frame.query_selector_all('input:not([type="hidden"]), textarea')
                visible_count = len([el for el in inputs if el.is_visible()])
                if visible_count > max_inputs:
                    max_inputs = visible_count
                    best_frame = frame
            except Exception:
                continue
        
        if max_inputs > 0:
            if best_frame != page:
                logger.info(f"Detected form inside iframe (name={best_frame.name}, url={best_frame.url}) with {max_inputs} fields.")
            return best_frame
            
        page.wait_for_timeout(1000)
        
    return page


def _log_field_inventory(page, add_log):
    """Logs every visible input/select/textarea detected on the page so you can verify
    what the automation found vs. what's actually on the page."""
    try:
        fields = page.evaluate("""
            () => {
                const elements = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="search"]), select, textarea');
                const results = [];
                elements.forEach(el => {
                    let label = '';
                    if (el.id) {
                        const lab = document.querySelector(`label[for="${el.id}"]`);
                        if (lab) label = lab.innerText.trim();
                    }
                    if (!label) {
                        const wrapping = el.closest('label');
                        if (wrapping) label = wrapping.innerText.trim();
                    }
                    if (!label && el.getAttribute('aria-label')) label = el.getAttribute('aria-label');
                    if (!label && el.placeholder) label = el.placeholder;
                    if (!label && el.name) label = el.name.replace(/[_-]/g, ' ');
                    results.push({ label: label, type: el.type || el.tagName.toLowerCase(), name: el.name || el.id || '' });
                });
                return results;
            }
        """)
        add_log(f"Detected {len(fields)} fields on page:")
        for f in fields:
            display = f.get('label') or f.get('name') or '(unlabeled)'
            add_log(f"  - [{f.get('type')}] {display}")
    except Exception as e:
        add_log(f"  Field inventory scan failed: {str(e)}", "warn")


def sanitize_numeric_answer(question: str, answer: str) -> str:
    """If the question expects a number/years, and the answer has extra text, extract the number."""
    if not answer:
        return answer
    q_lower = question.lower()
    if any(k in q_lower for k in ("how many years", "number of years", "years of experience", "notice period in days", "notice period (in days)", "notice period days", "gpa")):
        # Check if the answer contains digits
        match = re.search(r'\d+', answer)
        if match:
            return match.group(0)
    return answer


def generate_ai_answer(question_text: str, form_data: dict, resume_text: str = "") -> tuple:
    """
    Generate a best-guess answer for an application-form question using Groq
    (primary — fast + already configured via GROQ_API_KEY) with Anthropic as
    an optional fallback if ANTHROPIC_API_KEY is also set.

    Returns:
        tuple: (answer: str, confidence: float)
        - answer: The generated answer or None if failed
        - confidence: 0.0-1.0 confidence score
    """
    if not GROQ_API_KEY and not ANTHROPIC_API_KEY:
        logger.warning("No GROQ_API_KEY or ANTHROPIC_API_KEY set - skipping AI answer generation")
        return None, 0.0

    context_parts = []
    if form_data.get('first_name'):
        context_parts.append(f"Name: {form_data.get('first_name')} {form_data.get('last_name', '')}")
    if form_data.get('email'):
        context_parts.append(f"Email: {form_data.get('email')}")
    if form_data.get('phone'):
        context_parts.append(f"Phone: {form_data.get('phone')}")
    if form_data.get('location'):
        context_parts.append(f"Location: {form_data.get('location')}")
    if form_data.get('experience_years') is not None:
        context_parts.append(f"Experience: {form_data.get('experience_years')} years")
    if form_data.get('expected_salary'):
        context_parts.append(f"Expected Salary: {form_data.get('expected_salary')}")
    if form_data.get('current_salary'):
        context_parts.append(f"Current Salary: {form_data.get('current_salary')}")
    if form_data.get('notice_period') is not None:
        context_parts.append(f"Notice Period: {form_data.get('notice_period')} days")
    if form_data.get('willing_to_relocate'):
        context_parts.append(f"Willing to Relocate: {form_data.get('willing_to_relocate')}")
    if form_data.get('linkedin'):
        context_parts.append(f"LinkedIn: {form_data.get('linkedin')}")
    if form_data.get('github'):
        context_parts.append(f"GitHub: {form_data.get('github')}")
    skills = form_data.get('skills')
    if skills:
        skills_str = ", ".join(skills) if isinstance(skills, (list, tuple)) else str(skills)
        context_parts.append(f"Skills: {skills_str}")
    if resume_text:
        context_parts.append(f"\nFULL RESUME:\n{resume_text[:3000]}")

    context = "\n".join(context_parts) if context_parts else "No profile data available"

    prompt = f"""You are an expert AI Job Application Assistant.
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
15. If the question is about demographics (Gender, Race, Disability, Veteran status, Sexual Orientation, Religion) and the resume doesn't specify, ALWAYS return the "Prefer not to say" or "Decline to identify" option if provided in the options list.
16. If the answer cannot be determined from the resume (excluding expected/current salary, notice period, and demographics):
    - First check whether it can be reasonably inferred (e.g. assume authorized to work = "Yes", assume visa sponsorship not required = "No", 18 or older = "Yes").
    - If not, return exactly: "Not specified in resume"
17. Never mention that you are an AI.
18. Never mention the resume in your response.
19. Keep answers natural so they appear to be written by the candidate.
20. If the question asks for a count, duration, or numeric value in specific units (for example: "How many years of experience...", "What is your notice period in days?", "Expected salary in LPA", etc.), return ONLY the number/digits. Do not append words like "years", "months", "days", "LPA", etc.

CANDIDATE PROFILE:
{context}

QUESTION: {question_text}

Output Rules:
- Return ONLY the answer.
- No explanations.
- No extra comments.
- No labels.
- No Markdown.
- No quotation marks unless required."""

    # Try Groq first (OpenAI-compatible /chat/completions)
    if GROQ_API_KEY:
        models_to_try = [GROQ_MODEL]
        if GROQ_MODEL != "llama-3.1-8b-instant":
            models_to_try.append("llama-3.1-8b-instant")
            
        for model in models_to_try:
            success = False
            for attempt in range(2):
                try:
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {GROQ_API_KEY}",
                            "content-type": "application/json",
                        },
                        json={
                            "model": model,
                            "max_tokens": 200,
                            "temperature": 0.4,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                        timeout=15,
                    )
                    if response.status_code == 429 and attempt == 0:
                        logger.warning(f"Groq {model} returned 429 (Rate Limit) - sleeping 2s and retrying...")
                        time.sleep(2)
                        continue
                    response.raise_for_status()
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"].strip()
                    logger.info(f"Groq {model} raw answer: {repr(answer)}")
                    answer = sanitize_numeric_answer(question_text, answer)
                    return _score_ai_answer(answer)
                except Exception as e:
                    logger.error(f"Groq model {model} attempt failed: {str(e)}")
                    break  # Break retry loop to try the fallback model
            if success:
                break
            # fall through to Anthropic if configured

    # Fallback: Anthropic Claude
    if ANTHROPIC_API_KEY:
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            }
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            result = response.json()
            answer = result.get("content", [{}])[0].get("text", "").strip()
            answer = sanitize_numeric_answer(question_text, answer)
            return _score_ai_answer(answer)
        except Exception as e:
            logger.error(f"Anthropic answer generation failed: {str(e)}")

    return None, 0.0


def _score_ai_answer(answer: str) -> tuple:
    """Simple confidence scoring based on answer quality/shape."""
    if not answer or any(k in answer.lower() for k in ["not specified", "unknown", "n/a", "no details", "no information"]):
        return None, 0.0
    elif len(answer) < 10:
        return answer, 0.5
    else:
        return answer, 0.85


def pause_for_user_input(page, prompt_text="Please answer the question on screen"):
    try:
        page.evaluate(f"""() => {{
            const btn = document.createElement('button');
            btn.id = 'autojobapply-resume-btn';
            btn.innerHTML = 'Resume Automation ➔';
            btn.style.position = 'fixed';
            btn.style.bottom = '20px';
            btn.style.right = '20px';
            btn.style.zIndex = '999999';
            btn.style.padding = '15px 25px';
            btn.style.fontSize = '18px';
            btn.style.fontWeight = 'bold';
            btn.style.backgroundColor = '#0066cc';
            btn.style.color = 'white';
            btn.style.border = 'none';
            btn.style.borderRadius = '8px';
            btn.style.cursor = 'pointer';
            btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            
            const label = document.createElement('div');
            label.id = 'autojobapply-prompt-label';
            label.innerText = `{prompt_text}`;
            label.style.position = 'fixed';
            label.style.bottom = '80px';
            label.style.right = '20px';
            label.style.zIndex = '999999';
            label.style.backgroundColor = '#fff3cd';
            label.style.color = '#856404';
            label.style.padding = '10px 15px';
            label.style.border = '2px solid #ffeeba';
            label.style.borderRadius = '8px';
            label.style.fontWeight = 'bold';
            label.style.maxWidth = '300px';
            
            btn.onclick = () => {{
                btn.remove();
                label.remove();
            }};
            document.body.appendChild(label);
            document.body.appendChild(btn);
        }}""")
        page.wait_for_function("!document.getElementById('autojobapply-resume-btn')", timeout=0)
    except Exception as e:
        pass

def _resolve_via_review_queue(page, add_log, user_id, job_id, question_text: str, form_data: dict = None, resume_text: str = ""):
    """
    AI-FIRST AUTO-ANSWER MODE — Human review queue completely bypassed.

    Uses Groq AI to generate answers automatically from the applicant's resume
    and profile. No human waiting, no review queue polling.
    - Confidence >= 0.3 → use AI answer directly
    - AI fails or returns 'Not specified' → leave field blank and continue
    """
    if form_data:
        ai_answer, confidence = generate_ai_answer(question_text, form_data, resume_text)
        if ai_answer and confidence >= 0.3:
            add_log(f"  🤖 AI answered (confidence {confidence:.0%}): '{ai_answer[:80]}'")
            return ai_answer
        elif ai_answer:
            # Even low confidence — still use it, better than blank or waiting
            add_log(f"  🤖 AI answered (low confidence {confidence:.0%}): '{ai_answer[:80]}'")
            return ai_answer
        else:
            add_log(f"  🤖 AI could not answer '{question_text[:60]}'. Pausing for your manual input...", "warn")
            pause_for_user_input(page, f"AI couldn't answer:\n\n{question_text[:100]}\n\nPlease answer manually and click Resume.")
            return None
    else:
        add_log(f"  No profile data to answer '{question_text[:60]}'. Pausing for your manual input...", "warn")
        pause_for_user_input(page, f"No profile data to answer:\n\n{question_text[:100]}\n\nPlease answer manually and click Resume.")
        return None


def try_select_option(page, select_el, preferred_values: list, log_fn):
    """Try selecting one of the preferred option values in a <select>."""
    try:
        options = select_el.query_selector_all('option')
        for pref in preferred_values:
            for opt in options:
                opt_text = opt.inner_text().strip()
                opt_val  = opt.get_attribute('value') or ''
                if pref.lower() in opt_text.lower() or pref.lower() in opt_val.lower():
                    select_el.select_option(value=opt_val)
                    log_fn(f"  Select → '{opt_text}'")
                    return
    except Exception as e:
        log_fn(f"  Select option skip: {str(e)}", "warn")


def find_submit_button(page):
    """Find the main submit button selector on the page."""
    selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit your application")',
        'button:has-text("Submit application")',
        'button:has-text("Submit Application")',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send Application")',
        '[data-testid="submit-button"]',
        'button[class*="submit"]',
        'button[class*="Submit"]',
        '#submit-app-btn',
    ]
    for sel in selectors:
        try:
            elements = page.query_selector_all(sel)
            for btn in elements:
                if btn and btn.is_visible():
                    return sel
        except Exception:
            continue
    return None


def _question_keywords(question: str) -> list:
    """Extract unique meaningful words from a question string."""
    stopwords = {'a', 'an', 'the', 'is', 'are', 'do', 'you', 'to', 'in', 'or', 'and', 'for', 'will'}
    words = [w for w in re.findall(r'\w+', question.lower()) if w not in stopwords and len(w) > 2]
    return words[:4]