from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from repository import AsyncSessionLocal, JobMatch, SkillGap, MatchHistory
from embedding_service import get_embedding, get_embeddings_batch
from matcher import evaluate_job_match
from utilities.logger import get_logger

logger = get_logger("MatchingAgent")

class JobMatchingAgent:
    @staticmethod
    async def process_jobs_batch(user_id: int, user_profile: Dict[str, Any], jobs: List[Dict[str, Any]]):
        """Processes a batch of jobs for a user asynchronously."""
        logger.info(f"Running semantic matching for user {user_id} on {len(jobs)} jobs.")
        
        # Build resume embedding
        resume_text = str(user_profile.get('summary', '')) + " " + " ".join(user_profile.get('ai_keywords', []))
        resume_emb = get_embedding(resume_text)
        
        # Batch embed jobs
        job_texts = [j.get('description', '')[:2000] for j in jobs]
        job_embs = get_embeddings_batch(job_texts)
        
        # We need a DB session to save results
        async with AsyncSessionLocal() as db:
            history = MatchHistory(user_id=user_id, total_processed=len(jobs))
            db.add(history)
            await db.flush()
            
            auto = 0
            rev = 0
            skip = 0
            
            for idx, job in enumerate(jobs):
                result = evaluate_job_match(job, user_profile, job_embs[idx], resume_emb)
                
                # Update counters
                dec = result['decision']
                if dec == "AUTO_APPLY": auto += 1
                elif dec == "REVIEW_REQUIRED": rev += 1
                else: skip += 1
                
                # Save JobMatch
                match_record = JobMatch(
                    user_id=user_id,
                    job_id=job.get('id'), # Assumes job has an id from job_search_history
                    semantic_score=result['scores']['semantic_score'],
                    skill_score=result['scores']['skill_score'],
                    experience_score=result['scores']['experience_score'],
                    education_score=result['scores']['education_score'],
                    location_score=result['scores']['location_score'],
                    salary_score=result['scores']['salary_score'],
                    overall_score=result['overall_score'],
                    confidence=result['confidence'],
                    decision=dec,
                    reason=result['reason'],
                    llm_analysis=result['llm_analysis']
                )
                db.add(match_record)
                await db.flush()
                
                # Save SkillGap
                sg = result['skill_gap']
                skill_record = SkillGap(
                    match_id=match_record.id,
                    matched_skills=sg['matched_skills'],
                    missing_skills=sg['missing_skills'],
                    nice_to_have_skills=sg['nice_to_have_skills'],
                    critical_missing_skills=sg['critical_missing_skills']
                )
                db.add(skill_record)
                
            history.auto_apply_count = auto
            history.review_count = rev
            history.skip_count = skip
            import datetime
            history.completed_at = datetime.datetime.utcnow()
            
            await db.commit()
            logger.info(f"Completed match run. Auto: {auto}, Review: {rev}, Skip: {skip}")
            return {"success": True, "total": len(jobs), "auto_apply": auto, "review": rev, "skip": skip}
