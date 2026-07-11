def compute_education_score(resume_edu: str, job_desc: str) -> float:
    """Matches degree requirements (Masters, PhD, Bachelors)."""
    desc = job_desc.lower()
    
    requires_phd = "phd" in desc or "ph.d" in desc
    requires_masters = "masters" in desc or "ms" in desc.split() or "m.s" in desc
    requires_bachelors = "bachelors" in desc or "bs" in desc.split() or "b.s" in desc
    
    resume_edu_lower = str(resume_edu).lower()
    has_phd = "phd" in resume_edu_lower
    has_masters = "master" in resume_edu_lower or "ms" in resume_edu_lower.split()
    has_bachelors = "bachelor" in resume_edu_lower or "bs" in resume_edu_lower.split()
    
    if requires_phd and not has_phd: return 40.0
    if requires_masters and not (has_masters or has_phd): return 60.0
    if requires_bachelors and not (has_bachelors or has_masters or has_phd): return 60.0

    return 100.0
