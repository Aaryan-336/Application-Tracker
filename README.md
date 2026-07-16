# 🛰️ AI Career Agent & Application Tracker

> An intelligent, developer-first job discovery engine and application funnel tracker. Auto-scrape listings from 10+ channels, match them to your parsed resume profile using LLMs (Groq Llama-3.3), and automatically update application statuses by syncing with your Gmail inbox.

<div align="center">
  <p align="center">
    <a href="#-key-features">Key Features</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> •
    <a href="#%EF%B8%8F-getting-started">Getting Started</a> •
    <a href="#-api-configuration">API Configurations</a>
  </p>
</div>

---

## ⚡ Key Features

### 🕵️ 1. Multi-Channel Discovery Engine
Scrapes and aggregates real-time postings across **10 different channels** (7 free + 3 API-key) with smart deduplication and high-recall keyword matching:
*   **ATS Company Boards**: Greenhouse (30+ boards including Stripe, OpenAI, Razorpay) & Lever (15+ boards including Netflix, Swiggy).
*   **Remote Powerhouses**: RemoteOK, Himalayas, Remotive, Arbeitnow, and The Muse.
*   **Global/Local Hubs (API)**: LinkedIn, Indeed, Naukri, Glassdoor, and Glassdoor (via JSearch RapidAPI & Apify).
*   **Smart Location Routing**: Automates country-wide matching for regional searches (e.g. searches in "Bangalore" pull remote "India" jobs).

### 🧠 2. AI Resume Parsing & Match Analyzer
*   **PDF Telemetry Parsing**: Upload your resume PDF and let the system parse out technical skills, education, and career milestones.
*   **LLM Fit Evaluation**: Compares your resume details against job descriptions using Groq APIs (Llama-3.3-70B).
*   **Actionable Analytics**: Computes a match score (0-100%), displays matching/missing skills, and outlines a custom-tailored match rationale.
*   **Per-User API Keys**: Store your personal Groq key in your profile to run match cycles under your own developer quota.

### 📥 3. Inbox Telemetry (Gmail Sync)
*   **Hands-free Tracking**: Scans your Gmail inbox for application confirmations, interview invites, rejections, or offers.
*   **Auto-Funnel Updates**: Matches company names and automatically shifts job cards in your dashboard through the pipeline (`Applied` ➔ `Interviewing` ➔ `Offer` / `Rejected`).
*   **Daily Sync Scheduler**: Background scheduler automatically runs sync cycles in the early hours of the morning.

### 🎛️ 4. Sci-Fi Cyberpunk UI
*   Beautiful terminal-style dashboard with tailored glassmorphic styling, HSL colors, and smooth micro-animations.
*   Interactive console settings panel to control target keyword queries, location tags, and exact scraping limits (up to 100).
*   Interactive status workflows to `Ignore`, `Save/Track`, or `Apply Direct`.

---

## 🔮 System Architecture

```mermaid
flowchart TD
    %% Scraper Input Flow
    UserQuery[User Search Query & Location] --> ScraperEngine[Scraper Service]
    
    %% Scraper Sources
    subgraph Sources [Job Discovery Channels]
        FreeAPI[Free APIs: Himalayas, RemoteOK, Remotive...]
        ATS[Direct ATS: Greenhouse & Lever Boards]
        PremiumAPI[Premium APIs: JSearch, Adzuna, Apify]
    end
    ScraperEngine --> Sources
    Sources -->|Aggregate & Deduplicate| RawJobs[Raw Job Listings]
    
    %% AI Pipeline
    RawJobs --> Database[(PostgreSQL DB)]
    PDFResume[User Resume PDF] -->|Parser Service| Telemetry[Parsed Skills & Work Experience]
    Telemetry --> DBUser[User Profile]
    DBUser --> Database
    
    %% Groq Match Engine
    Database -->|Job & Resume Payload| MatchEngine[AI Match Analyzer]
    MatchEngine -->|Groq API Call| LLM[Groq Llama-3.3-70b]
    LLM -->|Match Score & Rationale JSON| MatchEngine
    MatchEngine -->|Update User Jobs| DBMatches[Discovered Match Feed]
    
    %% Gmail Synchronization
    Gmail[User Gmail Inbox] -->|Inbox Telemetry| GmailService[Gmail Sync Service]
    GmailService -->|State Mutation| DBMatches
```

---

## 🛠️ Tech Stack

### Frontend
*   **Framework**: Next.js 15 (App Router, TypeScript)
*   **Styling**: Custom CSS / Tailwind CSS
*   **Icons**: Lucide React
*   **Animations**: Custom CSS Keyframes (FadeIn, SlideUp)

### Backend
*   **Framework**: FastAPI (Python 3.10+)
*   **Database ORM**: SQLAlchemy (PostgreSQL / SQLite fallback)
*   **Task Scheduling**: APScheduler (cron-based background job sync)
*   **AI Engine**: Groq SDK (Llama-3.3-70b-versatile)
*   **Mail Protocol**: IMAP (SSL-secure Gmail reading)

---

## 🚀 Getting Started

### Prerequisites
*   Node.js 18+
*   Python 3.10+
*   PostgreSQL running locally (or SQLite fallback)

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Aaryan-336/Application-Tracker.git
cd "Application-Tracker/backend"

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env
```

Configure your `.env` variables:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/applications_tracker
GROQ_API_KEY=your_global_groq_key_here
# Optional API Keys
JSEARCH_API_KEY=your_rapidapi_jsearch_key
APIFY_API_TOKEN=your_apify_token
ADZUNA_APP_ID=your_adzuna_id
ADZUNA_APP_KEY=your_adzuna_key
```

Run database initialization and start the FastAPI dev server:
```bash
# Initialize database tables
python app/init_db.py

# Launch FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd "../frontend"

# Install dependencies
npm install

# Start Next.js development server
npm run dev -- --port 3000
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔑 API Configuration

To get the most out of your career assistant, configure your keys inside the **Profile Manager** tab:

| API Provider | Free Tier Benefits | What it Enables | Key Page |
|---|---|---|---|
| **Groq** | Free developer tier | AI Resume & Job Matching | [groq.com/keys](https://console.groq.com/keys) |
| **JSearch** (RapidAPI) | 500 requests / month | Search LinkedIn, Indeed, Glassdoor, Naukri | [rapidapi.com](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) |
| **Adzuna** | 250 requests / day | Real-time global listings (US, IN, EU...) | [developer.adzuna.com](https://developer.adzuna.com/) |
| **Apify** | Free usage credits | Direct scraping/crawling of local Indian boards | [apify.com](https://console.apify.com/account#/integrations) |
| **Gmail** | 100% Free | Auto-syncing application statuses from email | [Google App Passwords](https://myaccount.google.com/apppasswords) |

> [!TIP]
> **Using Gmail Sync**: Generate an **App Password** from your Google Account settings (requires 2-Factor Authentication). Enter your email and the 16-character App Password inside the settings page to enable sync safely.

---

<div align="center">
  <sub>Built with ❤️ by Aaryan Khanna. Developer-friendly job tracking.</sub>
</div>
