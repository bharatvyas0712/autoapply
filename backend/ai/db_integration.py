import os
import json
import mysql.connector
from dotenv import load_dotenv

# Load env variables from backend/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'autojobapply')
    )

def update_user_ai_profile(user_id: int, summary: str, skills: dict, keywords: list, job_titles: list):
    """
    Updates the user_profiles table with the generated AI insights.
    Stores keywords and job_titles within the skills JSON.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if profile exists
        cursor.execute("SELECT id, skills FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        # Merge new AI data into skills JSON
        existing_skills = {}
        if profile and profile.get('skills'):
            if isinstance(profile['skills'], str):
                existing_skills = json.loads(profile['skills'])
            else:
                existing_skills = profile['skills']
                
        existing_skills['ai_extracted'] = skills
        existing_skills['ai_keywords'] = keywords
        existing_skills['ai_job_titles'] = job_titles
        
        skills_json = json.dumps(existing_skills)
        
        if profile:
            cursor.execute(
                "UPDATE user_profiles SET summary = %s, skills = %s WHERE user_id = %s",
                (summary, skills_json, user_id)
            )
        else:
            # Create a new profile if it doesn't exist
            cursor.execute(
                "INSERT INTO user_profiles (user_id, summary, skills) VALUES (%s, %s, %s)",
                (user_id, summary, skills_json)
            )
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating DB: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_ai_profile(user_id: int):
    """
    Retrieves the AI insights for a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT summary, skills FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        if not profile:
            return None
            
        skills_data = {}
        if profile.get('skills'):
            if isinstance(profile['skills'], str):
                skills_data = json.loads(profile['skills'])
            else:
                skills_data = profile['skills']
                
        return {
            "summary": profile.get('summary'),
            "ai_extracted": skills_data.get('ai_extracted', {}),
            "ai_keywords": skills_data.get('ai_keywords', []),
            "ai_job_titles": skills_data.get('ai_job_titles', [])
        }
    finally:
        cursor.close()
        conn.close()
