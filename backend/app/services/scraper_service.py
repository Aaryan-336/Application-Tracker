import asyncio
import uuid
import json
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


class ScraperService:
    """
    Job discovery service that uses structured APIs instead of fragile web scraping.
    All sources return real direct-apply URLs.
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

    def _http_get_json(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 20) -> Any:
        """Synchronous HTTP GET that returns parsed JSON. Used inside asyncio.to_thread."""
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _http_post_json(self, url: str, payload: Dict, headers: Optional[Dict[str, str]] = None, timeout: int = 45) -> Any:
        """Synchronous HTTP POST that returns parsed JSON. Used inside asyncio.to_thread."""
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        req.add_header("User-Agent", "Mozilla/5.0")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ─── JSearch API (RapidAPI) ───────────────────────────────────────────
    # Free tier: 500 requests/month
    # Returns real jobs from LinkedIn, Indeed, Glassdoor with direct apply links
    async def fetch_jsearch_jobs(self, query: str = "", location: str = "Remote", limit: int = 5, api_key: str = "") -> List[Dict[str, Any]]:
        key = api_key or settings.JSEARCH_API_KEY
        if not key:
            print("[JSearch] No API key configured, skipping.")
            return []

        jobs = []
        try:
            search_query = f"{query} in {location}" if location else query
            url = (
                f"https://jsearch.p.rapidapi.com/search?"
                f"query={urllib.parse.quote(search_query)}"
                f"&num_pages=1"
                f"&page=1"
            )
            headers = {
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }

            print(f"[JSearch] Fetching jobs for '{search_query}'...")
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
                desc = item.get("job_description", "")[:2000]
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

    # ─── Remotive API ─────────────────────────────────────────────────────
    # Free, no API key needed, remote-only tech jobs
    async def fetch_remotive_jobs(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        jobs = []
        try:
            url = f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(query)}&limit={limit * 2}"
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
                desc = item.get("description", "")[:2000]
                apply_url = item.get("url", "")

                # Filter by query keyword if the API returned too broadly
                if query and query.lower() not in title.lower() and query.lower() not in (desc or "").lower():
                    continue

                if title and apply_url:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip() if loc else "Remote",
                        "description": desc.strip() or f"Remote job listing for {title} at {company}.",
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
    async def fetch_themuse_jobs(self, query: str = "", location: str = "Remote", limit: int = 5) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # The Muse supports category and location filtering
            params = f"page=1&descending=true"
            if location and location.lower() == "remote":
                params += "&location=Flexible%20/%20Remote"
            elif location:
                params += f"&location={urllib.parse.quote(location)}"
            # The Muse categories for tech
            params += "&category=Software%20Engineering"

            url = f"https://www.themuse.com/api/public/jobs?{params}"
            print(f"[The Muse] Fetching jobs...")
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
                
                desc_parts = item.get("contents", "")
                # Strip HTML tags from description
                import re
                desc = re.sub(r"<[^>]+>", " ", desc_parts)
                desc = re.sub(r"\s+", " ", desc).strip()[:2000]

                refs = item.get("refs", {})
                apply_url = refs.get("landing_page", "") if isinstance(refs, dict) else ""

                # Filter by query keyword
                if query and query.lower() not in title.lower() and query.lower() not in desc.lower():
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

    # ─── Adzuna API ───────────────────────────────────────────────────────
    # Free tier: 250 requests/day
    async def fetch_adzuna_jobs(self, query: str = "", location: str = "Remote", limit: int = 5, app_id: str = "", app_key: str = "") -> List[Dict[str, Any]]:
        aid = app_id or settings.ADZUNA_APP_ID
        akey = app_key or settings.ADZUNA_APP_KEY
        if not aid or not akey:
            print("[Adzuna] No API credentials configured, skipping.")
            return []

        jobs = []
        try:
            # Adzuna uses country codes in the URL. Default to 'us'.
            country = "us"
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

            print(f"[Adzuna] Fetching jobs for '{query}' in '{location}'...")
            data = await asyncio.to_thread(self._http_get_json, url)

            results = data.get("results", [])
            count = 0
            for item in results:
                if count >= limit:
                    break

                title = item.get("title", "")
                company = item.get("company", {}).get("display_name", "Unknown Company")
                loc = item.get("location", {}).get("display_name", location)
                desc = item.get("description", "")[:2000]
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

    # ─── Apify API (kept from original) ───────────────────────────────────
    async def fetch_apify_jobs(self, query: str = "", location: str = "Remote", limit: int = 5, apify_api_token: str = "") -> List[Dict[str, Any]]:
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

    # ─── Main Discovery Orchestrator ──────────────────────────────────────
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
        adzuna_app_key: Optional[str] = None
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
                sources = ["remotive", "themuse"]
                # Add API-key sources only if keys are available
                if jsearch_api_key or settings.JSEARCH_API_KEY:
                    sources.append("jsearch")
                if (adzuna_app_id or settings.ADZUNA_APP_ID) and (adzuna_app_key or settings.ADZUNA_APP_KEY):
                    sources.append("adzuna")
                if apify_api_token:
                    sources.append("apify")

            sources = list(set(sources))
            limit_per_source = max(2, limit // len(sources)) if sources else limit

            tasks = []
            if "jsearch" in sources:
                tasks.append(self.fetch_jsearch_jobs(query, location, limit_per_source, jsearch_api_key or ""))
            if "remotive" in sources:
                tasks.append(self.fetch_remotive_jobs(query, limit_per_source))
            if "themuse" in sources:
                tasks.append(self.fetch_themuse_jobs(query, location, limit_per_source))
            if "adzuna" in sources:
                tasks.append(self.fetch_adzuna_jobs(query, location, limit_per_source, adzuna_app_id or "", adzuna_app_key or ""))
            if "apify" in sources:
                tasks.append(self.fetch_apify_jobs(query, location, limit_per_source, apify_api_token or ""))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    scraped_jobs.extend(res)
                else:
                    print(f"Sub-source task failed: {res}")

        # Fallback to mock if nothing found
        if not scraped_jobs:
            print("No jobs found from any source. Injecting mock fallback jobs.")
            suffix = str(uuid.uuid4())[:8]
            for mj in self.mock_jobs:
                job_copy = mj.copy()
                job_copy["url"] = f"{mj['url']}-{suffix}"
                scraped_jobs.append(job_copy)

        new_jobs_count = 0
        matched_count = 0

        # Fetch all users with resumes to run matches
        users = db.query(User).all()
        user_resumes = {}
        for u in users:
            resume = db.query(Resume).filter(Resume.user_id == u.id).order_by(Resume.created_at.desc()).first()
            if resume:
                user_resumes[u.id] = resume

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
            for user_id, resume in user_resumes.items():
                existing_match = db.query(UserJob).filter(
                    UserJob.user_id == user_id,
                    UserJob.job_id == db_job.id
                ).first()

                if not existing_match:
                    try:
                        print(f"Matching resume ({user_id}) against job '{db_job.title}'")
                        match_result = matching_service.match_resume_to_job(resume, db_job)

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
