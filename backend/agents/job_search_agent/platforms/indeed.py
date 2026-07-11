from typing import List, Dict, Any
from .base_platform import BasePlatform
from normalizer import JobNormalizer
import aiohttp
from utilities.logger import get_logger

logger = get_logger("IndeedPlatform")

class Indeed(BasePlatform):
    def __init__(self):
        super().__init__()
        # In a real heavy scrape, this might use playwright.async_api
        # For simplicity and speed in this demo, using aiohttp with mocked endpoint logic
        self.session = None

    async def search_jobs(self, keywords: List[str], location: str, pages: int = 1) -> List[Dict[str, Any]]:
        query = " ".join(keywords)
        logger.info(f"Searching Indeed for: {query} in {location}")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        jobs = []
        for page in range(pages):
            # Mocking network request
            # response = await self.session.get(f"https://indeed.com/jobs?q={query}&l={location}&start={page*10}")
            
            # Simulated extracted data
            extracted = self.extract_job({
                "title": f"Software Engineer (Simulated Indeed {page})",
                "company": "Tech Corp",
                "location": location,
                "job_url": "https://indeed.com/viewjob?jk=123",
                "description": f"We are looking for someone with {query} skills.",
                "is_remote": True
            })
            
            jobs.append(self.normalize_job(extracted))
            
            has_next = await self.next_page()
            if not has_next:
                break
                
        return jobs

    def extract_job(self, html_or_json: Any) -> Dict[str, Any]:
        return html_or_json # In real implementation, parse BeautifulSoup or JSON

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return JobNormalizer.normalize(raw_job, self.platform_name)

    async def next_page(self) -> bool:
        # Mock pagination logic
        return True
