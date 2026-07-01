"""Candidate data mapper.

Transforms raw candidate JSON dictionaries from the dataset into the internal CandidateProfile representation.
"""

from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CandidateMapper:
    """Maps raw dataset candidate dictionaries to normalized CandidateProfile dictionaries."""

    def map(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Map raw dictionary to a format suitable for CandidateProfile initialization.
        
        Args:
            raw: Raw candidate dictionary parsed from JSON.
            
        Returns:
            A dictionary containing mapped fields matching CandidateProfile schema.
        """
        # 1. Candidate ID
        candidate_id = raw.get("candidate_id", "UNKNOWN_ID")
        
        # 2. Candidate Name
        profile = raw.get("profile")
        if not isinstance(profile, dict):
            profile = {}
        name = profile.get("anonymized_name") or "Unknown Candidate"
        
        # 3. Experience
        try:
            experience_years = float(profile.get("years_of_experience", 0.0) or 0.0)
        except (ValueError, TypeError):
            experience_years = 0.0
            
        # 4. Current Role
        current_role = profile.get("current_title") or "Unknown Role"
        
        # 5. Skills
        raw_skills = raw.get("skills", [])
        skills = []
        if isinstance(raw_skills, list):
            for s in raw_skills:
                if isinstance(s, dict) and "name" in s and s["name"]:
                    skills.append(str(s["name"]))
                elif isinstance(s, str) and s:
                    skills.append(s)
                
        # 6. Education
        raw_edu = raw.get("education", [])
        edu_list = []
        if isinstance(raw_edu, list):
            for e in raw_edu:
                if isinstance(e, dict):
                    degree = e.get("degree") or ""
                    field = e.get("field_of_study") or ""
                    institution = e.get("institution") or ""
                    start = e.get("start_year") or ""
                    end = e.get("end_year") or ""
                    
                    edu_parts = []
                    degree_field = f"{degree} {field}".strip()
                    if degree_field:
                        edu_parts.append(degree_field)
                    if institution:
                        edu_parts.append(institution)
                    if start or end:
                        edu_parts.append(f"{start}-{end}")
                        
                    if edu_parts:
                        edu_list.append(" - ".join(edu_parts))
        
        education = "\n".join(edu_list) if edu_list else "No education provided"
        
        # 7. Projects
        projects = []
        
        # 8. Resume Text
        resume_parts = []
        
        summary = profile.get("summary")
        if summary:
            resume_parts.append(f"Summary:\n{summary}")
            
        headline = profile.get("headline")
        if headline:
            resume_parts.append(f"Headline:\n{headline}")
            
        raw_history = raw.get("career_history", [])
        if isinstance(raw_history, list) and raw_history:
            history_strs = []
            for h in raw_history:
                if isinstance(h, dict):
                    title = h.get("title") or "Unknown Title"
                    company = h.get("company") or "Unknown Company"
                    start = h.get("start_date") or ""
                    end = h.get("end_date") or "Present"
                    desc = h.get("description") or ""
                    
                    h_str = f"{title} at {company} ({start} to {end})"
                    if desc:
                        h_str += f"\n{desc}"
                    history_strs.append(h_str)
            if history_strs:
                resume_parts.append("Career History:\n" + "\n\n".join(history_strs))
            
        if skills:
            resume_parts.append("Skills:\n" + ", ".join(skills))
            
        if education:
            resume_parts.append("Education:\n" + education)
            
        raw_certs = raw.get("certifications", [])
        if isinstance(raw_certs, list) and raw_certs:
            cert_strs = []
            for c in raw_certs:
                if isinstance(c, dict) and c.get("name"):
                    cert_strs.append(str(c["name"]))
                elif isinstance(c, str):
                    cert_strs.append(c)
            if cert_strs:
                resume_parts.append("Certifications:\n" + ", ".join(cert_strs))
                
        resume_text = "\n\n".join(resume_parts) if resume_parts else "No resume data available"
        
        # 9. Behaviour Signals
        raw_signals = raw.get("redrob_signals") or {}
        if isinstance(raw_signals, dict):
            try:
                interview_completed_val = float(raw_signals.get("interview_completion_rate") or 0.0)
                interview_completed = interview_completed_val > 0.0
            except (ValueError, TypeError):
                interview_completed = False

            try:
                github_score = float(raw_signals.get("github_activity_score") or -1.0)
            except (ValueError, TypeError):
                github_score = -1.0

            try:
                response_rate = float(raw_signals.get("recruiter_response_rate") or 0.0)
            except (ValueError, TypeError):
                response_rate = 0.0

            try:
                completeness = float(raw_signals.get("profile_completeness_score") or 0.0)
            except (ValueError, TypeError):
                completeness = 0.0

            try:
                notice = int(raw_signals.get("notice_period_days") or 0)
            except (ValueError, TypeError):
                notice = 0

            behaviour_signals = {
                "candidate_id": candidate_id,
                "github_activity_score": github_score,
                "recruiter_response_rate": response_rate,
                "profile_completeness": completeness,
                "notice_period_days": notice,
                "interview_completed": interview_completed
            }
        else:
            behaviour_signals = {
                "candidate_id": candidate_id,
                "github_activity_score": -1.0,
                "recruiter_response_rate": 0.0,
                "profile_completeness": 0.0,
                "notice_period_days": 0,
                "interview_completed": False
            }
        
        return {
            "candidate_id": candidate_id,
            "name": name,
            "skills": skills,
            "experience_years": experience_years,
            "current_role": current_role,
            "projects": projects,
            "education": education,
            "resume_text": resume_text,
            "behaviour_signals": behaviour_signals
        }
