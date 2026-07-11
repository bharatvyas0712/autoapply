def generate_job_titles(skills: dict, primary_domain: str, secondary_domain: str, seniority: str) -> list:
    """
    Generates AI job titles based on the extracted skills and domains.
    """
    titles = set()
    
    # Base titles based on domains
    domain_titles = {
        'Frontend': ['Frontend Developer', 'UI Engineer', 'Frontend Engineer', 'Web Developer', 'React Developer', 'Angular Developer', 'Vue Developer'],
        'Backend': ['Backend Developer', 'Backend Engineer', 'Server-side Engineer', 'API Developer', 'Python Developer', 'Java Developer', 'Node.js Developer', 'Go Developer'],
        'Data Science & AI': ['Data Scientist', 'AI Engineer', 'Machine Learning Engineer', 'ML Engineer', 'Data Engineer', 'NLP Engineer', 'Deep Learning Engineer', 'Computer Vision Engineer', 'Artificial Intelligence Engineer'],
        'Cloud & DevOps': ['DevOps Engineer', 'Cloud Engineer', 'Site Reliability Engineer', 'SRE', 'Platform Engineer', 'AWS Engineer', 'Cloud Solutions Architect'],
        'Mobile': ['Mobile Developer', 'iOS Developer', 'Android Developer', 'Mobile App Engineer', 'Flutter Developer', 'React Native Developer'],
        'General Software Engineering': ['Software Engineer', 'Software Developer', 'Full Stack Developer', 'Full Stack Engineer']
    }
    
    # 1. Add general domain titles
    if primary_domain in domain_titles:
        titles.update(domain_titles[primary_domain][:4])
        
    if secondary_domain and secondary_domain in domain_titles:
        titles.update(domain_titles[secondary_domain][:2])

    # 2. Add specific skill-based titles
    all_tech = []
    for k in ['programming_languages', 'frameworks', 'libraries', 'cloud', 'databases']:
        all_tech.extend([s.lower() for s in skills.get(k, [])])
        
    if 'python' in all_tech:
        titles.add('Python Developer')
        titles.add('Python Engineer')
        if 'opencv' in all_tech or 'yolo' in all_tech:
            titles.add('Computer Vision Engineer')
            titles.add('AI Engineer')
        if 'tensorflow' in all_tech or 'pytorch' in all_tech or 'keras' in all_tech:
            titles.add('Machine Learning Engineer')
            titles.add('Deep Learning Engineer')
            
    if 'react' in all_tech or 'next.js' in all_tech:
        titles.add('React Developer')
        titles.add('Frontend Engineer')
        
    if 'node.js' in all_tech or 'express' in all_tech:
        titles.add('Node.js Developer')
        titles.add('Backend Engineer')
        
    if ('react' in all_tech or 'angular' in all_tech) and ('node.js' in all_tech or 'python' in all_tech or 'java' in all_tech):
        titles.add('Full Stack Developer')
        titles.add('Full Stack Engineer')

    # 3. Apply Seniority Prefix
    final_titles = []
    prefix = ""
    if seniority in ["Senior", "Lead"]:
        prefix = seniority + " "
    elif seniority == "Fresher":
        prefix = "Junior "

    for t in list(titles)[:10]:
        final_titles.append(f"{prefix}{t}".strip())
        # Also add the raw title without prefix for broader search
        if prefix and t not in final_titles:
            final_titles.append(t)
            
    return list(set(final_titles))[:15]
