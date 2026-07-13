import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.services.matching_service import matching_service

def test_matching_logic():
    print("Initializing test matching objects...")
    
    # 1. Create a dummy user with Entry Level experience
    user = User(
        email="test_candidate@gmail.com",
        experience_level="entry"
    )
    
    # 2. Create a dummy resume associated with this user
    resume = Resume(
        skills=["Python", "FastAPI", "HTML"],
        experience=[{"role": "Intern Developer", "years": 1}],
        education=[],
        user=user
    )
    
    # 3. Create a Senior level job posting requiring 8 years experience
    senior_job = Job(
        title="Senior Lead backend Developer",
        company="BigTech Corp",
        location="Remote",
        description="We are seeking a Lead Backend Developer with 8+ years of experience in Python and FastAPI to architect our distributed database architectures."
    )
    
    # 4. Create an Entry level job posting requiring 0-2 years
    entry_job = Job(
        title="Junior Python Engineer",
        company="Startup Co",
        location="Remote",
        description="Looking for an entry level python developer. 0-2 years of experience. We will train you in FastAPI and HTML."
    )
    
    print("\nRunning matching service on Senior Job (should penalize Entry Level)...")
    try:
        senior_match = matching_service.match_resume_to_job(resume, senior_job)
        print(f"Senior Job Match Score: {senior_match['match_score']}/100")
        print(f"Rationale: {senior_match['match_rationale']}")
    except Exception as e:
        print(f"Failed to match senior job: {e}")

    print("\nRunning matching service on Junior Job (should fit well)...")
    try:
        entry_match = matching_service.match_resume_to_job(resume, entry_job)
        print(f"Junior Job Match Score: {entry_match['match_score']}/100")
        print(f"Rationale: {entry_match['match_rationale']}")
    except Exception as e:
        print(f"Failed to match junior job: {e}")

if __name__ == "__main__":
    # Check if GROQ_API_KEY is configured
    if not os.getenv("GROQ_API_KEY"):
        # Look in backend/.env
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
        
    if not os.getenv("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY is not set in environment or .env. The test cannot make live Groq LLM calls.")
    else:
        test_matching_logic()
