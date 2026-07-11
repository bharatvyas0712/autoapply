from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BasePlatform(ABC):
    """
    Abstract base class for all job search platform scrapers.
    """
    def __init__(self):
        self.platform_name = self.__class__.__name__
        self.session = None

    @abstractmethod
    async def search_jobs(self, keywords: List[str], location: str, pages: int = 1) -> List[Dict[str, Any]]:
        """
        Executes a search and returns a list of raw jobs.
        """
        pass

    @abstractmethod
    def extract_job(self, html_or_json: Any) -> Dict[str, Any]:
        """
        Extracts raw job fields from an HTML node or JSON response.
        """
        pass

    @abstractmethod
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes a raw job to the common schema using normalizer.py.
        """
        pass

    @abstractmethod
    async def next_page(self) -> bool:
        """
        Navigates to the next page of results. Returns True if successful.
        """
        pass

    async def close(self):
        """
        Cleans up resources (e.g., closing aiohttp session or playwright context).
        """
        if self.session:
            await self.session.close()
