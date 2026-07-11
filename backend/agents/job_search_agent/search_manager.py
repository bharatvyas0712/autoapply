import asyncio
from typing import List, Dict, Any
from config import settings
from utilities.logger import get_logger
from duplicate_detector import DuplicateDetector
from ranking import RankingEngine
from filters import JobFilters

logger = get_logger("SearchManager")

class SearchManager:
    def __init__(self):
        self._platforms = self._initialize_platforms()

    def _initialize_platforms(self):
        from platforms import (
            Indeed, Linkedin, Naukri, Wellfound, Greenhouse,
            Lever, Workday, Ashby, Dice, Monster, Glassdoor
        )
        platforms = []
        if settings.ENABLE_INDEED: platforms.append(Indeed())
        if settings.ENABLE_LINKEDIN: platforms.append(Linkedin())
        if settings.ENABLE_NAUKRI: platforms.append(Naukri())
        if settings.ENABLE_WELLFOUND: platforms.append(Wellfound())
        if settings.ENABLE_GREENHOUSE: platforms.append(Greenhouse())
        if settings.ENABLE_LEVER: platforms.append(Lever())
        if settings.ENABLE_WORKDAY: platforms.append(Workday())
        if settings.ENABLE_ASHBY: platforms.append(Ashby())
        if settings.ENABLE_DICE: platforms.append(Dice())
        if settings.ENABLE_MONSTER: platforms.append(Monster())
        if settings.ENABLE_GLASSDOOR: platforms.append(Glassdoor())
        
        logger.info(f"Initialized {len(platforms)} search platforms.")
        return platforms

    async def execute_search(self, user_profile: Dict[str, Any], search_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executes search across all enabled platforms concurrently.
        """
        if not search_filters:
            search_filters = {}

        # Determine keywords to use
        keywords = user_profile.get("ai_keywords", [])
        if not keywords:
            logger.warning("No keywords found in profile. Searching fallback.")
            keywords = ["Software Engineer"]
            
        location = search_filters.get("location", "Remote")
        
        # We search with the top 3 keywords to avoid hitting rate limits too hard
        search_keywords = keywords[:3]
        
        tasks = []
        # Create a semaphore to limit concurrent platform searches
        sem = asyncio.Semaphore(settings.MAX_CONCURRENT_SEARCHES)
        
        async def fetch_platform(platform):
            async with sem:
                try:
                    return await platform.search_jobs(search_keywords, location, pages=settings.MAX_PAGES_PER_SEARCH)
                except Exception as e:
                    logger.error(f"Error in {platform.platform_name}: {e}")
                    return []

        logger.info("Executing concurrent searches...")
        results = await asyncio.gather(*(fetch_platform(p) for p in self._platforms))
        
        # Flatten results
        all_jobs = [job for result in results for job in result]
        logger.info(f"Found {len(all_jobs)} total raw jobs.")
        
        # 1. Deduplicate
        unique_jobs = await DuplicateDetector.filter_duplicates(all_jobs)
        logger.info(f"After deduplication: {len(unique_jobs)} jobs.")
        
        # 2. Rank
        ranked_jobs = RankingEngine.rank_jobs(unique_jobs, user_profile)
        
        # 3. Apply strict filters
        final_jobs = JobFilters.apply_filters(ranked_jobs, search_filters)
        logger.info(f"Final filtered jobs: {len(final_jobs)} jobs.")
        
        # Close platform sessions
        await self.close()
        
        return final_jobs
        
    async def close(self):
        for p in self._platforms:
            await p.close()
