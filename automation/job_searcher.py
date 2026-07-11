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


def search_linkedin_jobs(query: str, location: str, limit: int = 10) -> list:
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
                        exclude_urls: set = None, max_pages: int = 4):
    """
    Search public Indeed job listings without logging in.

    NOTE: Indeed has aggressive anti-bot protection. This runs a real
    (headed-capable) Chromium and grabs whatever job cards render. If Indeed
    serves a captcha / block page, this returns an empty list gracefully — the
    caller should treat an empty result as "blocked or nothing found".

    easy_apply_only: when True, skips jobs that redirect to the employer's own
    site to apply ("Apply on company site") and keeps only jobs that use
    Indeed's own native apply flow ("Easily apply" / Indeed Apply widget).

    exclude_urls: job_urls to skip (e.g. jobs you've already seen/tracked) —
    without this, every run just re-scrapes Indeed's page 1 and shows the
    exact same top results every time. When set, this pages forward
    (Indeed's `start` offset, 10 results/page) up to `max_pages` pages until
    it collects `limit` NEW jobs or runs out of pages.

    Returns:
        (results: list, excluded_count: int) — excluded_count is how many
        matching jobs were skipped only because they were already in
        exclude_urls, so the caller can tell "genuinely nothing found /
        blocked" apart from "found matches but you've already seen them all".
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


def search_ats_jobs(query: str, location: str, limit: int = 25) -> list:
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
                results.append({
                    "title": title,
                    "company": company.capitalize(),
                    "location": loc,
                    "job_url": job.get('hostedUrl', ''),
                    "description": (job.get('descriptionPlain', '') or '')[:1500],
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