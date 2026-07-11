from typing import Dict, Any

class FieldMapper:
    """
    Maps standard profile keys to incoming form inputs using label/name heuristics.
    """
    
    @staticmethod
    def map_field_to_profile(label: str, name: str, profile: Dict[str, Any]) -> Any:
        text = f"{label} {name}".lower()
        
        # Personal
        if "first" in text and "name" in text:
            return profile.get("first_name", "")
        if "last" in text and "name" in text:
            return profile.get("last_name", "")
        if "full" in text and "name" in text or (text == "name"):
            return f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
        if "email" in text:
            return profile.get("email", "")
        if "phone" in text or "mobile" in text:
            return profile.get("phone", "")
        if "linkedin" in text:
            return profile.get("linkedin_url", "")
        if "github" in text:
            return profile.get("github_url", "")
        if "portfolio" in text or "website" in text:
            return profile.get("portfolio_url", "")
        if "address" in text:
            return profile.get("location", "")
            
        # Work / Salary
        if "expected" in text and "salary" in text:
            return str(profile.get("expected_salary", ""))
        if "notice" in text and "period" in text:
            return str(profile.get("notice_period_days", ""))
        if "years" in text and "experience" in text:
            return str(profile.get("experience_years", ""))
            
        return None
