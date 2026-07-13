import asyncio
import uuid
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright
from app.models.job import Job
from app.models.user import User
from app.models.resume import Resume
from app.models.user_job import UserJob
from app.services.matching_service import matching_service

class ScraperService:
    def resolve_direct_url(self, url: str) -> str:
        if not url or not url.startswith("http"):
            return url
            
        import urllib.parse
        import urllib.request
        from urllib.parse import urlparse, urlunparse
        
        parsed = urlparse(url)
        clean_domains = ["greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "bamboohr.com", "smartrecruiters.com", "breezy.hr"]
        if any(domain in parsed.netloc for domain in clean_domains) and "redirect" not in url:
            # Just strip queries to clean tracking parameters
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

        try:
            # Simple redirect following using urllib.request
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')]
            
            # Use GET to follow redirects (urllib follows automatically)
            req = urllib.request.Request(url)
            with opener.open(req, timeout=5) as resp:
                final_url = resp.geturl()
                parsed_final = urlparse(final_url)
                
                query_params = urllib.parse.parse_qsl(parsed_final.query)
                clean_params = [(k, v) for k, v in query_params if not k.startswith("utm_") and k not in ["ref", "source", "origin", "tracking", "originalSubdomain"]]
                new_query = urllib.parse.urlencode(clean_params)
                return urlunparse((parsed_final.scheme, parsed_final.netloc, parsed_final.path, parsed_final.params, new_query, parsed_final.fragment))
        except Exception as e:
            print(f"[URL Resolver] Failed to resolve redirect for {url}: {e}")
            return url

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

    async def scrape_weworkremotely(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        jobs = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                url = "https://weworkremotely.com/categories/remote-programming-jobs"
                print(f"[Scraper WWR] Navigating to {url}")
                await page.goto(url, timeout=30000)
                await page.wait_for_selector("section.jobs", timeout=10000)
                
                job_elements = await page.query_selector_all("section.jobs article ul li:not(.view-all)")
                
                count = 0
                for el in job_elements:
                    if count >= limit:
                        break
                        
                    title_el = await el.query_selector("span.title")
                    company_el = await el.query_selector("span.company")
                    region_el = await el.query_selector("span.region")
                    link_el = await el.query_selector("a[href*='/remote-jobs/']")
                    
                    if title_el and company_el and link_el:
                        title = await title_el.inner_text()
                        company = await company_el.inner_text()
                        location = await region_el.inner_text() if region_el else "Remote"
                        href = await link_el.get_attribute("href")
                        job_url = f"https://weworkremotely.com{href}"
                        
                        # Simple keyword filtering if query is provided
                        if query and query.lower() not in title.lower() and query.lower() not in company.lower():
                            continue
                            
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": location.strip(),
                            "description": f"Remote programming job at {company} listed on We Work Remotely. Location: {location}.",
                            "url": job_url,
                            "source": "WeWorkRemotely"
                        })
                        count += 1
                        
                # Follow links to extract full description for scraped jobs
                for job in jobs:
                    try:
                        await page.goto(job["url"], timeout=15000)
                        desc_container = await page.query_selector("#job-details")
                        if desc_container:
                            desc_text = await desc_container.inner_text()
                            if desc_text:
                                job["description"] = desc_text.strip()
                    except Exception as e:
                        print(f"[Scraper WWR] Failed to scrape details for {job['url']}: {e}")
                        
                await browser.close()
        except Exception as e:
            print(f"[Scraper WWR] Playwright scraping failed: {e}")
        return jobs

    async def scrape_yc(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        jobs = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # We query YC jobs page
                search_q = urllib.parse.quote(query)
                url = f"https://www.ycombinator.com/jobs?q={search_q}"
                print(f"[Scraper YC] Navigating to {url}")
                
                await page.goto(url, timeout=30000)
                await page.wait_for_selector(".space-y-2", timeout=10000)
                
                # Gather job listings
                job_elements = await page.query_selector_all(".flex.flex-col.justify-between.border-b")
                
                count = 0
                for el in job_elements:
                    if count >= limit:
                        break
                    
                    title_el = await el.query_selector(".font-bold")
                    company_el = await el.query_selector(".text-orange-500")
                    link_el = await el.query_selector("a[href*='/jobs/role/']")
                    
                    if title_el and link_el:
                        title = await title_el.inner_text()
                        company = await company_el.inner_text() if company_el else "YC Startup"
                        href = await link_el.get_attribute("href")
                        job_url = f"https://www.ycombinator.com{href}"
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": "Remote / USA",
                            "description": f"Job posting at YC Startup {company}. Apply on YCombinator jobs portal.",
                            "url": job_url,
                            "source": "YCombinator"
                        })
                        count += 1
                
                # Fetch job details to get exact apply links if possible
                for job in jobs:
                    try:
                        await page.goto(job["url"], timeout=15000)
                        # Look for apply button or text
                        apply_el = await page.query_selector("a.bg-orange-500")
                        if apply_el:
                            apply_url = await apply_el.get_attribute("href")
                            if apply_url and apply_url.startswith("http"):
                                job["url"] = apply_url
                        
                        desc_el = await page.query_selector(".whitespace-pre-line")
                        if desc_el:
                            job["description"] = await desc_el.inner_text()
                    except Exception as e:
                        print(f"[Scraper YC] Detail scrape failed: {e}")
                        
                await browser.close()
        except Exception as e:
            print(f"[Scraper YC] Scraping failed: {e}")
        return jobs

    async def scrape_internshala(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        jobs = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                search_q = urllib.parse.quote(query)
                url = f"https://internshala.com/jobs/keywords-{search_q}"
                print(f"[Scraper Internshala] Navigating to {url}")
                
                await page.goto(url, timeout=30000)
                
                # Check if elements are found
                job_elements = await page.query_selector_all(".individual_internship")
                
                count = 0
                for el in job_elements:
                    if count >= limit:
                        break
                    
                    title_el = await el.query_selector(".job-title-container a")
                    company_el = await el.query_selector(".company-name")
                    location_el = await el.query_selector(".location_names")
                    
                    if title_el and company_el:
                        title = await title_el.inner_text()
                        company = await company_el.inner_text()
                        location = await location_el.inner_text() if location_el else "India"
                        href = await title_el.get_attribute("href")
                        job_url = f"https://internshala.com{href}" if href.startswith("/") else href
                        
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": location.strip(),
                            "description": f"Job placement opportunity at {company} listed on Internshala. Location: {location}.",
                            "url": job_url,
                            "source": "Internshala"
                        })
                        count += 1
                
                # Fetch details
                for job in jobs:
                    try:
                        await page.goto(job["url"], timeout=15000)
                        desc_container = await page.query_selector(".text-container")
                        if desc_container:
                            job["description"] = await desc_container.inner_text()
                    except Exception as e:
                        print(f"[Scraper Internshala] Detail fetch failed: {e}")
                        
                await browser.close()
        except Exception as e:
            print(f"[Scraper Internshala] Scraping failed: {e}")
        return jobs

    async def scrape_web_direct(self, query: str = "", location: str = "Remote", limit: int = 5) -> List[Dict[str, Any]]:
        # This performs a DuckDuckGo HTML query to retrieve direct Greenhouse/Lever/Ashby apply links!
        # It's highly robust, handles corporate portals, and bypasses Cloudflare walls.
        jobs = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                search_terms = f"site:greenhouse.io OR site:lever.co OR site:jobs.ashbyhq.com \"{query}\" \"{location}\" jobs"
                encoded_search = urllib.parse.quote(search_terms)
                url = f"https://html.duckduckgo.com/html/?q={encoded_search}"
                
                print(f"[Scraper Web] Navigating to DDG: {url}")
                await page.goto(url, timeout=30000)
                
                result_elements = await page.query_selector_all(".web-result")
                count = 0
                for el in result_elements:
                    if count >= limit:
                        break
                    
                    link_el = await el.query_selector(".result__snippet")
                    title_el = await el.query_selector(".result__link")
                    url_el = await el.query_selector(".result__url")
                    
                    if title_el and url_el:
                        title_text = await title_el.inner_text()
                        snippet_text = await link_el.inner_text() if link_el else ""
                        raw_url = await url_el.inner_text()
                        
                        # Build formatted URL
                        job_url = "https://" + raw_url.strip() if not raw_url.startswith("http") else raw_url.strip()
                        
                        # Clean up URL (DuckDuckGo sometimes formats them)
                        if "greenhouse.io" in job_url:
                            # e.g. boards.greenhouse.io/company/jobs/1234
                            match = re.search(r"greenhouse\.io/[a-zA-Z0-9_\-]+/jobs/\d+", job_url)
                            if match:
                                job_url = "https://" + match.group(0)
                        elif "lever.co" in job_url:
                            match = re.search(r"jobs\.lever\.co/[a-zA-Z0-9_\-]+/[a-z0-9\-]+", job_url)
                            if match:
                                job_url = "https://" + match.group(0)
                        
                        # Try to parse company name from title or snippet
                        # e.g., "Software Engineer at HubSpot" or "HubSpot - Software Engineer"
                        company = "Job Listing"
                        title = title_text
                        if " - " in title_text:
                            parts = title_text.split(" - ")
                            title = parts[0]
                            company = parts[1]
                        elif " at " in title_text:
                            parts = title_text.split(" at ")
                            title = parts[0]
                            company = parts[1]
                            
                        # If title is generic, skip
                        if not title or len(title) < 3:
                            continue
                            
                        jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "location": location,
                            "description": snippet_text.strip() or f"Job placement matching query found on {job_url}.",
                            "url": job_url,
                            "source": "Web Direct"
                        })
                        count += 1
                        
                await browser.close()
        except Exception as e:
            print(f"[Scraper Web] General web search failed: {e}")
        return jobs

    async def scrape_apify(self, query: str = "", location: str = "Remote", limit: int = 5, apify_api_token: str = None) -> List[Dict[str, Any]]:
        token = apify_api_token
        if not token:
            print("[Scraper Apify] No APIFY_API_TOKEN found, skipping.")
            return []
            
        import urllib.request
        import json
        import asyncio
        
        jobs = []
        url = f"https://api.apify.com/v2/acts/apify~google-jobs-scraper/run-sync-get-dataset-items?token={token}"
        payload = {
            "queries": f"{query} jobs in {location}",
            "maxResultsPerQuery": limit,
            "maxPagesPerQuery": 1
        }
        
        def run_request():
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
                
        try:
            print(f"[Scraper Apify] Triggering Apify Google Jobs Scraper for '{query}' in '{location}'...")
            items = await asyncio.to_thread(run_request)
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
                        "description": desc.strip()[:1000] if desc else f"Job listing for {title} at {company}.",
                        "url": apply_url.strip(),
                        "source": "Apify Google Jobs"
                    })
                    count += 1
            print(f"[Scraper Apify] Successfully parsed {len(jobs)} items.")
        except Exception as e:
            print(f"[Scraper Apify] Failed to scrape with Apify: {e}")
            
        return jobs

    async def discover_and_match_jobs(
        self, 
        db: Session, 
        query: str = "Software Engineer", 
        location: str = "Remote", 
        limit: int = 10, 
        sources: List[str] = ["all"],
        use_mock: bool = False,
        apify_api_token: Optional[str] = None
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
            # Aggregate jobs based on requested sources
            tasks = []
            
            # Divide limit among sources
            if "all" in sources:
                if apify_api_token:
                    sources = ["weworkremotely", "yc", "internshala", "apify"]
                else:
                    sources = ["weworkremotely", "yc", "internshala", "web"]
            
            if apify_api_token and "web" in sources:
                sources = [s if s != "web" else "apify" for s in sources]
                
            sources = list(set(sources))
            limit_per_source = max(1, limit // len(sources)) if sources else limit
            
            if "weworkremotely" in sources:
                tasks.append(self.scrape_weworkremotely(query, limit_per_source))
            if "yc" in sources:
                tasks.append(self.scrape_yc(query, limit_per_source))
            if "internshala" in sources:
                tasks.append(self.scrape_internshala(query, limit_per_source))
            if "apify" in sources:
                tasks.append(self.scrape_apify(query, location, limit_per_source, apify_api_token))
            if "web" in sources or "linkedin" in sources or "naukri" in sources or "wellfound" in sources or "hubspot" in sources:
                # We run the general web search which aggregates all these
                tasks.append(self.scrape_web_direct(query, location, limit_per_source))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    scraped_jobs.extend(res)
                else:
                    print(f"Sub-scraper task failed: {res}")

        # Fallback to mock if nothing scraped
        if not scraped_jobs:
            print("No jobs scraped. Injecting mock fallback jobs.")
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

        for job_data in scraped_jobs:
            resolved_url = self.resolve_direct_url(job_data["url"])
            job_data["url"] = resolved_url
            
            # Check if job already exists
            existing_job = db.query(Job).filter(Job.url == resolved_url).first()
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

        print(f"Discovery complete. Created {new_jobs_count} new jobs. Ran {matched_count} matches.")
        return new_jobs_count

scraper_service = ScraperService()
