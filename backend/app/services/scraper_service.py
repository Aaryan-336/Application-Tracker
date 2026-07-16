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

# ─── Location Intelligence ────────────────────────────────────────────────────
# India location keywords (preserved for backward compatibility)
INDIA_LOCATION_KEYWORDS = [
    "india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
    "chennai", "pune", "kolkata", "ahmedabad", "gurugram", "gurgaon",
    "noida", "jaipur", "chandigarh", "kochi", "indore", "lucknow",
    "coimbatore", "thiruvananthapuram", "nagpur", "surat", "vadodara",
]

# City → Country mapping for intelligent location expansion
CITY_TO_COUNTRY = {
    # US cities
    "san francisco": "united states", "new york": "united states",
    "seattle": "united states", "austin": "united states",
    "boston": "united states", "chicago": "united states",
    "los angeles": "united states", "denver": "united states",
    "miami": "united states", "atlanta": "united states",
    "dallas": "united states", "houston": "united states",
    "portland": "united states", "phoenix": "united states",
    "san jose": "united states", "san diego": "united states",
    "washington dc": "united states", "raleigh": "united states",
    "pittsburgh": "united states", "minneapolis": "united states",
    # UK cities
    "london": "united kingdom", "manchester": "united kingdom",
    "edinburgh": "united kingdom", "cambridge": "united kingdom",
    "bristol": "united kingdom", "birmingham": "united kingdom",
    "leeds": "united kingdom", "oxford": "united kingdom",
    # Canada
    "toronto": "canada", "vancouver": "canada", "montreal": "canada",
    "ottawa": "canada", "calgary": "canada", "waterloo": "canada",
    # Germany
    "berlin": "germany", "munich": "germany", "hamburg": "germany",
    "frankfurt": "germany", "cologne": "germany",
    # India
    "bangalore": "india", "bengaluru": "india", "mumbai": "india",
    "delhi": "india", "new delhi": "india", "hyderabad": "india",
    "pune": "india", "chennai": "india", "kolkata": "india",
    "gurugram": "india", "gurgaon": "india", "noida": "india",
    "ahmedabad": "india", "jaipur": "india", "kochi": "india",
    "indore": "india", "chandigarh": "india", "coimbatore": "india",
    "thiruvananthapuram": "india", "nagpur": "india", "surat": "india",
    # Others
    "singapore": "singapore", "tokyo": "japan", "sydney": "australia",
    "melbourne": "australia", "dublin": "ireland", "amsterdam": "netherlands",
    "paris": "france", "stockholm": "sweden", "zurich": "switzerland",
    "tel aviv": "israel", "sao paulo": "brazil",
}

# Country name aliases for matching variations (excluding two-letter codes to avoid conflicts with US states)
COUNTRY_ALIASES = {
    "united states": ["us", "usa", "u.s.", "u.s.a.", "america", "united states of america"],
    "united kingdom": ["uk", "u.k.", "britain", "england", "great britain"],
    "india": [],
    "canada": [],
    "germany": ["deutschland"],
    "australia": [],
    "singapore": [],
    "ireland": [],
    "netherlands": ["holland"],
    "france": [],
    "japan": [],
    "israel": [],
    "sweden": [],
    "switzerland": [],
    "brazil": [],
}

# US state abbreviation ↔ full name mapping
US_STATES = {
    "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas",
    "ca": "california", "co": "colorado", "ct": "connecticut", "de": "delaware",
    "fl": "florida", "ga": "georgia", "hi": "hawaii", "id": "idaho",
    "il": "illinois", "in": "indiana", "ia": "iowa", "ks": "kansas",
    "ky": "kentucky", "la": "louisiana", "me": "maine", "md": "maryland",
    "ma": "massachusetts", "mi": "michigan", "mn": "minnesota", "ms": "mississippi",
    "mo": "missouri", "mt": "montana", "ne": "nebraska", "nv": "nevada",
    "nh": "new hampshire", "nj": "new jersey", "nm": "new mexico", "ny": "new york",
    "nc": "north carolina", "nd": "north dakota", "oh": "ohio", "ok": "oklahoma",
    "or": "oregon", "pa": "pennsylvania", "ri": "rhode island", "sc": "south carolina",
    "sd": "south dakota", "tn": "tennessee", "tx": "texas", "ut": "utah",
    "vt": "vermont", "va": "virginia", "wa": "washington", "wv": "west virginia",
    "wi": "wisconsin", "wy": "wyoming",
}

