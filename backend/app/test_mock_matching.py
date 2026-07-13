import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from app.models.resume import Resume
from app.models.job import Job
from app.services.matching_service import matching_service

def run_test():
    print("Testing AI Matching Engine with Groq...")
    
    # Check if GROQ_API_KEY is configured
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY is not set in environment or .env. The test will fail if it makes a live call.")
        print("Please configure GROQ_API_KEY in backend/.env to run matching tests successfully.")
        return

    # Create dummy Resume object
    dummy_resume = Resume(
        skills=["Python", "FastAPI", "PostgreSQL", "React", "Docker", "Git"],
        experience=[
            {
                "role": "Software Developer",
                "company": "Dev Solutions",
                "duration": "2 years",
                "description": "Developed backend APIs using Python and FastAPI. Built frontend forms in React."
            }
        ],
        education=[
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "Tech University",
                "year": "2022"
            }
        ]
    )

    # Create dummy Job object
    dummy_job = Job(
        title="Backend Software Engineer (FastAPI)",
        company="FastAPI Corp",
        location="Remote",
        description=(
            "We are seeking a Backend Software Engineer specialized in Python and FastAPI. "
            "You will be responsible for creating robust microservices, designing SQL schemas, and deploying with Docker. "
            "Required skills: Python, FastAPI, PostgreSQL, SQL, Docker, Kubernetes."
        )
    )

    try:
        result = matching_service.match_resume_to_job(dummy_resume, dummy_job)
        print("\n=== AI Matching Verification Results ===")
        print(f"Match Score: {result.get('match_score')}%")
        print(f"Rationale: {result.get('match_rationale')}")
        print(f"Matching Skills: {result.get('matching_skills')}")
        print(f"Missing Skills: {result.get('missing_skills')}")
        print("=========================================\n")
    except Exception as e:
        print(f"ERROR: AI matching failed: {e}")

if __name__ == "__main__":
    run_test()
