from typing import Dict, Any
import re

def compute_experience_score(resume_level: str, job_desc: str) -> float:
    """Matches seniority levels and penalizes excessive requirements."""
    desc = job_desc.lower()
    
    req_years = 0
    years_match = re.findall(r'(\d+)(?:\+|-)?\s*(?:years|yrs)\s*(?:of)?\s*experience', desc)
    if years_match:
        req_years = max([int(y) for y in years_match])
        
    user_years = 0
    if resume_level == "Fresher" or resume_level == "Entry Level": user_years = 1
    elif resume_level == "Mid Level" or resume_level == "Mid": user_years = 3
    elif resume_level == "Senior Level" or resume_level == "Senior": user_years = 6
    elif resume_level == "Executive/Lead" or resume_level == "Lead": user_years = 10
    else: user_years = 2 # default
    
    # If job requires significantly more years than user has, penalize heavily
    if req_years > user_years + 2:
        return 20.0
    # If job requires less or equal, it's a good match (though overqualified might be a slight penalty if too high, but we'll ignore for now)
    if req_years <= user_years:
        return 100.0
        
    # Marginal gap
    return 70.0
