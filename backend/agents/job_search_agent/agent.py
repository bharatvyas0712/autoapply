import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from search_manager import SearchManager
from database import AsyncSessionLocal, SearchSession, PlatformSearchLog, JobSearchHistory
from cache import job_cache
from utilities.logger import get_logger

logger = get_logger("AgentCore")

class JobSearchAgent:
    @staticmethod
    async def run_search_for_user(user_profile: Dict[str, Any], search_filters: Dict[str, Any] = None):
        """
        Runs the full AI search pipeline for a given user and saves to DB.
        """
        user_id = user_profile.get("user_id")
        logger.info(f"Starting agent search for user {user_id}")
        
        async with AsyncSessionLocal() as db:
            # 1. Create a Search Session
            session_log = SearchSession(user_id=user_id)
            db.add(session_log)
            await db.commit()
            await db.refresh(session_log)
            
            try:
                # 2. Execute search
                manager = SearchManager()
                jobs = await manager.execute_search(user_profile, search_filters)
                
                # 3. Save to DB and Cache
                saved_count = 0
                for job in jobs:
                    # Save to cache to prevent duplicate across sessions
                    await job_cache.add_job(job['job_hash'])
                    
                    db_job = JobSearchHistory(
                        user_id=user_id,
                        job_hash=job['job_hash'],
                        title=job['title'],
                        company=job['company'],
                        location=job['location'],
                        platform=job['platform'],
                        job_url=job['job_url'],
                        description=job.get('description', '')[:2000], # Trucate just in case
                        salary=job.get('salary', ''),
                        employment_type=job.get('employment_type', ''),
                        is_remote=job.get('is_remote', False),
                        match_score=job.get('match_score', 0),
                        posted_date=job.get('posted_date', '')
                    )
                    db.add(db_job)
                    saved_count += 1
                    
                session_log.total_jobs_found = saved_count
                session_log.status = "completed"
                import datetime
                session_log.completed_at = datetime.datetime.utcnow()
                
                await db.commit()
                logger.info(f"Agent finished. Saved {saved_count} jobs.")
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                session_log.status = "failed"
                await db.commit()
                logger.error(f"Search failed for user {user_id}: {e}")

