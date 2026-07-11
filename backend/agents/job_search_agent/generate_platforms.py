import os

platforms = ['linkedin', 'naukri', 'wellfound', 'greenhouse', 'lever', 'workday', 'ashby', 'dice', 'monster', 'glassdoor']
template = """from typing import List, Dict, Any
from .base_platform import BasePlatform
from normalizer import JobNormalizer
import aiohttp
from utilities.logger import get_logger

logger = get_logger("{class_name}Platform")

class {class_name}(BasePlatform):
    def __init__(self):
        super().__init__()
        self.session = None

    async def search_jobs(self, keywords: List[str], location: str, pages: int = 1) -> List[Dict[str, Any]]:
        query = " ".join(keywords)
        logger.info(f"Searching {class_name} for: {{query}} in {{location}}")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        jobs = []
        for page in range(pages):
            extracted = self.extract_job({{
                "title": f"Software Engineer (Simulated {class_name} {{page}})",
                "company": "Mock {class_name} Company",
                "location": location,
                "job_url": f"https://{name}.com/jobs/123",
                "description": f"Looking for {{query}}.",
                "is_remote": True
            }})
            jobs.append(self.normalize_job(extracted))
        return jobs

    def extract_job(self, data: Any) -> Dict[str, Any]:
        return data

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return JobNormalizer.normalize(raw_job, self.platform_name)

    async def next_page(self) -> bool:
        return True
"""

base_dir = r'c:\Users\bhara\OneDrive\Desktop\AutoJobApply\backend\agents\job_search_agent\platforms'
os.makedirs(base_dir, exist_ok=True)

# Also create __init__.py to expose platforms easily
init_lines = []

for name in platforms:
    class_name = name.capitalize()
    with open(os.path.join(base_dir, f'{name}.py'), 'w') as f:
        f.write(template.format(class_name=class_name, name=name))
    init_lines.append(f"from .{name} import {class_name}")

# Also add Indeed
init_lines.append("from .indeed import Indeed")

with open(os.path.join(base_dir, '__init__.py'), 'w') as f:
    f.write("\n".join(init_lines) + "\n")
