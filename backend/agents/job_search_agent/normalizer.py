from typing import Dict, Any, Optional
from datetime import datetime
from utilities.helpers import clean_text

class JobNormalizer:
    @staticmethod
    def normalize(raw_job: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Normalizes a raw job dictionary from any platform into a common schema.
        """
        return {
            "title": clean_text(raw_job.get("title", "")),
            "company": clean_text(raw_job.get("company", "")),
            "location": clean_text(raw_job.get("location", "")),
            "platform": platform,
            "job_url": raw_job.get("job_url", ""),
            "description": clean_text(raw_job.get("description", "")),
            "salary": clean_text(raw_job.get("salary", "")),
            "employment_type": clean_text(raw_job.get("employment_type", "Full Time")),
            "is_remote": JobNormalizer._is_remote(raw_job),
            "posted_date": raw_job.get("posted_date", datetime.utcnow().isoformat()),
            "company_logo": raw_job.get("company_logo", ""),
            "job_id": raw_job.get("job_id", ""),
            "application_url": raw_job.get("application_url", raw_job.get("job_url", ""))
        }
        
    @staticmethod
    def _is_remote(raw_job: Dict[str, Any]) -> bool:
        remote_flags = ["remote", "work from home", "wfh"]
        location = str(raw_job.get("location", "")).lower()
        title = str(raw_job.get("title", "")).lower()
        
        if raw_job.get("is_remote") is True:
            return True
            
        return any(flag in location for flag in remote_flags) or any(flag in title for flag in remote_flags)
