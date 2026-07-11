from skill_extractor import analyze_resume_text
from keyword_generator import generate_keywords
from job_titles_generator import generate_job_titles
from resume_summary import generate_resume_summary
from embedding_service import get_embedding
from vector_store import store_embedding_for_user
from db_integration import update_user_ai_profile

def process_resume(user_id: int, resume_text: str):
    """
    Orchestrates the entire AI resume intelligence pipeline.
    """
    print(f"Starting AI analysis for user {user_id}")
    
    # 1. Extract skills and metadata
    extraction_results = analyze_resume_text(resume_text)
    skills = extraction_results['technical_skills']
    exp_level = extraction_results['experience_level']
    seniority = extraction_results['seniority']
    primary_domain = extraction_results['primary_domain']
    secondary_domain = extraction_results['secondary_domain']
    
    # 2. Generate Keywords
    keywords = generate_keywords(skills, primary_domain, secondary_domain, seniority)
    
    # 3. Generate Job Titles
    job_titles = generate_job_titles(skills, primary_domain, secondary_domain, seniority)
    
    # 4. Generate AI Summary
    summary = generate_resume_summary(skills, primary_domain, exp_level, seniority)
    
    # 5. Create Embeddings
    # Embed the entire text or a summarized version for semantic matching
    text_to_embed = f"{summary} " + " ".join(keywords) + f" {resume_text[:1000]}"
    embedding = get_embedding(text_to_embed)
    
    # 6. Store in Vector Database (FAISS)
    store_embedding_for_user(user_id, embedding)
    
    # 7. Update MySQL Database
    db_success = update_user_ai_profile(user_id, summary, skills, keywords, job_titles)
    
    return {
        "success": db_success,
        "summary": summary,
        "skills": skills,
        "keywords": keywords,
        "job_titles": job_titles,
        "primary_domain": primary_domain,
        "experience_level": exp_level
    }
