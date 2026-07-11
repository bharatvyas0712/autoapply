import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import settings
from utilities.logger import get_logger
from agent import JobSearchAgent

logger = get_logger("Scheduler")

class SearchScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # We will schedule the search task to run every X minutes
        # Since user profiles are dynamic, this normally would fetch active users from the DB
        # and queue their searches. For now, we will add a static hook.
        
        self.scheduler.add_job(
            self.run_scheduled_searches,
            'interval',
            minutes=settings.SEARCH_INTERVAL_MINUTES,
            id='background_search_job'
        )
        self.scheduler.start()
        logger.info(f"Started search scheduler. Interval: {settings.SEARCH_INTERVAL_MINUTES}m")
        
    def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped.")

    async def run_scheduled_searches(self):
        logger.info("Executing scheduled batch searches...")
        # Mocking getting active users. In production: fetch users from DB with active subscriptions/flags
        
        # Example user profile mock matching AI output
        mock_user = {
            "user_id": 1,
            "ai_job_titles": ["Software Engineer", "Backend Engineer"],
            "ai_keywords": ["Python", "FastAPI", "SQLAlchemy"],
            "primary_domain": "Backend",
            "job_type_pref": "remote"
        }
        
        await JobSearchAgent.run_search_for_user(mock_user)

# Global instance
job_scheduler = SearchScheduler()
