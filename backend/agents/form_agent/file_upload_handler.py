import os
from typing import List, Dict, Any

class FileUploadHandler:
    """
    Handles local file path mapping for resume, cover letters, and other documentation attachments.
    """
    
    @staticmethod
    def map_file_inputs(fields: List[Dict[str, Any]], resume_path: str, cover_letter_path: str = "") -> Dict[str, str]:
        """
        Maps file-upload input elements to target document paths.
        """
        mapping = {}
        for field in fields:
            name = field.get("name", "").lower()
            label = field.get("label", "").lower()
            
            # Simple matching heuristics
            if "resume" in name or "resume" in label or "cv" in name or "cv" in label:
                if os.path.exists(resume_path):
                    mapping[field.get("name")] = resume_path
            elif "cover" in name or "cover" in label or "letter" in name or "letter" in label:
                if cover_letter_path and os.path.exists(cover_letter_path):
                    mapping[field.get("name")] = cover_letter_path
                    
        return mapping