# Adzuna country detection from location keywords
LOCATION_TO_ADZUNA_COUNTRY = {
    "us": ["united states", "usa", "america", "san francisco", "new york",
           "seattle", "austin", "boston", "chicago", "los angeles", "denver",
           "miami", "atlanta", "dallas", "houston", "portland", "san jose"],
    "gb": ["uk", "united kingdom", "london", "manchester", "britain",
           "england", "edinburgh", "cambridge", "bristol", "birmingham"],
    "in": INDIA_LOCATION_KEYWORDS,
    "ca": ["canada", "toronto", "vancouver", "montreal", "ottawa", "calgary"],
    "de": ["germany", "berlin", "munich", "hamburg", "frankfurt", "deutschland"],
    "au": ["australia", "sydney", "melbourne"],
    "fr": ["france", "paris"],
    "nl": ["netherlands", "amsterdam", "holland"],
    "sg": ["singapore"],
    "at": ["austria", "vienna"],
    "nz": ["new zealand", "auckland", "wellington"],
    "za": ["south africa", "cape town", "johannesburg"],
    "pl": ["poland", "warsaw", "krakow"],
    "it": ["italy", "milan", "rome"],
}

# ─── Seniority Detection ─────────────────────────────────────────────────────
SENIORITY_KEYWORDS = {
    "entry": ["junior", "jr.", "jr ", "entry", "entry-level", "entry level",
              "intern", "internship", "trainee", "graduate", "associate",
              "fresher", "0-2 years", "1-2 years", "0-1 years",
              "new grad", "early career", "beginner"],
    "mid":   ["mid-level", "mid level", "intermediate", "3+ years",
              "4+ years", "5+ years", "3-5 years", "2-4 years", "2-5 years"],
    "senior": ["senior", "sr.", "sr ", "lead", "principal", "staff",
               "architect", "head of", "director", "vp ", "vice president",
               "chief", "manager", "8+ years", "10+ years", "7+ years",
               "6+ years", "5-8 years", "team lead"],
}

LEVEL_ORDER = {"entry": 0, "mid": 1, "senior": 2, "lead": 3, "executive": 4}

# ─── Query Matching ──────────────────────────────────────────────────────────
STOPWORDS = {"and", "or", "the", "in", "at", "for", "of", "a", "an", "to",
             "is", "it", "be", "as", "on", "with", "by", "we", "our", "are"}

