from typing import List, Dict, Any
from .base_platform import BasePlatform
from normalizer import JobNormalizer
import aiohttp
from utilities.logger import get_logger

logger = get_logger("GlassdoorPlatform")

class Glassdoor(BasePlatform):
    def __init__(self):
        super().__init__()
        self.session = None

    async def search_jobs(self, keywords: List[str], location: str, pages: int = 1) -> List[Dict[str, Any]]:
        query = " ".join(keywords)
        logger.info(f"Searching Glassdoor for: {query} in {location}")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        jobs = []
        for page in range(pages):
            extracted = self.extract_job({
                "title": f"Software Engineer (Simulated Glassdoor {page})",
                "company": "Mock Glassdoor Company",
                "location": location,
                "job_url": f"https://glassdoor.com/jobs/123",
                "description": f"Looking for {query}.",
                "is_remote": True
            })
            jobs.append(self.normalize_job(extracted))
        return jobs

    def extract_job(self, data: Any) -> Dict[str, Any]:
        return data

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return JobNormalizer.normalize(raw_job, self.platform_name)

    async def next_page(self) -> bool:
        return True
