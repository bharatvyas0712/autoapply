def compute_confidence(scores: dict, job_description: str) -> float:
    """
    Computes a confidence score based on the quality of data.
    If the job description is too short, confidence drops.
    """
    confidence = 100.0
    if len(job_description) < 200:
        confidence -= 30.0
    elif len(job_description) < 500:
        confidence -= 15.0
        
    # Standard deviation of scores could also lower confidence (conflicting signals)
    score_list = [scores.get('semantic_score',0), scores.get('skill_score',0)]
    if abs(score_list[0] - score_list[1]) > 40:
        confidence -= 15.0
        
    return max(0.0, min(100.0, confidence))
