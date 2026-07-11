import re

# Comprehensive skill dictionaries for rule-based extraction
KNOWLEDGE_BASE = {
    'programming_languages': [
        'python', 'java', 'javascript', 'c++', 'c#', 'c', 'ruby', 'go', 'php', 'swift', 'kotlin', 'typescript', 'rust', 'scala', 'dart', 'r'
    ],
    'frameworks': [
        'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'node.js', 'springboot', 'ruby on rails', 'laravel', 'next.js', 'nuxt.js', 'fastapi'
    ],
    'libraries': [
        'opencv', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'keras', 'pytorch', 'matplotlib', 'seaborn', 'nltk', 'spacy', 'beautifulsoup', 'selenium', 'playwright', 'requests'
    ],
    'cloud': [
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'heroku', 'terraform', 'ansible', 'jenkins', 'circleci', 'github actions', 'gitlab ci'
    ],
    'databases': [
        'mysql', 'postgresql', 'mongodb', 'sqlite', 'redis', 'oracle', 'sql server', 'cassandra', 'dynamodb', 'elasticsearch', 'neo4j', 'firebase', 'supabase'
    ],
    'soft_skills': [
        'leadership', 'communication', 'teamwork', 'problem solving', 'agile', 'scrum', 'time management', 'critical thinking', 'project management', 'collaboration', 'adaptability'
    ]
}

def extract_skills_from_text(text: str) -> dict:
    """Extracts various categories of skills from resume text using regex word matching."""
    text_lower = text.lower()
    extracted = {
        'programming_languages': [],
        'frameworks': [],
        'libraries': [],
        'cloud': [],
        'databases': [],
        'soft_skills': [],
        'top_skills': []
    }
    
    all_tech_skills = []
    
    for category, skills in KNOWLEDGE_BASE.items():
        for skill in skills:
            # Word boundary regex to ensure exact matches
            pattern = rf'\b{re.escape(skill)}\b'
            if skill == 'c++':
                pattern = r'\bc\+\+\b'
            elif skill == 'c#':
                pattern = r'\bc#\b'
            
            if re.search(pattern, text_lower):
                capitalized_skill = skill.title() if skill not in ['php', 'aws', 'gcp', 'sql', 'mysql', 'postgresql'] else skill.upper()
                if skill == 'node.js': capitalized_skill = 'Node.js'
                if skill == 'next.js': capitalized_skill = 'Next.js'
                if skill == 'react': capitalized_skill = 'React'
                if skill == 'javascript': capitalized_skill = 'JavaScript'
                
                extracted[category].append(capitalized_skill)
                if category != 'soft_skills':
                    all_tech_skills.append(capitalized_skill)
    
    # Simple top skills - just take the first 5 technical skills found
    extracted['top_skills'] = list(set(all_tech_skills))[:8]
    return extracted

def extract_experience_level(text: str):
    """Determines experience level and seniority based on years of experience mentioned."""
    text_lower = text.lower()
    
    # Try to find "X years of experience"
    years_patterns = [
        r'(\d+)(?:\+|-)?\s*(?:years|yrs)\s*(?:of)?\s*experience',
        r'experience.*?(?:of)?\s*(\d+)(?:\+|-)?\s*(?:years|yrs)'
    ]
    
    max_years = 0
    for pattern in years_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            max_years = max(max_years, max([int(y) for y in matches]))
            
    if max_years > 0:
        if max_years < 2:
            return "Entry Level", "Fresher"
        elif 2 <= max_years < 5:
            return "Mid Level", "Junior/Mid"
        elif 5 <= max_years < 8:
            return "Senior Level", "Senior"
        else:
            return "Executive/Lead", "Lead"
            
    # Fallback to keywords
    if "lead" in text_lower or "principal" in text_lower or "manager" in text_lower:
         return "Senior Level", "Lead"
    elif "senior" in text_lower or "sr." in text_lower:
         return "Senior Level", "Senior"
    elif "intern" in text_lower or "fresher" in text_lower or "entry level" in text_lower:
         return "Entry Level", "Fresher"
    else:
         # Default
         return "Mid Level", "Mid"

def extract_domains(tech_skills: list):
    """Determines primary and secondary domains based on extracted tech skills."""
    domain_scores = {
        'Frontend': ['React', 'Angular', 'Vue', 'JavaScript', 'TypeScript', 'Next.js'],
        'Backend': ['Python', 'Java', 'Node.js', 'Django', 'Flask', 'Spring', 'Express', 'MySQL', 'PostgreSQL'],
        'Data Science & AI': ['Python', 'Pandas', 'Numpy', 'Scikit-Learn', 'Tensorflow', 'Keras', 'Pytorch', 'Opencv'],
        'Cloud & DevOps': ['Aws', 'Azure', 'Gcp', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform'],
        'Mobile': ['Swift', 'Kotlin', 'Dart', 'React Native', 'Flutter']
    }
    
    scores = {domain: 0 for domain in domain_scores}
    for skill in tech_skills:
        for domain, d_skills in domain_scores.items():
            if skill in d_skills or skill.upper() in [s.upper() for s in d_skills]:
                scores[domain] += 1
                
    # Sort domains by score
    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    primary = sorted_domains[0][0] if sorted_domains[0][1] > 0 else "General Software Engineering"
    secondary = sorted_domains[1][0] if len(sorted_domains) > 1 and sorted_domains[1][1] > 0 else None
    
    return primary, secondary

def analyze_resume_text(text: str):
    """Main orchestration for extracting skills, levels, and domains from text."""
    skills = extract_skills_from_text(text)
    exp_level, seniority = extract_experience_level(text)
    
    all_tech = []
    for k in ['programming_languages', 'frameworks', 'libraries', 'cloud', 'databases']:
        all_tech.extend(skills[k])
        
    primary_domain, secondary_domain = extract_domains(all_tech)
    
    return {
        "technical_skills": skills,
        "experience_level": exp_level,
        "seniority": seniority,
        "primary_domain": primary_domain,
        "secondary_domain": secondary_domain
    }
