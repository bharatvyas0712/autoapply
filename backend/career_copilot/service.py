from resume_optimizer import ResumeOptimizer
from ats_checker import ATSChecker
from linkedin_optimizer import LinkedInOptimizer
from mock_interviewer import MockInterviewer
from salary_predictor import SalaryPredictor
from skill_gap_analyzer import SkillGapAnalyzer
from career_path_planner import CareerPathPlanner
from repository import AsyncSessionLocal, OptimizedResume, InterviewSession, CareerRoadmap, SalaryPrediction, OfferComparison
from sqlalchemy.future import select
from typing import Dict, Any, List

class CareerCopilotService:
    @staticmethod
    async def optimize_resume(user_id: int, resume_text: str, keywords: List[str]) -> Dict[str, Any]:
        res = ResumeOptimizer.optimize(resume_text, keywords)
        
        async with AsyncSessionLocal() as db:
            opt = OptimizedResume(
                user_id=user_id,
                original_resume_path="resume.pdf",
                optimized_resume_path="resume_optimized.pdf",
                suggestions=res["suggestions"]
            )
            db.add(opt)
            await db.commit()
            
        return res

    @staticmethod
    def get_ats_score(resume_text: str, job_description: str) -> Dict[str, Any]:
        return ATSChecker.check_score(resume_text, job_description)

    @staticmethod
    def optimize_linkedin(skills: list, target_role: str) -> Dict[str, Any]:
        return LinkedInOptimizer.optimize_profile(skills, target_role)

    @staticmethod
    async def start_mock_interview(user_id: int, interview_type: str) -> Dict[str, Any]:
        questions = MockInterviewer.generate_questions(interview_type)
        
        async with AsyncSessionLocal() as db:
            session = InterviewSession(
                user_id=user_id,
                interview_type=interview_type,
                questions=questions
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
        return {"session_id": session.id, "questions": questions}

    @staticmethod
    async def get_salary_prediction(user_id: int, role: str, location: str) -> Dict[str, Any]:
        res = SalaryPredictor.predict(role, location, 3)
        
        async with AsyncSessionLocal() as db:
            pred = SalaryPrediction(
                user_id=user_id,
                role=role,
                location=location,
                predicted_min=res["predicted_min"],
                predicted_max=res["predicted_max"]
            )
            db.add(pred)
            await db.commit()
            
        return res

    @staticmethod
    def get_skill_gap(current_skills: list, target_skills: list) -> Dict[str, Any]:
        return SkillGapAnalyzer.analyze(current_skills, target_skills)

    @staticmethod
    async def get_career_roadmap(user_id: int, current_role: str, target_role: str) -> Dict[str, Any]:
        res = CareerPathPlanner.generate_roadmaps(current_role, target_role)
        
        async with AsyncSessionLocal() as db:
            rm = CareerRoadmap(
                user_id=user_id,
                target_role=target_role,
                roadmap_6m=res["roadmap_6m"],
                roadmap_12m=res["roadmap_12m"],
                roadmap_24m=res["roadmap_24m"]
            )
            db.add(rm)
            await db.commit()
            
        return res
