import asyncio
import uuid
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.user import User
from app.models.resume import Resume
from app.models.user_job import UserJob
from app.services.matching_service import matching_service
from app.config import settings


# ─── Curated company board tokens ────────────────────────────────────────────
# Greenhouse Boards API: https://boards-api.greenhouse.io/v1/boards/{token}/jobs
GREENHOUSE_BOARDS = {
    # Global tech
    "stripe": "Stripe",
    "figma": "Figma",
    "notion": "Notion",
    "coinbase": "Coinbase",
    "discord": "Discord",
    "databricks": "Databricks",
    "ramp": "Ramp",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "vercel": "Vercel",
    "canva": "Canva",
    "gitlab": "GitLab",
    "airtable": "Airtable",
    "plaid": "Plaid",
    # India tech
    "razorpay": "Razorpay",
    "cred": "CRED",
    "zerodha": "Zerodha",
    "meesho": "Meesho",
    "postman": "Postman",
    "browserstack": "BrowserStack",
    "hasura": "Hasura",
    "zomato": "Zomato",
    "groww": "Groww",
    "phonepe": "PhonePe",
    "dream11": "Dream11",
    "freshworks": "Freshworks",
    "chargebee": "Chargebee",
    "clevertap": "CleverTap",
    "unacademy": "Unacademy",
}

# Lever Postings API: https://api.lever.co/v0/postings/{slug}?mode=json
LEVER_BOARDS = {
    # Global tech
    "netflix": "Netflix",
    "atlassian": "Atlassian",
    "twitch": "Twitch",
    "nerdwallet": "NerdWallet",
    "GoCardless": "GoCardless",
    "samsara": "Samsara",
    "relativity": "Relativity",
    # India tech
    "swiggy": "Swiggy",
    "curefit": "CureFit",
    "urbancompany": "Urban Company",
    "lenskart": "Lenskart",
    "leadsquared": "LeadSquared",
    "druva": "Druva",
    "moengage": "MoEngage",
}

# India location keywords for Adzuna country auto-detection
INDIA_LOCATION_KEYWORDS = [
    "india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
    "chennai", "pune", "kolkata", "ahmedabad", "gurugram", "gurgaon",
    "noida", "jaipur", "chandigarh", "kochi", "indore", "lucknow",
    "coimbatore", "thiruvananthapuram", "nagpur", "surat", "vadodara",
]


