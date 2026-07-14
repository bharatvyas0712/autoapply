"""
Job Searcher Engine.

- LinkedIn / Indeed  → Playwright scraping (best-effort, can be blocked)
- Greenhouse / Lever → official public JSON APIs (reliable, no anti-bot)
"""
import re
import random
import urllib.parse
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

GREENHOUSE_COMPANIES = [
    'postman', 'groww', 'phonepe', 'druva',
    'stripe', 'databricks', 'coinbase', 'dropbox', 'gitlab', 'figma', 'discord',
    'reddit', 'doordash', 'instacart', 'robinhood', 'plaid', 'brex', 'ramp',
    'retool', 'benchling', 'samsara', 'airbnb', 'asana', 'cloudflare',
    'airtable', 'webflow', 'elastic', 'datadog', 'mongodb', 'okta', 'pagerduty',
    'squarespace', 'affirm', 'scaleai', 'anthropic', 'twilio',
]
LEVER_COMPANIES = [
    'cred', 'meesho',
    'lever', 'leadiq', 'mistral', 'huggingface', 'voleon', 'sardine', 'palantir',
]

INDIA_TERMS = [
    'india', 'bengaluru', 'bangalore', 'mumbai', 'delhi', 'new delhi', 'hyderabad',
    'pune', 'chennai', 'gurgaon', 'gurugram', 'noida', 'kolkata', 'ahmedabad',
    'jaipur', 'indore', 'kochi', 'chandigarh', 'remote - india', 'remote india',
]

NON_INDIA_HINTS = [
    'united states', 'usa', 'u.s', 'canada', 'united kingdom', ' uk', 'europe',
    'emea', 'germany', 'france', 'ireland', 'singapore', 'australia', 'japan',
    'brazil', 'mexico', 'netherlands', 'spain', 'poland', 'philippines',
    'indonesia', 'uae', 'dubai', 'latam', 'apac',
]


def _india_query(location: str) -> bool:
    return any(t in (location or '').lower() for t in INDIA_TERMS)


def _location_matches(job_loc: str, query_loc: str) -> bool:
    j = (job_loc or '').lower()
    q = (query_loc or '').lower()
    if not q:
        return True
    if _india_query(q):
        if any(t in j for t in INDIA_TERMS):
            return True
        if 'remote' in j and not any(h in j for h in NON_INDIA_HINTS):
            return True
        return False
    if 'remote' in q:
        return 'remote' in j
    return q in j or 'remote' in j

_BLOCK_TITLE_HINTS = ('just a moment', 'verify you are human', 'attention required', 'access denied', 'are you a robot')


def _fetch_full_description(page, url: str, selectors: list, timeout: int = 15000):
    """
    Visit a job's own detail page and pull the full description text.

    Search-results cards only expose a title (LinkedIn) or a 1-2 line
    snippet (Indeed) — nowhere near enough text for scoreJob() in
    matcher.js to judge real skill overlap, which was causing good matches
    to score near 0 and get hidden below the match threshold.

    Returns:
        str  - real description text (possibly "" if the page loaded but no
               selector matched)
        None - hit an anti-bot / verification wall (e.g. Indeed's "Just a
               moment..." Cloudflare check). Signals the caller to stop
               fetching further detail pages this run instead of continuing
               to hammer a source that's already blocking us.
    """
    try:
        page.wait_for_timeout(random.randint(400, 1100))
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
        title = (page.title() or "").lower()
        if any(hint in title for hint in _BLOCK_TITLE_HINTS):
            print(f"Detail-page fetch blocked (anti-bot wall) at {url}")
            return None
        for sel in selectors:
            el = page.query_selector(sel)
            if el:
                text = el.inner_text().strip()
                if text:
                    return text[:1500]
    except Exception as e:
        print(f"Description fetch failed for {url}: {e}")
    return ""


