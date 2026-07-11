def generate_resume_summary(skills: dict, primary_domain: str, experience_level: str, seniority: str) -> str:
    """
    Generates a concise AI summary based on extracted info.
    Example: "Fresher AI Engineer with experience in Python, Machine Learning, Computer Vision, YOLO, OpenCV, Deep Learning, NLP and backend development."
    """
    # 1. Title phrase
    title = primary_domain
    if primary_domain == "General Software Engineering":
        title = "Software Engineer"
    elif primary_domain == "Data Science & AI":
        title = "AI Engineer / Data Scientist"
    elif primary_domain == "Frontend":
        title = "Frontend Developer"
    elif primary_domain == "Backend":
        title = "Backend Developer"
    elif primary_domain == "Cloud & DevOps":
        title = "Cloud/DevOps Engineer"
        
    prefix = ""
    if seniority in ["Senior", "Lead"]:
        prefix = f"{seniority} "
    elif seniority == "Fresher":
        prefix = "Fresher "
    elif seniority == "Mid":
        prefix = "Mid-level "
        
    intro = f"{prefix}{title}".strip()
    
    # 2. Skills phrase
    all_tech = []
    for k in ['programming_languages', 'frameworks', 'libraries', 'cloud', 'databases']:
        if k in skills:
            all_tech.extend(skills[k])
            
    # Take top 8-10 skills
    top_skills = list(set(all_tech))[:10]
    
    if not top_skills:
        return f"{intro} looking for new opportunities."
        
    if len(top_skills) > 1:
        skills_str = ", ".join(top_skills[:-1]) + f", and {top_skills[-1]}"
    else:
        skills_str = top_skills[0]
        
    summary = f"{intro} with experience in {skills_str}."
    
    return summary
