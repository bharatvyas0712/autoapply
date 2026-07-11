from typing import Dict, Any
from similarity import compute_semantic_score
from skill_gap import analyze_skill_gap
from experience_matcher import compute_experience_score
from education_matcher import compute_education_score
from location_matcher import compute_location_score
from salary_matcher import compute_salary_score
from ranking import compute_overall_rank
from confidence import compute_confidence
from decision_engine import get_decision
from reason_generator import generate_reason
from llm_analyzer import analyze_with_llm

def evaluate_job_match(job: Dict[str, Any], user_profile: Dict[str, Any], job_emb: list, resume_emb: list) -> Dict[str, Any]:
    """Aggregates all matching logic for a single job against a user profile."""
    
    # 1. Similarity
    semantic_score = compute_semantic_score(resume_emb, job_emb)
    
    # 2. Skill Gap
    user_skills = user_profile.get('ai_keywords', []) + [s for sublist in user_profile.get('ai_extracted', {}).values() for s in sublist]
    skill_gap = analyze_skill_gap(user_skills, job.get('description', ''))
    
    # 3. Matchers
    exp_score = compute_experience_score(user_profile.get('experience_level', 'Mid'), job.get('description', ''))
    edu_score = compute_education_score(user_profile.get('education', ''), job.get('description', ''))
    loc_score = compute_location_score(
        user_profile.get('preferred_location', ''), 
        job.get('location', ''), 
        job.get('is_remote', False), 
        "remote" in str(user_profile.get('job_type_pref', '')).lower()
    )
    sal_score = compute_salary_score(user_profile.get('expected_salary', ''), job.get('salary', ''))
    
    # 4. Aggregate & Rank
    scores = {
        'semantic_score': semantic_score,
        'skill_score': skill_gap['skill_score'],
        'experience_score': exp_score,
        'education_score': edu_score,
        'location_score': loc_score,
        'salary_score': sal_score
    }
    overall = compute_overall_rank(scores)
    
    # 5. Confidence, Decision, Reason
    conf = compute_confidence(scores, job.get('description', ''))
    decision = get_decision(overall)
    reason = generate_reason(scores, skill_gap, decision)
    
    # 6. LLM (Optional)
    llm_analysis = analyze_with_llm(job.get('description', ''), user_profile)
    
    return {
        "scores": scores,
        "overall_score": overall,
        "confidence": conf,
        "decision": decision,
        "reason": reason,
        "skill_gap": skill_gap,
        "llm_analysis": llm_analysis
    }
