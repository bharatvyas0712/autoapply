from utilities.helpers import is_valid_email, is_valid_url
from typing import Dict, Any, List

class ValidationEngine:
    """
    Validates form answers to prevent invalid entries before submitting applications.
    """
    
    @staticmethod
    def validate_answers(fields_to_validate: List[Dict[str, Any]]) -> Dict[str, Any]:
        errors = {}
        for field in fields_to_validate:
            name = field.get("name", "")
            value = str(field.get("value", "")).strip()
            field_type = field.get("type", "").lower()
            required = field.get("required", False)
            
            if required and not value:
                errors[name] = "This field is required."
                continue
                
            if value:
                if "email" in name.lower() or field_type == "email":
                    if not is_valid_email(value):
                        errors[name] = "Invalid email address format."
                elif any(u in name.lower() for u in ["linkedin", "github", "portfolio", "url", "website"]):
                    if not is_valid_url(value):
                        errors[name] = "Invalid URL link format."
                        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
