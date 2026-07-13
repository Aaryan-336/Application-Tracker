import json
from typing import Dict, Any
from pypdf import PdfReader
from app.services.groq_service import groq_service

class ParserService:
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content:
                    text += text_content + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error reading PDF file {file_path}: {e}")
            raise ValueError(f"Failed to read PDF file: {str(e)}")

    def parse_resume_text(self, text: str) -> Dict[str, Any]:
        system_instruction = (
            "You are an expert Applicant Tracking System (ATS) resume parsing assistant. "
            "Your job is to analyze the raw resume text and convert it into a highly clean, structured JSON object. "
            "Return only valid JSON matching the exact schema specified, with no extra text or explanations. "
            "Response format MUST be a JSON object."
        )

        prompt = (
            f"Analyze the following resume text and extract the structured profile details.\n\n"
            f"Resume Text:\n\"\"\"\n{text}\n\"\"\"\n\n"
            f"Return JSON object with the following schema:\n"
            f"{{\n"
            f"  \"skills\": [\"list of technical and soft skills, e.g. Python, SQL, Project Management\"],\n"
            f"  \"experience\": [\n"
            f"    {{\n"
            f"      \"role\": \"Job Title/Role\",\n"
            f"      \"company\": \"Company Name\",\n"
            f"      \"duration\": \"Duration, e.g. Jan 2020 - Dec 2022 or 2 years\",\n"
            f"      \"description\": \"Brief description of duties/accomplishments\"\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"education\": [\n"
            f"    {{\n"
            f"      \"degree\": \"Degree, e.g. B.S.\",\n"
            f"      \"school\": \"School/University Name\",\n"
            f"      \"year\": \"Graduation Year, e.g. 2021\"\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"preferred_roles\": [\"List of roles they seem qualified for and are seeking, e.g. Backend Engineer, Fullstack Developer\"]\n"
            f"}}"
        )

        response_str = groq_service.chat_completion(
            prompt=prompt,
            system_instruction=system_instruction,
            response_format={"type": "json_object"}
        )

        try:
            parsed_data = json.loads(response_str)
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from Groq parser response: {response_str}")
            # Fallback structure
            return {
                "skills": [],
                "experience": [],
                "education": [],
                "preferred_roles": []
            }

parser_service = ParserService()
