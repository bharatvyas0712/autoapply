def generate_keywords(skills: dict, primary_domain: str, secondary_domain: str, seniority: str) -> list:
    """
    Generates 30+ search keywords based on extracted skills and domains.
    """
    keywords = set()
    
    # 1. Base Domain Keywords
    domain_map = {
        'Frontend': ['Frontend Developer', 'UI Engineer', 'Frontend Engineer', 'Web Developer'],
        'Backend': ['Backend Developer', 'Backend Engineer', 'Server-side Engineer', 'API Developer'],
        'Data Science & AI': ['Data Scientist', 'AI Engineer', 'Machine Learning Engineer', 'ML Engineer', 'Data Engineer', 'NLP Engineer', 'Deep Learning Engineer'],
        'Cloud & DevOps': ['DevOps Engineer', 'Cloud Engineer', 'Site Reliability Engineer', 'SRE', 'Platform Engineer'],
        'Mobile': ['Mobile Developer', 'iOS Developer', 'Android Developer', 'Mobile App Engineer'],
        'General Software Engineering': ['Software Engineer', 'Software Developer', 'Full Stack Developer', 'Programmer']
    }
    
    if primary_domain in domain_map:
        for title in domain_map[primary_domain]:
            keywords.add(title)
            if seniority != "Mid":
                keywords.add(f"{seniority} {title}")
                
    if secondary_domain and secondary_domain in domain_map:
        for title in domain_map[secondary_domain]:
            keywords.add(title)

    # 2. Skill-based Keywords
    all_tech = []
    for k in ['programming_languages', 'frameworks', 'libraries', 'cloud', 'databases']:
        all_tech.extend(skills.get(k, []))
        
    for skill in all_tech:
        # Add the raw skill
        keywords.add(skill)
        
        # Combinations
        if skill.lower() in ['python', 'java', 'c++', 'ruby', 'go', 'php', 'javascript']:
            keywords.add(f"{skill} Developer")
            keywords.add(f"{skill} Engineer")
            keywords.add(f"Backend {skill}")
            
        if skill.lower() in ['react', 'angular', 'vue']:
            keywords.add(f"{skill} Developer")
            keywords.add(f"Frontend {skill}")
            
        if skill.lower() in ['aws', 'azure', 'gcp']:
            keywords.add(f"{skill} Cloud Engineer")
            keywords.add(f"{skill} DevOps")
            
        if skill.lower() in ['tensorflow', 'pytorch', 'scikit-learn']:
            keywords.add("Machine Learning")
            keywords.add("Deep Learning")
            keywords.add("Generative AI")
            keywords.add("LLM Engineer")

    # 3. Add generic variations if short on keywords
    generic = ["Software Engineering", "Tech Lead", "System Design", "Agile", "REST API", "Microservices"]
    if len(keywords) < 30:
        for g in generic:
            keywords.add(g)
            
    # Convert to list and limit to around 35 for relevance
    return list(keywords)[:35]