def search_linkedin_jobs(query: str, location: str, limit: int = 10, experience_level: str = "", job_type: str = "") -> list:
    results = []
    base_url = "https://www.linkedin.com/jobs/search/"
    params = {
        "keywords": query,
        "location": location,
        "f_TPR": "r2592000"
    }

    search_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        page = ctx.new_page()

        try:
            page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            try:
                page.wait_for_selector('ul.jobs-search__results-list', timeout=10000)
            except PlaywrightTimeoutError:
                pass

            job_cards = page.query_selector_all('ul.jobs-search__results-list > li')

            for card in job_cards[:limit]:
                try:
                    title_el = card.query_selector('h3.base-search-card__title')
                    company_el = card.query_selector('h4.base-search-card__subtitle')
                    location_el = card.query_selector('span.job-search-card__location')
                    link_el = card.query_selector('a.base-card__full-link')

                    title = title_el.inner_text().strip() if title_el else "Unknown Title"
                    company = company_el.inner_text().strip() if company_el else "Unknown Company"
                    loc = location_el.inner_text().strip() if location_el else location

                    # Apply local experience and job type filters
                    if not _job_matches_filters(title, "", experience_level, job_type):
                        continue

                    url = link_el.get_attribute('href') if link_el else search_url
                    if url and '?' in url:
                        url = url.split('?')[0]

                    results.append({
                        "title": title,
                        "company": company,
                        "location": loc,
                        "job_url": url,
                        "source": "linkedin_public",
                        "job_type": "full-time"
                    })
                except Exception as e:
                    print(f"Error extracting job card: {e}")
                    continue

            # Fetch each job's real description from its own page so scoring
            # has something to work with beyond the bare title. Stop as soon
            # as we hit an anti-bot wall instead of continuing to hammer it.
            for job in results:
                desc = _fetch_full_description(
                    page, job["job_url"],
                    ['.show-more-less-html__markup', '.description__text', 'div.jobs-description__content']
                )
                if desc is None:
                    break
                job["description"] = desc

        except Exception as e:
            print(f"Error during job search: {e}")
        finally:
            browser.close()

    return results

def search_indeed_jobs(query: str, location: str, limit: int = 15, easy_apply_only: bool = False,
                        exclude_urls: set = None, max_pages: int = 4, experience_level: str = "", job_type: str = ""):
    """
    Search public Indeed job listings without logging in.
    ...
    """
    exclude_urls = exclude_urls or set()
    results = []
    seen_this_run = set()
    excluded_count = 0

    domain = "https://in.indeed.com" if _india_query(location) else "https://www.indeed.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        try:
            for page_num in range(max_pages):
                if len(results) >= limit:
                    break

                params = {"q": query, "l": location, "sort": "date"}
                
                if page_num > 0:
                    params["start"] = page_num * 10
                search_url = f"{domain}/jobs?{urllib.parse.urlencode(params)}"

                page.goto(search_url, timeout=35000, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)

                card_selectors = [
                    'div.job_seen_beacon',
                    '#mosaic-provider-jobcards div.cardOutline',
                    'a.tapItem',
                ]
                cards = []
                for sel in card_selectors:
                    cards = page.query_selector_all(sel)
                    if cards:
                        break

                if not cards:
                    break

                for card in cards:
                    if len(results) >= limit:
                        break
                    try:
                        title_el = (card.query_selector('h2.jobTitle span[title]')
                                    or card.query_selector('h2.jobTitle')
                                    or card.query_selector('[id^="jobTitle"]'))
                        company_el = (card.query_selector('[data-testid="company-name"]')
                                      or card.query_selector('span.companyName'))
                        location_el = (card.query_selector('[data-testid="text-location"]')
                                       or card.query_selector('div.companyLocation'))
                        link_el = card.query_selector('a[data-jk]') or card.query_selector('h2.jobTitle a')
                        snippet_el = (card.query_selector('[data-testid="jobsnippet_footer"]')
                                      or card.query_selector('div.job-snippet')
                                      or card.query_selector('div.underShelfFooter'))

                        title = title_el.inner_text().strip() if title_el else "Unknown Title"
                        company = company_el.inner_text().strip() if company_el else "Unknown Company"
                        loc = location_el.inner_text().strip() if location_el else location
                        snippet = snippet_el.inner_text().strip() if snippet_el else ""

                        # Apply local experience and job type filters
                        if not _job_matches_filters(title, snippet, experience_level, job_type):
                            continue

                        job_url = ""
                        if link_el:
                            jk = link_el.get_attribute('data-jk')
                            href = link_el.get_attribute('href')
                            if jk:
                                job_url = f"{domain}/viewjob?jk={jk}"
                            elif href:
                                job_url = href if href.startswith('http') else f"{domain}{href}"

                        if not job_url or job_url in seen_this_run:
                            continue
                        seen_this_run.add(job_url)

                        if job_url in exclude_urls:
                            excluded_count += 1
                            continue

                        is_easy_apply = _card_is_easy_apply(card)
                        if easy_apply_only and not is_easy_apply:
                            continue

                        results.append({
                            "title": title,
                            "company": company,
                            "location": loc,
                            "job_url": job_url,
                            "description": snippet,
                            "source": "indeed",
                            "job_type": "full-time",
                            "easy_apply": is_easy_apply,
                        })
                    except Exception as e:
                        print(f"Error extracting Indeed card: {e}")
                        continue

            # Fetch each job's real description from its own page — the
            # search-card snippet is only 1-2 lines, nowhere near enough
            # text for accurate skill-overlap scoring. Fall back to the
            # snippet if the detail page fetch fails, and stop entirely as
            # soon as Indeed's anti-bot wall shows up (it blocks fast —
            # usually after just 1-2 rapid detail-page navigations).
            for job in results:
                full_desc = _fetch_full_description(page, job["job_url"], ['#jobDescriptionText'])
                if full_desc is None:
                    break
                if full_desc:
                    job["description"] = full_desc

        except Exception as e:
            print(f"Error during Indeed search: {e}")
        finally:
            browser.close()

    return results, excluded_count


