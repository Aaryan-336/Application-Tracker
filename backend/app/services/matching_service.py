import json
from typing import Dict, Any
from app.models.resume import Resume
from app.models.job import Job
from app.services.groq_service import groq_service

class MatchingService:
    def match_resume_to_job(self, resume: Resume, job: Job) -> Dict[str, Any]:
        system_instruction = (
            "You are an expert technical recruiter and talent matching AI. "
            "Your task is to compare a candidate's resume (skills, experience, education) against a job description. "
            "Evaluate how well the candidate matches the job and output the analysis in JSON format. "
            "Response format MUST be a JSON object."
        )

        experience_level = resume.user.experience_level if (resume.user and resume.user.experience_level) else "Unspecified"

        prompt = (
            f"Analyze the match between this candidate's resume and the job description.\n\n"
            f"--- Candidate Resume ---\n"
            f"Skills: {resume.skills}\n"
            f"Experience: {resume.experience}\n"
            f"Education: {resume.education}\n\n"
            f"--- Candidate Preferred Experience Level ---\n"
            f"{experience_level}\n\n"
            f"--- Job Details ---\n"
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Location: {job.location}\n"
            f"Description:\n{job.description}\n\n"
            f"Evaluate the match and return a JSON object. "
            f"CRITICAL: Take the candidate's preferred experience level ({experience_level}) and actual work history into account when evaluating fit. "
            f"If the job description is for a senior/lead/managerial role and the candidate has marked their preferred level as 'entry' or has very little work experience, "
            f"penalize the match_score heavily and explain this mismatch in the match_rationale. Similarly, if there is a good alignment in seniority, factor that in positively.\n\n"
            f"Response schema MUST be:\n"
            f"{{\n"
            f"  \"match_score\": 85, // An integer score from 0 to 100 representing suitability\n"
            f"  \"match_rationale\": \"A 2-3 sentence summary explaining the match score and fit.\",\n"
            f"  \"matching_skills\": [\"list of skills from the resume that match the job description\"],\n"
            f"  \"missing_skills\": [\"list of key technical skills/tools requested in the job description that are missing from the resume\"]\n"
            f"}}"
        )

        response_str = groq_service.chat_completion(
            prompt=prompt,
            system_instruction=system_instruction,
            response_format={"type": "json_object"}
        )

        try:
            match_data = json.loads(response_str)
            # Ensure type constraints
            match_data["match_score"] = int(match_data.get("match_score", 50))
            return match_data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse match result from Groq: {response_str}. Error: {e}")
            return {
                "match_score": 50,
                "match_rationale": "Evaluated using fallback matching algorithm due to parsing errors.",
                "matching_skills": [],
                "missing_skills": []
            }

matching_service = MatchingService()
