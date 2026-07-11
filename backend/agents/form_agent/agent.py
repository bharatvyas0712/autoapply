from typing import List, Dict, Any
from form_detector import FormDetector
from field_classifier import FieldClassifier
from field_mapper import FieldMapper
from answer_generator import AnswerGenerator
from validation_engine import ValidationEngine
from confidence_engine import ConfidenceEngine
from review_queue import ReviewQueue
from file_upload_handler import FileUploadHandler
from utilities.logger import get_logger

logger = get_logger("FormAgent")

class FormFillingAgent:
    """
    Core orchestrator that runs form analysis, mapping, and filling decisions.
    """
    
    @staticmethod
    async def analyze_and_generate(
        user_id: int,
        job_id: int,
        dom_structure: List[Dict[str, Any]],
        profile: Dict[str, Any],
        job_details: Dict[str, Any],
        resume_path: str,
        cover_letter_path: str = ""
    ) -> Dict[str, Any]:
        
        # 1. Detect Fields
        fields = FormDetector.detect_fields_from_dom(dom_structure)
        logger.info(f"Form Agent detected {len(fields)} fields.")
        
        filled_values = {}
        review_required = []
        validation_fields = []
        
        for field in fields:
            label = field["label"]
            name = field["name"]
            field_type = field["type"]
            required = field["required"]
            
            # Skip file inputs for text-filling mapping
            if field_type == "file":
                continue
                
            # 2. Classify Field
            category = FieldClassifier.classify(label, name)
            
            if category == "Personal Information" or category == "Salary":
                # Static profile map
                val = FieldMapper.map_field_to_profile(label, name, profile)
                if val is not None:
                    filled_values[name] = val
                    validation_fields.append({"name": name, "value": val, "type": field_type, "required": required})
                elif required:
                    # If required but profile value missing, queue for review
                    review_id = await ReviewQueue.add_to_queue(user_id, job_id, f"Fill missing: {label}", "", 0.0)
                    review_required.append({"review_id": review_id, "field": name, "label": label})
                    
            elif category == "Behavioral Questions" or category == "Work Experience":
                # Generate semantic text answer
                ans_data = AnswerGenerator.generate_answer(label, profile, job_details)
                ans = ans_data["answer"]
                conf = ans_data["confidence"]
                
                # Check confidence
                is_confident = ConfidenceEngine.check_confidence(conf)
                if is_confident:
                    filled_values[name] = ans
                    validation_fields.append({"name": name, "value": ans, "type": field_type, "required": required})
                else:
                    review_id = await ReviewQueue.add_to_queue(user_id, job_id, label, ans, conf)
                    review_required.append({"review_id": review_id, "field": name, "label": label, "proposed": ans})
        
        # 3. File Upload mappings
        file_fields = [f for f in fields if f["type"] == "file"]
        file_uploads = FileUploadHandler.map_file_inputs(file_fields, resume_path, cover_letter_path)
        
        # 4. Validation Check on filled values
        val_result = ValidationEngine.validate_answers(validation_fields)
        
        return {
            "success": val_result["is_valid"],
            "filled_fields": filled_values,
            "file_uploads": file_uploads,
            "validation_errors": val_result["errors"],
            "review_queue_items": review_required
        }