def search_naukri_jobs(query: str, location: str, limit: int = 15, 
                        exclude_urls: set = None, max_pages: int = 4, experience_level: str = "", job_type: str = ""):
    """
    Search public Naukri job listings using Playwright.
    """
    exclude_urls = exclude_urls or set()
    results = []
    seen_this_run = set()
    excluded_count = 0

    q_fmt = (query or "").replace(" ", "-").lower()
    l_fmt = (location or "").replace(" ", "-").lower()
    
    if not q_fmt and not l_fmt:
        base_url_path = "jobs"
    elif q_fmt and not l_fmt:
        base_url_path = f"{q_fmt}-jobs"
    elif not q_fmt and l_fmt:
        base_url_path = f"jobs-in-{l_fmt}"
    else:
        base_url_path = f"{q_fmt}-jobs-in-{l_fmt}"

    domain = "https://www.naukri.com"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--window-position=-3000,-3000'
            ]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        try:
            for page_num in range(1, max_pages + 1):
                if len(results) >= limit:
                    break

                search_url = f"{domain}/{base_url_path}"
                if page_num > 1:
                    search_url += f"-{page_num}"
                
                query_params = []
                if experience_level == 'fresher':
                    query_params.append("experience=0")
                elif experience_level == 'entry':
                    query_params.append("experience=1")
                elif experience_level == 'mid':
                    query_params.append("experience=3")
                elif experience_level == 'senior':
                    query_params.append("experience=6")
                
                if query_params:
                    search_url += "?" + "&".join(query_params)
                
                page.goto(search_url, timeout=35000, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)

                title_lower = (page.title() or "").lower()
                if "access denied" in title_lower or any(hint in title_lower for hint in _BLOCK_TITLE_HINTS):
                    print(f"Blocked by Naukri anti-bot at page {page_num}.")
                    break

                card_selectors = [
                    'article.jobTuple',
                    '.srp-jobtuple-wrapper',
                    'div.jobTuple',
                    'div[data-job-id]'
                ]
                
                cards = []
                for sel in card_selectors:
                    cards = page.query_selector_all(sel)
                    if cards:
                        break

                if not cards:
                    break

                for card in cards:
                    if len(results) >= limit:
                        break
                    try:
                        title_el = (card.query_selector('a.title') or card.query_selector('.title'))
                        company_el = (card.query_selector('a.comp-name') or card.query_selector('.subTitle') or card.query_selector('.company'))
                        location_el = (card.query_selector('.locWdth') or card.query_selector('.location'))
                        snippet_el = (card.query_selector('.job-description') or card.query_selector('.ellipsis.job-description'))
                        exp_el = card.query_selector('.expwdth') or card.query_selector('.exp-wrap')
                        
                        title = title_el.inner_text().strip() if title_el else "Unknown Title"
                        company = company_el.inner_text().strip() if company_el else "Unknown Company"
                        loc = location_el.inner_text().strip() if location_el else location
                        snippet = snippet_el.inner_text().strip() if snippet_el else ""
                        exp_text = exp_el.inner_text().strip() if exp_el else ""

                        if exp_text:
                            snippet = f"[Experience: {exp_text}] {snippet}"

                        if not _job_matches_filters(title, snippet, experience_level, job_type):
                            continue

                        job_url = ""
                        if title_el:
                            href = title_el.get_attribute('href')
                            if href:
                                job_url = href if href.startswith('http') else f"{domain}{href}"

                        if not job_url or job_url in seen_this_run:
                            continue
                        seen_this_run.add(job_url)

                        if job_url in exclude_urls:
                            excluded_count += 1
                            continue

                        results.append({
                            "title": title,
                            "company": company,
                            "location": loc,
                            "job_url": job_url,
                            "description": snippet,
                            "source": "naukri",
                            "job_type": "full-time",
                            "easy_apply": False,
                        })
                    except Exception as e:
                        print(f"Error extracting Naukri card: {e}")
                        continue
                        
                page.wait_for_timeout(2000)

            for job in results:
                full_desc = _fetch_full_description(page, job["job_url"], ['.job-desc', '.dang-inner-html', '.jobDesc'])
                if full_desc is None:
                    break
                if full_desc:
                    job["description"] = full_desc
                    
        except Exception as e:
            print(f"Error during Naukri search: {e}")
        finally:
            browser.close()

    return results, excluded_count


