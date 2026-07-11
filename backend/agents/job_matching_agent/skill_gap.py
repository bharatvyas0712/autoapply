from typing import Dict, List, Any
import re

def analyze_skill_gap(resume_skills: List[str], job_description: str) -> Dict[str, Any]:
    """
    Identifies matched, missing, and nice-to-have skills.
    In a full production scenario with NLP, we would extract required skills from the job_description.
    Here we use a robust heuristic keyword match against common tech skills.
    """
    desc_lower = job_description.lower()
    
    # Simulate extracting skills from job description using the same KNOWLEDGE_BASE concept 
    # from the Resume Intelligence Engine. For speed, we define a small subset.
    common_skills = [
        "python", "java", "javascript", "c++", "c#", "ruby", "go", "php", "swift", "kotlin", "typescript", "rust",
        "react", "angular", "vue", "django", "flask", "spring", "express", "node.js",
        "aws", "azure", "gcp", "docker", "kubernetes", "mysql", "postgresql", "mongodb", "redis",
        "machine learning", "deep learning", "opencv", "tensorflow", "pytorch", "nlp", "llm"
    ]
    
    job_required_skills = set()
    for skill in common_skills:
        pattern = rf'\b{re.escape(skill)}\b'
        if skill in ['c++', 'c#']:
            pattern = rf'\b{re.escape(skill)}\b' # specific handling might be needed, simplified here
        if re.search(pattern, desc_lower):
            job_required_skills.add(skill.title() if len(skill)>3 else skill.upper())
            
    resume_skills_lower = [s.lower() for s in resume_skills]
    
    matched = []
    missing = []
    critical_missing = []
    
    for req_skill in job_required_skills:
        if req_skill.lower() in resume_skills_lower:
            matched.append(req_skill)
        else:
            missing.append(req_skill)
            # Simple heuristic for 'critical' (e.g. if it appears multiple times in desc)
            if desc_lower.count(req_skill.lower()) > 2:
                critical_missing.append(req_skill)
                
    # Calculate a simple score based on matched / required
    score = 100.0
    if job_required_skills:
        score = (len(matched) / len(job_required_skills)) * 100.0
        
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "nice_to_have_skills": [], # Could be extracted from 'nice to have' sections
        "critical_missing_skills": critical_missing,
        "skill_score": score
    }
