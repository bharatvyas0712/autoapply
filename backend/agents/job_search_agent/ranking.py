from typing import Dict, Any, List

class RankingEngine:
    @staticmethod
    def calculate_score(job: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """
        Calculates an AI relevance score (0-100) based on Resume AI profile and job description.
        Factors: Skills match, Title match, Remote preference.
        """
        score = 0.0
        
        # 1. Title Match (Max 30 points)
        ai_titles = user_profile.get("ai_job_titles", [])
        job_title = job.get("title", "").lower()
        title_matched = False
        for ai_title in ai_titles:
            if ai_title.lower() in job_title or job_title in ai_title.lower():
                score += 30.0
                title_matched = True
                break
        
        if not title_matched:
            # Partial match on domains
            primary = user_profile.get("primary_domain", "").lower()
            if primary in job_title:
                score += 15.0
                
        # 2. Skills Match (Max 50 points)
        # Search for AI extracted skills in the job description
        desc = job.get("description", "").lower()
        skills_extracted = user_profile.get("ai_extracted", {})
        
        all_skills = []
        for k in ['programming_languages', 'frameworks', 'libraries', 'cloud', 'databases']:
            all_skills.extend([s.lower() for s in skills_extracted.get(k, [])])
            
        if not all_skills:
            all_skills = [k.lower() for k in user_profile.get("ai_keywords", [])]
            
        matched_skills = 0
        total_skills_to_check = len(all_skills) if all_skills else 1
        
        for skill in all_skills:
            if skill in desc:
                matched_skills += 1
                
        skill_score = (matched_skills / total_skills_to_check) * 50.0 if total_skills_to_check > 0 else 0
        score += min(skill_score, 50.0)
        
        # 3. Preferences Match (Max 20 points)
        # Example: Remote preference
        job_type_pref = user_profile.get("job_type_pref", "remote")
        if "remote" in str(job_type_pref).lower() and job.get("is_remote"):
            score += 20.0
        elif "remote" not in str(job_type_pref).lower() and not job.get("is_remote"):
            score += 20.0
        else:
            score += 10.0 # partial points for not strictly contradicting
            
        return min(max(score, 0.0), 100.0)

    @staticmethod
    def rank_jobs(jobs: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        for job in jobs:
            job['match_score'] = RankingEngine.calculate_score(job, user_profile)
            
        # Sort descending by match score
        return sorted(jobs, key=lambda x: x['match_score'], reverse=True)