def _card_is_easy_apply(card) -> bool:
    try:
        text = (card.inner_text() or "").lower()
        if "easily apply" in text or "easy apply" in text:
            return True
        if card.query_selector('[data-testid="ia-container"]') or card.query_selector('.indeedApplyButton'):
            return True
    except Exception:
        pass
    return False


def _query_keywords(query: str) -> list:
    stop = {'the', 'and', 'for', 'developer', 'engineer', 'senior', 'junior', 'a', 'an', 'of', 'in', 'to'}
    words = [w for w in re.findall(r'[a-z0-9+#.]+', (query or '').lower()) if len(w) > 1 and w not in ('it', 'is', 'on', 'at', 'as', 'do', 'be', 'up')]
    strong = [w for w in words if w not in stop]
    return strong or words


def _title_matches(title: str, keywords: list) -> bool:
    if not keywords:
        return True
    t = (title or '').lower()
    return any(kw in t for kw in keywords)


# ---------------------------------------------------------------------------
# Experience-level keyword signals
# ---------------------------------------------------------------------------
SENIOR_KEYWORDS_RE = re.compile(
    r'\b(senior|sr|lead|principal|director|vp|manager|architect|staff|head)\b',
    re.IGNORECASE
)
JUNIOR_KEYWORDS_RE = re.compile(r'\b(junior|jr)\b', re.IGNORECASE)
FRESHER_KEYWORDS_RE = re.compile(
    r'\b(fresher|fresh graduate|graduate trainee|trainee|campus hire|'
    r'0[\s-]*1\s*years?|no experience required)\b',
    re.IGNORECASE
)
ENTRY_KEYWORDS_RE = re.compile(r'\b(entry[\s-]?level|entry level|associate)\b', re.IGNORECASE)

# Matches things like "2-4 years", "3+ years", "5 years of experience",
# "at least 2 years". Used to pull the minimum years-of-experience figure
# a posting asks for, so we can bucket by experience_level accurately
# instead of relying on title keywords alone (which "fresher" vs "entry"
# previously did — identically and incorrectly).
_YEARS_RE = re.compile(
    r'(\d+)\s*(?:\+|to|-)?\s*(?:\d+)?\s*\+?\s*years?\s*(?:of\s*)?(?:experience|exp)?',
    re.IGNORECASE
)


def _min_years_required(text: str):
    """
    Pulls the smallest 'N years' figure mentioned in a job title/description.
    Returns None if no such figure is found (so we don't wrongly reject
    postings that just never state a number).
    """
    if not text:
        return None
    matches = [int(m) for m in _YEARS_RE.findall(text) if m]
    return min(matches) if matches else None