class ScraperService:
    """
    Job discovery service that aggregates listings from multiple free and
    API-key-based sources. All sources return real direct-apply URLs.
    """

    def __init__(self):
        self.mock_jobs = [
            {
                "title": "Backend Software Engineer (FastAPI & Python)",
                "company": "FastTech Solutions",
                "location": "Remote (US/Canada)",
                "description": "We are seeking a senior backend software engineer with extensive experience in Python, FastAPI, and PostgreSQL. You will design scalable REST APIs, optimize database queries, and integrate AI models. Required skills: Python, FastAPI, SQL, PostgreSQL, Redis, Docker, Git.",
                "url": "https://careers.fasttech.com/jobs/backend-fastapi",
                "source": "MockSource"
            },
            {
                "title": "Fullstack Developer (React & Node.js)",
                "company": "SaaS Launchpad",
                "location": "Remote (Global)",
                "description": "Join our product team to build modern web applications. You will work on Next.js frontend and Node.js backend. Experience with TypeScript, TailwindCSS, PostgreSQL, and AWS is required. Required skills: JavaScript, TypeScript, React, Next.js, Node.js, TailwindCSS, PostgreSQL.",
                "url": "https://careers.saaslaunchpad.io/jobs/fullstack-react",
                "source": "MockSource"
            },
            {
                "title": "AI/ML Engineer",
                "company": "NeuralMind Systems",
                "location": "Remote (EU)",
                "description": "We are looking for an AI engineer to develop agentic workflows and LLM pipelines. You will work with LangChain, LlamaIndex, Groq, and OpenAI APIs. Experience with vector databases (Pinecone, pgvector) is highly valued. Required skills: Python, PyTorch, LLMs, LangChain, vector databases, Groq.",
                "url": "https://apply.workable.com/neuralmind/j/12345ABC",
                "source": "MockSource"
            }
        ]

    # ─── HTTP helpers ─────────────────────────────────────────────────────
    def _http_get_json(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 20) -> Any:
        """Synchronous HTTP GET that returns parsed JSON. Used inside asyncio.to_thread."""
        import ssl
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _http_post_json(self, url: str, payload: Dict, headers: Optional[Dict[str, str]] = None, timeout: int = 45) -> Any:
        """Synchronous HTTP POST that returns parsed JSON. Used inside asyncio.to_thread."""
        import ssl
        context = ssl._create_unverified_context()
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        req.add_header("User-Agent", "Mozilla/5.0")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ─── Helper: keyword match check ──────────────────────────────────────
    @staticmethod
    def _matches_query(query: str, *fields: str) -> bool:
        """Return True if query is empty OR any field contains the query (case-insensitive)."""
        if not query:
            return True
        q = query.lower()
        return any(q in (f or "").lower() for f in fields)

    @staticmethod
    def _matches_location(location: str, job_location: str) -> bool:
        """Return True if location filter is empty, 'remote', or is found in job_location."""
        if not location:
            return True
        loc_lower = location.lower()
        if loc_lower == "remote":
            return True  # accept all when user wants remote
        return loc_lower in (job_location or "").lower()

    @staticmethod
    def _clean_html(text: str, max_len: int = 2000) -> str:
        """Strip HTML tags and collapse whitespace."""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_len]

    # ═══════════════════════════════════════════════════════════════════════
    #  FREE SOURCES (no API key required)
    # ═══════════════════════════════════════════════════════════════════════

    # ─── Remotive API ─────────────────────────────────────────────────────
    # Free, no API key needed, remote-only tech jobs
    async def fetch_remotive_jobs(self, query: str = "", location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(query)}&limit={limit * 3}"
            print(f"[Remotive] Fetching remote jobs for '{query}'...")
            data = await asyncio.to_thread(self._http_get_json, url)

            results = data.get("jobs", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("title", "")
                company = item.get("company_name", "Unknown Company")
                loc = item.get("candidate_required_location", "Remote")
                desc = self._clean_html(item.get("description", ""))
                apply_url = item.get("url", "")

                if not self._matches_location(location, loc):
                    continue
                if not self._matches_query(query, title, desc):
                    continue

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip() if loc else "Remote",
                        "description": desc or f"Remote job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "Remotive"
                    })
                    count += 1

            print(f"[Remotive] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[Remotive] API request failed: {e}")
        return jobs

    # ─── The Muse API ─────────────────────────────────────────────────────
    # Free, no API key needed, curated tech jobs
    async def fetch_themuse_jobs(self, query: str = "", location: str = "Remote", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []
        try:
            params = "page=1&descending=true"
            if location and location.lower() == "remote":
                params += "&location=Flexible%20/%20Remote"
            elif location:
                params += f"&location={urllib.parse.quote(location)}"
            params += "&category=Software%20Engineering"

            url = f"https://www.themuse.com/api/public/jobs?{params}"
            print(f"[The Muse] Fetching jobs for '{query}' in '{location}'...")
            data = await asyncio.to_thread(self._http_get_json, url)

            results = data.get("results", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("name", "")
                company_data = item.get("company", {})
                company = company_data.get("name", "Unknown Company") if isinstance(company_data, dict) else "Unknown Company"

                locations_list = item.get("locations", [])
                loc = ", ".join(l.get("name", "") for l in locations_list) if locations_list else location

                desc = self._clean_html(item.get("contents", ""))

                refs = item.get("refs", {})
                apply_url = refs.get("landing_page", "") if isinstance(refs, dict) else ""

                if not self._matches_query(query, title, desc):
                    continue

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip() if loc else "Not specified",
                        "description": desc or f"Tech job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "The Muse"
                    })
                    count += 1

            print(f"[The Muse] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[The Muse] API request failed: {e}")
        return jobs

    # ─── RemoteOK API ─────────────────────────────────────────────────────
    # Free, no API key needed, remote tech jobs JSON feed
    async def fetch_remoteok_jobs(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = "https://remoteok.com/api"
            print(f"[RemoteOK] Fetching remote jobs for '{query}'...")
            data = await asyncio.to_thread(self._http_get_json, url)

            # First item is metadata/legal notice — skip it
            results = data[1:] if isinstance(data, list) and len(data) > 1 else []
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("position", "")
                company = item.get("company", "Unknown Company")
                loc = item.get("location", "Remote")
                if not loc or not loc.strip():
                    loc = "Remote"
                desc = self._clean_html(item.get("description", ""))
                apply_url = item.get("url", "")
                if apply_url and not apply_url.startswith("http"):
                    apply_url = f"https://remoteok.com{apply_url}"

                tags = item.get("tags", [])
                tags_str = ", ".join(tags) if tags else ""

                if not self._matches_query(query, title, desc, tags_str):
                    continue

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip(),
                        "description": desc or f"Remote job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "RemoteOK"
                    })
                    count += 1

            print(f"[RemoteOK] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[RemoteOK] API request failed: {e}")
        return jobs

    # ─── Arbeitnow API ────────────────────────────────────────────────────
    # Free, no API key needed, global + remote, location & remote filters
    async def fetch_arbeitnow_jobs(self, query: str = "", location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            print(f"[Arbeitnow] Fetching jobs for '{query}' in '{location}'...")
            data = await asyncio.to_thread(self._http_get_json, url)

            results = data.get("data", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("title", "")
                company = item.get("company_name", "Unknown Company")
                loc = item.get("location", "")
                is_remote = item.get("remote", False)
                if is_remote:
                    loc = f"Remote — {loc}" if loc else "Remote"
                desc = self._clean_html(item.get("description", ""))
                apply_url = item.get("url", "")

                if not self._matches_location(location, loc):
                    # For remote filter, also check the remote flag
                    if location and location.lower() == "remote" and is_remote:
                        pass  # remote match
                    else:
                        continue

                if not self._matches_query(query, title, desc):
                    continue

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip() if loc else "Not specified",
                        "description": desc or f"Job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "Arbeitnow"
                    })
                    count += 1

            print(f"[Arbeitnow] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[Arbeitnow] API request failed: {e}")
        return jobs

    # ─── Himalayas API ────────────────────────────────────────────────────
    # Free, no API key needed, remote jobs with keyword and country search
    async def fetch_himalayas_jobs(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []
        try:
            params = f"limit={limit * 2}"
            if query:
                params += f"&q={urllib.parse.quote(query)}"
            url = f"https://himalayas.app/jobs/api?{params}"
            print(f"[Himalayas] Fetching remote jobs for '{query}'...")
            data = await asyncio.to_thread(self._http_get_json, url)

            results = data.get("jobs", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("title", "")
                company = item.get("companyName", "") or item.get("company_name", "Unknown Company")
                loc_parts = item.get("locationRestrictions", [])
                if isinstance(loc_parts, list):
                    loc = ", ".join(loc_parts) if loc_parts else "Remote"
                else:
                    loc = str(loc_parts) if loc_parts else "Remote"
                desc = self._clean_html(item.get("description", ""))
                apply_url = item.get("applicationLink", "") or item.get("url", "")

                if not self._matches_query(query, title, desc):
                    continue

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc if loc else "Remote",
                        "description": desc or f"Remote job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "Himalayas"
                    })
                    count += 1

            print(f"[Himalayas] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[Himalayas] API request failed: {e}")
        return jobs

    # ─── Greenhouse Boards API ────────────────────────────────────────────
    # Free, no API key, public job board endpoint for curated companies
    async def fetch_greenhouse_jobs(self, query: str = "", location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []

        async def _fetch_board(board_token: str, company_name: str) -> List[Dict[str, Any]]:
            board_jobs = []
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
                data = await asyncio.to_thread(self._http_get_json, url, timeout=10)

                for item in data.get("jobs", []):
                    title = item.get("title", "")
                    loc_data = item.get("location", {})
                    loc = loc_data.get("name", "") if isinstance(loc_data, dict) else str(loc_data)

                    desc = self._clean_html(item.get("content", ""))
                    apply_url = item.get("absolute_url", "")

                    if not self._matches_location(location, loc):
                        continue
                    if not self._matches_query(query, title, desc):
                        continue

                    if title and apply_url:
                        board_jobs.append({
                            "title": title.strip(),
                            "company": company_name,
                            "location": loc.strip() if loc else "Not specified",
                            "description": desc or f"Job listing for {title} at {company_name}.",
                            "url": apply_url.strip(),
                            "source": "Greenhouse"
                        })
            except Exception:
                pass  # silently skip boards that 404, timeout, etc.
            return board_jobs

        print(f"[Greenhouse] Fetching jobs from {len(GREENHOUSE_BOARDS)} company boards...")

        # Fetch concurrently with a semaphore to avoid hammering
        sem = asyncio.Semaphore(6)

        async def _fetch_with_sem(token: str, name: str):
            async with sem:
                return await _fetch_board(token, name)

        board_results = await asyncio.gather(
            *[_fetch_with_sem(token, name) for token, name in GREENHOUSE_BOARDS.items()],
            return_exceptions=True
        )

        for res in board_results:
            if isinstance(res, list):
                jobs.extend(res)

        jobs = jobs[:limit]
        print(f"[Greenhouse] Found {len(jobs)} jobs across company boards.")
        return jobs

    # ─── Lever Postings API ───────────────────────────────────────────────
    # Free, no API key, public postings for curated companies
    async def fetch_lever_jobs(self, query: str = "", location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        jobs = []

        async def _fetch_board(slug: str, company_name: str) -> List[Dict[str, Any]]:
            board_jobs = []
            try:
                url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                data = await asyncio.to_thread(self._http_get_json, url, timeout=10)

                if not isinstance(data, list):
                    return []

                for item in data:
                    title = item.get("text", "")
                    categories = item.get("categories", {})
                    loc = categories.get("location", "") if isinstance(categories, dict) else ""

                    desc_plain = item.get("descriptionPlain", "")
                    additional = item.get("additionalPlain", "")
                    desc = f"{desc_plain} {additional}".strip()[:2000]

                    apply_url = item.get("applyUrl", "") or item.get("hostedUrl", "")

                    if not self._matches_location(location, loc):
                        continue
                    if not self._matches_query(query, title, desc):
                        continue

                    if title and apply_url:
                        board_jobs.append({
                            "title": title.strip(),
                            "company": company_name,
                            "location": loc.strip() if loc else "Not specified",
                            "description": desc or f"Job listing for {title} at {company_name}.",
                            "url": apply_url.strip(),
                            "source": "Lever"
                        })
            except Exception:
                pass  # silently skip boards that 404, timeout, etc.
            return board_jobs

        print(f"[Lever] Fetching jobs from {len(LEVER_BOARDS)} company boards...")

        sem = asyncio.Semaphore(6)

        async def _fetch_with_sem(slug: str, name: str):
            async with sem:
                return await _fetch_board(slug, name)

        board_results = await asyncio.gather(
            *[_fetch_with_sem(slug, name) for slug, name in LEVER_BOARDS.items()],
            return_exceptions=True
        )

        for res in board_results:
            if isinstance(res, list):
                jobs.extend(res)

        jobs = jobs[:limit]
        print(f"[Lever] Found {len(jobs)} jobs across company boards.")
        return jobs

    # ═══════════════════════════════════════════════════════════════════════
    #  API-KEY SOURCES (require user-configured keys)
    # ═══════════════════════════════════════════════════════════════════════

    # ─── JSearch API (RapidAPI) ───────────────────────────────────────────
    # Free tier: 500 requests/month
    # Returns real jobs from LinkedIn, Indeed, Glassdoor, Naukri with direct apply links
    async def fetch_jsearch_jobs(self, query: str = "", location: str = "Remote", limit: int = 10, api_key: str = "") -> List[Dict[str, Any]]:
        key = api_key or settings.JSEARCH_API_KEY
        if not key:
            print("[JSearch] No API key configured, skipping.")
            return []

        jobs = []
        try:
            search_query = f"{query} in {location}" if location else query
            num_pages = 2 if limit > 10 else 1
            url = (
                f"https://jsearch.p.rapidapi.com/search?"
                f"query={urllib.parse.quote(search_query)}"
                f"&num_pages={num_pages}"
                f"&page=1"
            )
            headers = {
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }

            print(f"[JSearch] Fetching jobs for '{search_query}' (pages={num_pages})...")
            data = await asyncio.to_thread(self._http_get_json, url, headers)

            results = data.get("data", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("job_title", "")
                company = item.get("employer_name", "Unknown Company")
                loc = item.get("job_city", "") or item.get("job_state", "") or item.get("job_country", location)
                if item.get("job_is_remote"):
                    loc = f"Remote — {loc}" if loc else "Remote"
                desc = (item.get("job_description", "") or "")[:2000]
                apply_url = item.get("job_apply_link") or item.get("job_google_link", "")

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip() if loc else "Not specified",
                        "description": desc.strip() or f"Job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "JSearch"
                    })
                    count += 1

            print(f"[JSearch] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[JSearch] API request failed: {e}")
        return jobs

    # ─── Adzuna API ───────────────────────────────────────────────────────
    # Free tier: 250 requests/day — auto-detects India from location
    async def fetch_adzuna_jobs(self, query: str = "", location: str = "Remote", limit: int = 10, app_id: str = "", app_key: str = "") -> List[Dict[str, Any]]:
        aid = app_id or settings.ADZUNA_APP_ID
        akey = app_key or settings.ADZUNA_APP_KEY
        if not aid or not akey:
            print("[Adzuna] No API credentials configured, skipping.")
            return []

        jobs = []
        try:
            # Auto-detect India from location keywords
            country = "us"
            if location:
                loc_lower = location.lower()
                for kw in INDIA_LOCATION_KEYWORDS:
                    if kw in loc_lower:
                        country = "in"
                        break

            search_what = urllib.parse.quote(query)
            search_where = urllib.parse.quote(location) if location and location.lower() != "remote" else ""

            url = (
                f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?"
                f"app_id={aid}&app_key={akey}"
                f"&results_per_page={limit}"
                f"&what={search_what}"
            )
            if search_where:
                url += f"&where={search_where}"

            print(f"[Adzuna] Fetching jobs for '{query}' in '{location}' (country={country})...")
            data = await asyncio.to_thread(self._http_get_json, url)

            results = data.get("results", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("title", "")
                company = item.get("company", {}).get("display_name", "Unknown Company")
                loc = item.get("location", {}).get("display_name", location)
                desc = (item.get("description", "") or "")[:2000]
                apply_url = item.get("redirect_url", "") or item.get("adref", "")

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip() if loc else "Not specified",
                        "description": desc.strip() or f"Job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "Adzuna"
                    })
                    count += 1

            print(f"[Adzuna] Found {len(jobs)} jobs.")
        except Exception as e:
            print(f"[Adzuna] API request failed: {e}")
        return jobs

    # ─── Apify API ────────────────────────────────────────────────────────
    # For direct scraping of Naukri, Internshala, LinkedIn via Apify actors
    async def fetch_apify_jobs(self, query: str = "", location: str = "Remote", limit: int = 10, apify_api_token: str = "") -> List[Dict[str, Any]]:
        token = apify_api_token
        if not token:
            print("[Apify] No APIFY_API_TOKEN found, skipping.")
            return []

        jobs = []
        url = f"https://api.apify.com/v2/acts/apify~google-jobs-scraper/run-sync-get-dataset-items?token={token}"
        payload = {
            "queries": f"{query} jobs in {location}",
            "maxResultsPerQuery": limit,
            "maxPagesPerQuery": 1
        }

        try:
            print(f"[Apify] Triggering Google Jobs Scraper for '{query}' in '{location}'...")
            items = await asyncio.to_thread(self._http_post_json, url, payload)
            count = 0
            for item in items:
                if count >= limit:
                    break

                title = item.get("title")
                company = item.get("companyName") or item.get("company") or "Unknown Company"
                loc = item.get("location") or location
                desc = item.get("description") or item.get("jobDescription") or ""
                apply_url = item.get("applyLink") or item.get("jobUrl") or item.get("url")

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip(),
                        "description": desc.strip()[:2000] if desc else f"Job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "Apify Google Jobs"
                    })
                    count += 1
            print(f"[Apify] Successfully parsed {len(jobs)} items.")
        except Exception as e:
            print(f"[Apify] Failed: {e}")

        return jobs

    # ═══════════════════════════════════════════════════════════════════════
    #  MAIN DISCOVERY ORCHESTRATOR
    # ═══════════════════════════════════════════════════════════════════════
    async def discover_and_match_jobs(
        self,
        db: Session,
        query: str = "Software Engineer",
        location: str = "Remote",
        limit: int = 10,
        sources: List[str] = ["all"],
        use_mock: bool = False,
        apify_api_token: Optional[str] = None,
        jsearch_api_key: Optional[str] = None,
        adzuna_app_id: Optional[str] = None,
        adzuna_app_key: Optional[str] = None,
        groq_api_key: Optional[str] = None
    ) -> int:
        print(f"Starting job discovery: query='{query}', location='{location}', limit={limit}, sources={sources}, use_mock={use_mock}")
        scraped_jobs = []

        if use_mock:
            # Fallback to mock jobs
            suffix = str(uuid.uuid4())[:8]
            for mj in self.mock_jobs:
                job_copy = mj.copy()
                job_copy["url"] = f"{mj['url']}-{suffix}"
                scraped_jobs.append(job_copy)
        else:
            # Resolve "all" to available sources
            if "all" in sources:
                # All free sources always included
                sources = [
                    "remotive", "themuse", "remoteok",
                    "arbeitnow", "himalayas", "greenhouse", "lever"
                ]
                # Add API-key sources only if keys are available
                if jsearch_api_key or settings.JSEARCH_API_KEY:
                    sources.append("jsearch")
                if (adzuna_app_id or settings.ADZUNA_APP_ID) and (adzuna_app_key or settings.ADZUNA_APP_KEY):
                    sources.append("adzuna")
                if apify_api_token:
                    sources.append("apify")

            sources = list(set(sources))

            # Overfetch from each source — each gets the full user limit.
            # We deduplicate and trim to the exact requested limit after.
            per_source_limit = max(10, limit)

            tasks = []
            if "jsearch" in sources:
                tasks.append(self.fetch_jsearch_jobs(query, location, per_source_limit, jsearch_api_key or ""))
            if "remotive" in sources:
                tasks.append(self.fetch_remotive_jobs(query, location, per_source_limit))
            if "themuse" in sources:
                tasks.append(self.fetch_themuse_jobs(query, location, per_source_limit))
            if "adzuna" in sources:
                tasks.append(self.fetch_adzuna_jobs(query, location, per_source_limit, adzuna_app_id or "", adzuna_app_key or ""))
            if "apify" in sources:
                tasks.append(self.fetch_apify_jobs(query, location, per_source_limit, apify_api_token or ""))
            if "remoteok" in sources:
                tasks.append(self.fetch_remoteok_jobs(query, per_source_limit))
            if "arbeitnow" in sources:
                tasks.append(self.fetch_arbeitnow_jobs(query, location, per_source_limit))
            if "himalayas" in sources:
                tasks.append(self.fetch_himalayas_jobs(query, per_source_limit))
            if "greenhouse" in sources:
                tasks.append(self.fetch_greenhouse_jobs(query, location, per_source_limit))
            if "lever" in sources:
                tasks.append(self.fetch_lever_jobs(query, location, per_source_limit))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    scraped_jobs.extend(res)
                else:
                    print(f"Sub-source task failed: {res}")

        # ─── Deduplicate by URL ───────────────────────────────────────────
        seen_urls = set()
        unique_jobs = []
        for job in scraped_jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                unique_jobs.append(job)
        scraped_jobs = unique_jobs

        if not scraped_jobs:
            print("No jobs found from any source. Returning 0.")
            return 0

        new_jobs_count = 0
        matched_count = 0

        # Fetch all users with resumes to run matches
        users = db.query(User).all()
        user_resumes = {}
        for u in users:
            resume = db.query(Resume).filter(Resume.user_id == u.id).order_by(Resume.created_at.desc()).first()
            if resume:
                user_resumes[u.id] = (resume, u.groq_api_key or "")

        # Limit to the actual overall requested count
        scraped_jobs = scraped_jobs[:limit]

        rate_limit_hit = False
        for job_data in scraped_jobs:
            if rate_limit_hit:
                print("Job matching aborted early due to rate limit constraints.")
                break

            # Check if job already exists
            existing_job = db.query(Job).filter(Job.url == job_data["url"]).first()
            if not existing_job:
                db_job = Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    url=job_data["url"],
                    source=job_data["source"]
                )
                db.add(db_job)
                db.commit()
                db.refresh(db_job)
                new_jobs_count += 1
            else:
                db_job = existing_job

            # Run matches for this job against all user resumes
            for user_id, (resume, user_groq_key) in user_resumes.items():
                existing_match = db.query(UserJob).filter(
                    UserJob.user_id == user_id,
                    UserJob.job_id == db_job.id
                ).first()

                if not existing_match:
                    try:
                        # Prefer user's own Groq key, then caller's key, then global
                        effective_groq_key = user_groq_key or groq_api_key or ""
                        print(f"Matching resume ({user_id}) against job '{db_job.title}'")
                        match_result = matching_service.match_resume_to_job(resume, db_job, groq_api_key=effective_groq_key)

                        user_job = UserJob(
                            user_id=user_id,
                            job_id=db_job.id,
                            match_score=match_result.get("match_score", 50),
                            match_rationale=match_result.get("match_rationale", ""),
                            missing_skills=match_result.get("missing_skills", []),
                            matching_skills=match_result.get("matching_skills", []),
                            status="discovered"
                        )
                        db.add(user_job)
                        db.commit()
                        matched_count += 1
                    except Exception as e:
                        print(f"Error matching job {db_job.id} for user {user_id}: {e}")
                        db.rollback()
                        err_msg = str(e).lower()
                        if "rate limit" in err_msg or "429" in err_msg or "rate_limit" in err_msg:
                            print("Rate limit hit during matching. Setting abort flag.")
                            rate_limit_hit = True
                            break

        print(f"Discovery complete. Created {new_jobs_count} new jobs. Ran {matched_count} matches.")
        return new_jobs_count


scraper_service = ScraperService()
