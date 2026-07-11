from typing import List, Dict, Any

class JobFilters:
    @staticmethod
    def apply_filters(jobs: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Applies strict configuration filters to the search results.
        """
        filtered_jobs = []
        
        req_remote = filters.get("remote_only")
        min_score = filters.get("min_match_score", 0)
        
        for job in jobs:
            # Match Score Filter
            if job.get('match_score', 0) < min_score:
                continue
                
            # Remote Filter
            if req_remote and not job.get('is_remote'):
                continue
                
            filtered_jobs.append(job)
            
        return filtered_jobs