def _job_matches_filters(title: str, description: str, experience_level: str, job_type: str) -> bool:
    title_lower = title.lower()
    desc_lower = description.lower()
    combined = f"{title_lower} {desc_lower}"
    min_years = _min_years_required(combined)

    is_senior_kw = bool(SENIOR_KEYWORDS_RE.search(title))
    is_junior_kw = bool(JUNIOR_KEYWORDS_RE.search(title))
    is_fresher_kw = bool(FRESHER_KEYWORDS_RE.search(combined))
    is_entry_kw = bool(ENTRY_KEYWORDS_RE.search(combined))

    # 1. Experience Level filter
    if experience_level == 'fresher':
        # Fresher = 0-1 yrs. Reject senior-sounding titles and anything
        # explicitly asking for 2+ years of experience.
        if is_senior_kw:
            return False
        if min_years is not None and min_years >= 2:
            return False
        # Require a positive fresher/entry/junior/graduate signal, unless
        # the posting simply never states a years figure (common for
        # fresher-friendly roles).
        if min_years is None and not (is_fresher_kw or is_entry_kw or is_junior_kw):
            if not re.search(r'\b(graduate|associate|jr)\b', title_lower):
                return False

    elif experience_level == 'entry':
        # Entry-level = up to ~2 yrs. Distinct from 'fresher': allows a
        # bit more experience, still excludes senior roles.
        if is_senior_kw:
            return False
        if min_years is not None and min_years > 2:
            return False

    elif experience_level == 'mid':
        if is_fresher_kw or is_junior_kw:
            return False
        if any(w in title_lower for w in ('director', 'vp', 'executive', 'chief')):
            return False
        if min_years is not None and (min_years < 2 or min_years > 6):
            return False

    elif experience_level == 'senior':
        if is_junior_kw or is_fresher_kw:
            return False
        if not is_senior_kw:
            has_sr_desc = min_years is not None and min_years >= 5
            if not has_sr_desc:
                return False

    # 2. Job Type filter
    if job_type == 'full-time':
        if 'intern' in title_lower and 'full-time' not in title_lower:
            return False
    elif job_type == 'part-time':
        if 'part-time' not in title_lower and 'part-time' not in desc_lower and 'part time' not in title_lower and 'part time' not in desc_lower:
            return False
    elif job_type == 'contract':
        if not any(w in title_lower or w in desc_lower for w in ('contract', 'freelance', 'temp', 'temporary')):
            return False
    elif job_type == 'internship':
        if 'intern' not in title_lower and 'intern' not in desc_lower:
            return False

    return True


def search_ats_jobs(query: str, location: str, limit: int = 25, experience_level: str = "", job_type: str = "") -> list:
    results = []
    keywords = _query_keywords(query)
    headers = {"User-Agent": "AutoJobApply/1.0 (+https://localhost)"}

    for company in GREENHOUSE_COMPANIES:
        if len(results) >= limit:
            break
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                continue
            for job in r.json().get('jobs', []):
                title = job.get('title', '')
                if not _title_matches(title, keywords):
                    continue
                loc = (job.get('location') or {}).get('name', '') or location
                if not _location_matches(loc, location):
                    continue
                content = re.sub(r'<[^>]+>', ' ', job.get('content', '') or '')[:1500]
                
                # Apply local filters
                if not _job_matches_filters(title, content, experience_level, job_type):
                    continue
                
                results.append({
                    "title": title,
                    "company": company.capitalize(),
                    "location": loc,
                    "job_url": job.get('absolute_url', ''),
                    "description": content,
                    "source": "greenhouse",
                    "job_type": "full-time",
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"Greenhouse {company} error: {e}")
            continue

    for company in LEVER_COMPANIES:
        if len(results) >= limit:
            break
        try:
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                continue
            for job in r.json():
                title = job.get('text', '')
                if not _title_matches(title, keywords):
                    continue
                loc = (job.get('categories') or {}).get('location', '') or location
                if not _location_matches(loc, location):
                    continue
                desc = (job.get('descriptionPlain', '') or '')[:1500]
                
                # Apply local filters
                if not _job_matches_filters(title, desc, experience_level, job_type):
                    continue
                
                results.append({
                    "title": title,
                    "company": company.capitalize(),
                    "location": loc,
                    "job_url": job.get('hostedUrl', ''),
                    "description": desc,
                    "source": "lever",
                    "job_type": "full-time",
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"Lever {company} error: {e}")
            continue

    return results


if __name__ == "__main__":
    jobs, _ = search_indeed_jobs("Software Engineer", "Remote")
    print(f"Found {len(jobs)} jobs on Indeed")
    for j in jobs:
        print(f"{j['title']} at {j['company']} ({j['location']}) - {j['job_url']}")