# ─── Source Confidence ────────────────────────────────────────────────────────
SOURCE_CONFIDENCE = {
    "Greenhouse": 1.0, "Lever": 1.0,
    "JSearch": 0.85, "Remotive": 0.8, "Himalayas": 0.8,
    "The Muse": 0.75, "RemoteOK": 0.7, "Arbeitnow": 0.7,
    "Apify Google Jobs": 0.65, "Adzuna": 0.6,
}


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
        """
        Smart keyword matching:
        1. If no query, match everything.
        2. Split query into words (using stopword filter, not length filter).
        3. Match if ALL query words are in the title,
           OR at least 60% of query words are in the title,
           OR all query words are present across combined fields.
        """
        if not query:
            return True

        query_words = [w.strip().lower() for w in query.split()
                       if w.strip().lower() not in STOPWORDS and len(w.strip()) > 0]
        if not query_words:
            return True

        # Combine all fields
        combined = " ".join((f or "") for f in fields).lower()

        # Check title (first field) with strict all-word matching
        first_field = (fields[0] or "").lower() if fields else ""
        title_match_count = sum(1 for w in query_words if w in first_field)

        # All query words in title → strong match
        if title_match_count == len(query_words):
            return True

        # At least 60% of query words in title → partial match
        if len(query_words) > 0 and title_match_count / len(query_words) >= 0.6:
            return True

        # Otherwise, check if all query words are present in combined text
        return all(w in combined for w in query_words)

    @staticmethod
    def _is_job_in_country(job_location: str, country: str) -> bool:
        """
        Check if a job location represents a given country, including checking city/state subregions
        (like checking if 'New York, NY' is in the 'united states').
        """
        job_loc_lower = (job_location or "").lower().strip()
        if not job_loc_lower:
            return False

        # 1. Direct name check with word boundary
        try:
            if re.search(r'\b' + re.escape(country) + r'\b', job_loc_lower):
                return True
        except re.error:
            if country == job_loc_lower:
                return True

        # 2. Alias match (e.g. 'us' or 'usa' for 'united states')
        for alias in COUNTRY_ALIASES.get(country, []):
            try:
                if re.search(r'\b' + re.escape(alias) + r'\b', job_loc_lower):
                    return True
            except re.error:
                if alias in job_loc_lower:
                    return True

        # 3. Special US logic: Check for US state abbreviation or full name
        if country == "united states":
            for abbr, full_name in US_STATES.items():
                try:
                    if re.search(r'\b' + re.escape(abbr) + r'\b', job_loc_lower):
                        return True
                except re.error:
                    pass
                if full_name in job_loc_lower:
                    return True

        # 4. Check if any city in the country is mentioned in the job location
        for city, cntry in CITY_TO_COUNTRY.items():
            if cntry == country:
                try:
                    if re.search(r'\b' + re.escape(city) + r'\b', job_loc_lower):
                        return True
                except re.error:
                    if city in job_loc_lower:
                        return True

        return False

    @staticmethod
    def _matches_location(location: str, job_location: str) -> bool:
        """
        Smart location matching with word-boundary awareness:
        1. If no location, match everything.
        2. If user wants 'remote', only match actually remote jobs.
        3. If job is remote/worldwide/anywhere/global, match any location.
        4. Word-boundary matching (prevents 'India' matching 'Indianapolis').
        5. City → country expansion (SF → United States).
        6. State abbreviation matching (CA → California).
        """
        if not location:
            return True

        loc_lower = location.lower().strip()
        job_loc_lower = (job_location or "").lower().strip()

        # 1. "Remote" search → only match remote jobs
        if loc_lower == "remote":
            remote_indicators = ["remote", "worldwide", "anywhere", "global",
                                 "work from home", "wfh", "distributed", "telecommute"]
            return any(w in job_loc_lower for w in remote_indicators) or not job_loc_lower.strip()

        # 2. Remote jobs match any location search
        if any(w in job_loc_lower for w in ["worldwide", "remote", "anywhere", "global"]):
            return True

        # 3. Word-boundary match (prevents "India" matching "Indianapolis")
        try:
            if re.search(r'\b' + re.escape(loc_lower) + r'\b', job_loc_lower):
                return True
        except re.error:
            if loc_lower in job_loc_lower:
                return True

        # 4. City → Country expansion
        country = CITY_TO_COUNTRY.get(loc_lower)
        if country:
            if ScraperService._is_job_in_country(job_location, country):
                return True

        # 5. If searching a country name / alias, check if job is in that country
        for country_name, aliases in COUNTRY_ALIASES.items():
            if loc_lower == country_name or loc_lower in aliases:
                if ScraperService._is_job_in_country(job_location, country_name):
                    return True

        # 6. US state abbreviation matching
        for abbr, full_name in US_STATES.items():
            if loc_lower == full_name or loc_lower == abbr:
                try:
                    if re.search(r'\b' + re.escape(abbr.upper()) + r'\b', job_location or ""):
                        return True
                except re.error:
                    pass
                if full_name in job_loc_lower:
                    return True

        return False

    @staticmethod
    def _clean_html(text: str, max_len: int = 2000) -> str:
        """Strip HTML tags and collapse whitespace."""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_len]

    # ─── Helper: detect job seniority from title/description ──────────────
    @staticmethod
    def _detect_job_seniority(title: str, description: str = "") -> str:
        """
        Detect seniority level from job title and description keywords.
        Title keywords take priority over description keywords.
        Returns: 'entry', 'mid', or 'senior'
        """
        title_lower = title.lower()
        # Check title first (highest signal)
        for level in ["entry", "senior", "mid"]:  # Check entry/senior before mid
            keywords = SENIORITY_KEYWORDS.get(level, [])
            if any(kw in title_lower for kw in keywords):
                return level

        # Fall back to description (first 500 chars)
        desc_lower = (description or "")[:500].lower()
        for level in ["entry", "senior", "mid"]:
            keywords = SENIORITY_KEYWORDS.get(level, [])
            if any(kw in desc_lower for kw in keywords):
                return level

        return "mid"  # default assumption if no signals found

    @staticmethod
    def _is_experience_compatible(user_level: str, job_level: str) -> bool:
        """
        Check if user's experience level is compatible with the job.
        Allows ±1 level difference (e.g., entry user can see entry + mid jobs).
        """
        if not user_level:
            return True  # No preference set, show everything
        user_rank = LEVEL_ORDER.get(user_level, 1)
        job_rank = LEVEL_ORDER.get(job_level, 1)
        return abs(user_rank - job_rank) <= 1

    # ─── Helper: detect Adzuna country code from location ─────────────────
    @staticmethod
    def _detect_adzuna_country(location: str) -> str:
        """Detect the best Adzuna country code from a location string."""
        loc = location.lower()
        for country_code, keywords in LOCATION_TO_ADZUNA_COUNTRY.items():
            if any(kw in loc for kw in keywords):
                return country_code
        return "us"  # fallback

    # ─── Helper: normalize company name for dedup ─────────────────────────
    @staticmethod
    def _normalize_company(name: str) -> str:
        """Normalize company name for deduplication comparison."""
        name = name.lower().strip()
        name = re.sub(r'[^a-z0-9]', '', name)  # Remove special chars/spaces
        return name

    # ─── Helper: validate scraped job data ────────────────────────────────
    @staticmethod
    def _validate_job(job: Dict[str, Any]) -> bool:
        """Reject garbage or incomplete job data before storing."""
        url = job.get("url", "")
        title = job.get("title", "")
        desc = job.get("description", "")

        # Must have a valid URL
        if not url.startswith(("http://", "https://")):
            return False
        # Title must be reasonable length
        if len(title) < 5 or len(title) > 300:
            return False
        # Reject HTML garbage in title
        if "<" in title or ">" in title:
            return False
        # Description should be meaningful (at least 30 chars)
        if len(desc) < 30:
            return False
        return True

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
            # Use proper location params instead of appending to query string
            num_pages = 2 if limit > 10 else 1
            url = (
                f"https://jsearch.p.rapidapi.com/search?"
                f"query={urllib.parse.quote(query)}"
                f"&num_pages={num_pages}"
                f"&page=1"
            )
            # Add dedicated location/remote params
            if location and location.lower() == "remote":
                url += "&remote_jobs_only=true"
            elif location:
                url += f"&location={urllib.parse.quote(location)}"

            headers = {
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }

            print(f"[JSearch] Fetching jobs for '{query}' in '{location}' (pages={num_pages})...")
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
    # Free tier: 250 requests/day — auto-detects country from location
    async def fetch_adzuna_jobs(self, query: str = "", location: str = "Remote", limit: int = 10, app_id: str = "", app_key: str = "") -> List[Dict[str, Any]]:
        aid = app_id or settings.ADZUNA_APP_ID
        akey = app_key or settings.ADZUNA_APP_KEY
        if not aid or not akey:
            print("[Adzuna] No API credentials configured, skipping.")
            return []

        jobs = []
        try:
            # Auto-detect country from location keywords (supports 14+ countries)
            country = self._detect_adzuna_country(location) if location else "us"

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
        groq_api_key: Optional[str] = None,
        experience_level: Optional[str] = None
    ) -> int:
        print(f"Starting job discovery: query='{query}', location='{location}', limit={limit}, sources={sources}, use_mock={use_mock}, experience_level={experience_level}")
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

        # ─── Validate scraped data ─────────────────────────────────────────
        valid_jobs = [job for job in scraped_jobs if self._validate_job(job)]
        invalid_count = len(scraped_jobs) - len(valid_jobs)
        if invalid_count > 0:
            print(f"[Validation] Filtered out {invalid_count} invalid/garbage job entries.")
        scraped_jobs = valid_jobs

        # ─── Deduplicate by URL + Company+Title ────────────────────────────
        seen_urls = set()
        seen_company_title = set()
        unique_jobs = []
        for job in scraped_jobs:
            # Primary: exact URL match
            if job["url"] in seen_urls:
                continue
            # Secondary: normalized company + title match
            norm_key = (
                self._normalize_company(job["company"]),
                re.sub(r'[^a-z0-9]', '', job["title"].lower())
            )
            if norm_key in seen_company_title:
                continue
            seen_urls.add(job["url"])
            seen_company_title.add(norm_key)
            unique_jobs.append(job)

        dedup_removed = len(scraped_jobs) - len(unique_jobs)
        if dedup_removed > 0:
            print(f"[Dedup] Removed {dedup_removed} duplicate entries (URL + company+title).")
        scraped_jobs = unique_jobs

        # ─── Detect seniority + filter by experience level ─────────────────
        if experience_level:
            pre_filter_count = len(scraped_jobs)
            filtered_jobs = []
            for job in scraped_jobs:
                job_seniority = self._detect_job_seniority(job["title"], job.get("description", ""))
                job["_seniority"] = job_seniority  # Store for later use
                if self._is_experience_compatible(experience_level, job_seniority):
                    filtered_jobs.append(job)
                else:
                    print(f"[Experience Filter] Skipped '{job['title']}' (detected: {job_seniority}, user: {experience_level})")
            scraped_jobs = filtered_jobs
            exp_filtered = pre_filter_count - len(scraped_jobs)
            if exp_filtered > 0:
                print(f"[Experience Filter] Filtered out {exp_filtered} jobs incompatible with '{experience_level}' level.")
        else:
            # Still detect seniority for storage, just don't filter
            for job in scraped_jobs:
                job["_seniority"] = self._detect_job_seniority(job["title"], job.get("description", ""))

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
                user_resumes[u.id] = (resume, u.groq_api_key or "", u.experience_level or "")

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
                    source=job_data["source"],
                    seniority_level=job_data.get("_seniority", "mid")
                )
                db.add(db_job)
                db.commit()
                db.refresh(db_job)
                new_jobs_count += 1
            else:
                db_job = existing_job
                # Update seniority if not previously set
                if not db_job.seniority_level and job_data.get("_seniority"):
                    db_job.seniority_level = job_data["_seniority"]
                    db.commit()

            # Run matches for this job against all user resumes
            for user_id, (resume, user_groq_key, user_exp_level) in user_resumes.items():
                # Per-user experience compatibility check
                job_seniority = job_data.get("_seniority", "mid")
                if user_exp_level and not self._is_experience_compatible(user_exp_level, job_seniority):
                    print(f"[Experience Filter] Skipping match for user {user_id} (level: {user_exp_level}) against '{db_job.title}' (level: {job_seniority})")
                    continue

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

                        # Apply deterministic experience level score adjustment
                        base_score = match_result.get("match_score", 50)
                        adjusted_score = matching_service.adjust_score_for_experience(
                            base_score, user_exp_level, job_seniority
                        )
                        if adjusted_score != base_score:
                            print(f"  [Experience Adj] Score {base_score} → {adjusted_score} (user: {user_exp_level}, job: {job_seniority})")

                        user_job = UserJob(
                            user_id=user_id,
                            job_id=db_job.id,
                            match_score=adjusted_score,
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

