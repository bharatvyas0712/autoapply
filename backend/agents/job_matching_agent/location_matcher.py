def compute_location_score(pref_location: str, job_location: str, is_remote: bool, pref_remote: bool) -> float:
    """Matches location based on remote preference and city match."""
    score = 50.0
    
    # 1. Remote matching
    if is_remote and pref_remote:
        score += 50.0
        return min(score, 100.0)
    elif not is_remote and pref_remote:
        score -= 20.0 # penalty for requiring onsite when remote preferred
        
    # 2. City/State matching
    if pref_location and job_location:
        if pref_location.lower() in job_location.lower() or job_location.lower() in pref_location.lower():
            score += 50.0
            
    return max(0.0, min(100.0, score))
