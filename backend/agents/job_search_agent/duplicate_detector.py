from typing import Dict, Any, List
from utilities.helpers import generate_job_hash
from cache import job_cache

class DuplicateDetector:
    @staticmethod
    async def filter_duplicates(normalized_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters out jobs that are already in the cache (have been processed recently) 
        or are duplicates within the same batch.
        """
        unique_jobs = []
        seen_hashes = set()
        
        for job in normalized_jobs:
            job_hash = generate_job_hash(job['company'], job['title'], job['location'])
            
            # Check if duplicate in current batch
            if job_hash in seen_hashes:
                continue
                
            # Check if duplicate globally across sessions
            is_dup = await job_cache.is_processed(job_hash)
            if not is_dup:
                seen_hashes.add(job_hash)
                # Keep a reference to the hash for later caching when saved to DB
                job['job_hash'] = job_hash 
                unique_jobs.append(job)
                
        return unique_jobs
