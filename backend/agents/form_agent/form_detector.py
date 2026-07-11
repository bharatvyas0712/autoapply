from typing import List, Dict, Any

class FormDetector:
    """
    Scans and extracts input elements and forms from raw DOM structures or page analyses.
    Designed to interface with the browser automation outputs.
    """
    
    @staticmethod
    def detect_fields_from_dom(dom_structure: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses DOM tags to locate form controls (input, select, textarea, file upload).
        """
        detected = []
        for element in dom_structure:
            tag_name = element.get("tag", "").lower()
            if tag_name in ["input", "select", "textarea"]:
                el_type = element.get("type", "").lower() or tag_name
                name = element.get("name", "")
                placeholder = element.get("placeholder", "")
                label = element.get("label", "") or placeholder or name
                
                detected.append({
                    "id": element.get("id"),
                    "tag": tag_name,
                    "type": el_type,
                    "name": name,
                    "label": label,
                    "required": element.get("required", False),
                    "options": element.get("options", [])  # for dropdown selects
                })
        return detected
