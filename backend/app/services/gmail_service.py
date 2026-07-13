import imaplib
import email
from email.header import decode_header
import datetime
import json
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.job import Job
from app.models.user_job import UserJob
from app.services.groq_service import groq_service

class GmailService:
    def parse_body(self, msg) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    # If we only have HTML, we can still use it, but strip HTML tags to avoid hitting token limits
                    try:
                        html_content = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        # Basic HTML tag stripping
                        text_content = re.sub(r"<[^>]+>", " ", html_content)
                        text_content = re.sub(r"\s+", " ", text_content)
                        body += text_content
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                pass
        return body[:4000] # Limit to 4000 characters to prevent huge token counts

    def decode_mime_header(self, header_val: str) -> str:
        if not header_val:
            return ""
        decoded = decode_header(header_val)
        parts = []
        for text, encoding in decoded:
            if isinstance(text, bytes):
                try:
                    parts.append(text.decode(encoding or "utf-8", errors="ignore"))
                except Exception:
                    parts.append(text.decode("latin1", errors="ignore"))
            else:
                parts.append(str(text))
        return "".join(parts)

    def test_connection(self, email_address: str, app_password: str) -> bool:
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(email_address, app_password)
            mail.logout()
            return True
        except Exception as e:
            print(f"Gmail connection test failed: {e}")
            return False

    async def sync_user_emails(self, db: Session, user: User, days_back: int = 14) -> List[Dict[str, Any]]:
        if not user.gmail_address or not user.gmail_app_password:
            raise ValueError("Gmail configuration is missing credentials.")

        updates_found = []
        mail = None
        try:
            # 1. Connect and login
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(user.gmail_address, user.gmail_app_password)
            mail.select("INBOX")

            # Calculate date filter (e.g. SINCE 01-Jul-2026)
            since_date = (datetime.date.today() - datetime.timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # 2. Search for all emails since date
            status, messages = mail.search(None, f'SINCE {since_date}')
            if status != "OK" or not messages[0]:
                print(f"No messages found since {since_date}")
                user.gmail_last_synced = datetime.datetime.utcnow()
                db.commit()
                return []

            message_ids = messages[0].split()
            print(f"Found {len(message_ids)} emails since {since_date} for user {user.email}. Evaluating headers...")

            # Relevant keywords in subject to check
            placement_keywords = [
                "application", "applied", "interview", "offer", "rejection", "reject",
                "update", "careers", "recruiting", "recruiter", "placement", "job", 
                "shortlist", "assessment", "test", "hiring", "scheduling"
            ]

            # Process in reverse (newest first)
            for msg_id in reversed(message_ids):
                # Fetch header first to filter quickly
                res, data = mail.fetch(msg_id, "(RFC822.HEADER)")
                if res != "OK":
                    continue
                
                raw_headers = data[0][1]
                msg = email.message_from_bytes(raw_headers)
                
                subject = self.decode_mime_header(msg.get("Subject", ""))
                sender = self.decode_mime_header(msg.get("From", ""))
                date_str = msg.get("Date", "")

                subject_lower = subject.lower()
                sender_lower = sender.lower()

                # Check if it looks placement related based on headers
                is_candidate = any(kw in subject_lower or kw in sender_lower for kw in placement_keywords)
                if not is_candidate:
                    continue

                # Fetch full email body for candidates
                res_body, data_body = mail.fetch(msg_id, "(RFC822)")
                if res_body != "OK":
                    continue
                
                full_msg = email.message_from_bytes(data_body[0][1])
                body_content = self.parse_body(full_msg)

                # 3. Ask LLM to analyze the email
                analysis_prompt = f"""
Analyze the following email metadata and content to determine if it is a job placement or job application related communication.

From: {sender}
Subject: {subject}
Date: {date_str}

Content:
{body_content}

Your goal is to parse this and extract the details. You MUST return valid JSON matching this schema:
{{
  "is_placement_related": boolean,
  "company": "string or null (Name of company hiring)",
  "job_title": "string or null (e.g. Software Engineer)",
  "status": "applied" | "interviewing" | "rejected" | "offered" | null,
  "notes": "string or null (e.g. Short summary such as 'Application received' or 'Interview scheduled for July 25th')"
}}
Only return JSON. Do not include any explanation or markdown formatting.
"""
                try:
                    llm_output = groq_service.chat_completion(
                        prompt=analysis_prompt,
                        system_instruction="You are a precise backend parsing assistant that outputs strictly valid JSON.",
                        temperature=0.0,
                        response_format={"type": "json_object"}
                    )
                    
                    parsed_result = json.loads(llm_output)
                    if parsed_result.get("is_placement_related") and parsed_result.get("company"):
                        company = parsed_result["company"]
                        job_title = parsed_result.get("job_title") or "Position"
                        status_val = parsed_result.get("status") or "applied"
                        notes = parsed_result.get("notes") or ""

                        # Process this update in the database
                        # Try to find existing matched job by company and title (fuzzy or exact)
                        job_query = db.query(Job).filter(
                            Job.company.ilike(company)
                        )
                        if job_title and job_title != "Position":
                            job_query = job_query.filter(Job.title.ilike(f"%{job_title}%"))
                        
                        existing_job = job_query.first()
                        
                        if not existing_job:
                            # Create new job
                            new_job = Job(
                                title=job_title,
                                company=company,
                                location="Remote/Email Direct",
                                description=f"Imported from email update: '{subject}'",
                                url="https://mail.google.com",
                                source="GmailSync"
                            )
                            db.add(new_job)
                            db.commit()
                            db.refresh(new_job)
                            job_id = new_job.id
                        else:
                            job_id = existing_job.id

                        # Find user-job entry
                        user_job = db.query(UserJob).filter(
                            UserJob.user_id == user.id,
                            UserJob.job_id == job_id
                        ).first()

                        if not user_job:
                            # Create new tracked application
                            user_job = UserJob(
                                user_id=user.id,
                                job_id=job_id,
                                match_score=100, # Hand-imported/verified
                                match_rationale="Automatically detected and synced from Gmail inbox.",
                                status=status_val,
                                notes=notes,
                                applied_at=datetime.datetime.utcnow() if status_val == "applied" else None
                            )
                            db.add(user_job)
                            db.commit()
                            updates_found.append({
                                "company": company,
                                "job_title": job_title,
                                "status": status_val,
                                "notes": notes,
                                "type": "new"
                            })
                        else:
                            # Only update if status is different or notes changed
                            if user_job.status != status_val or user_job.notes != notes:
                                user_job.status = status_val
                                user_job.notes = notes
                                if status_val == "applied" and not user_job.applied_at:
                                    user_job.applied_at = datetime.datetime.utcnow()
                                db.commit()
                                updates_found.append({
                                    "company": company,
                                    "job_title": job_title,
                                    "status": status_val,
                                    "notes": notes,
                                    "type": "updated"
                                })
                except Exception as parse_err:
                    print(f"Failed to parse email with Groq/JSON: {parse_err}")
                    continue

            user.gmail_last_synced = datetime.datetime.utcnow()
            db.commit()
            return updates_found
        except Exception as e:
            print(f"Gmail sync operation failed: {e}")
            raise e
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass

gmail_service = GmailService()
