from repository import (
    AsyncSessionLocal,
    LearningStatistics,
    ApplicationOutcome,
    CompanyHistory,
    ResumeVersion,
    Memory,
)
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Dict, Any, List

import groq_client


class LearningEngine:
    """
    Evaluates historical data, success rates, rejections, and compiles
    personalized tips (skills to acquire, target salary, companies to avoid).
    """

    @staticmethod
    async def process_feedback_hook(user_id: int, target_id: int, target_type: str, action: str):
        # Triggered when feedback is submitted. In practice, updates weights.
        pass

    @staticmethod
    async def calculate_statistics(user_id: int) -> Dict[str, Any]:
        stats = {}
        async with AsyncSessionLocal() as db:
            # 1. Total applications
            total = await db.execute(select(func.count(ApplicationOutcome.id)).where(ApplicationOutcome.user_id == user_id))
            stats["total_applications"] = total.scalar() or 0

            # 2. Total interviews
            interviews = await db.execute(select(func.count(ApplicationOutcome.id)).where(
                ApplicationOutcome.user_id == user_id,
                ApplicationOutcome.outcome == "interview"
            ))
            stats["total_interviews"] = interviews.scalar() or 0

            stats["interview_rate"] = (stats["total_interviews"] / stats["total_applications"] * 100) if stats["total_applications"] > 0 else 0.0

            # 3. Real counts for the dashboard (previously hardcoded on the frontend)
            memories_count = await db.execute(select(func.count(Memory.id)).where(Memory.user_id == user_id))
            stats["memories_count"] = memories_count.scalar() or 0

            companies_count = await db.execute(
                select(func.count(func.distinct(CompanyHistory.company_name))).where(CompanyHistory.user_id == user_id)
            )
            stats["companies_count"] = companies_count.scalar() or 0

            resumes_count = await db.execute(select(func.count(ResumeVersion.id)).where(ResumeVersion.user_id == user_id))
            stats["resumes_count"] = resumes_count.scalar() or 0

        return stats

    @staticmethod
    async def generate_recommendations(user_id: int) -> List[str]:
        """Builds personalized recommendations grounded in the user's actual
        application outcomes, company history, and resume version performance,
        using Groq to synthesize them into plain-English tips. Falls back to
        generic starter guidance only if there isn't enough data yet, or if
        the LLM call fails."""
        async with AsyncSessionLocal() as db:
            outcomes_res = await db.execute(
                select(ApplicationOutcome).where(ApplicationOutcome.user_id == user_id)
            )
            outcomes = outcomes_res.scalars().all()

            companies_res = await db.execute(
                select(CompanyHistory).where(CompanyHistory.user_id == user_id)
            )
            companies = companies_res.scalars().all()

            resumes_res = await db.execute(
                select(ResumeVersion).where(ResumeVersion.user_id == user_id)
            )
            resumes = resumes_res.scalars().all()

        if not outcomes and not companies and not resumes:
            return [
                "Apply to a few jobs and log outcomes to start getting personalized recommendations here.",
                "Upload at least one resume version so we can track what's working.",
            ]

        outcomes_summary = "\n".join(
            f"- {o.job_title or 'Unknown role'} at {o.company_name or 'Unknown company'}: "
            f"{o.outcome}" + (f", offered {o.salary_offered}" if o.salary_offered else "")
            for o in outcomes
        ) or "No application outcomes logged yet."

        companies_summary = "\n".join(
            f"- {c.company_name}: {c.previous_applications_count} application(s), last status: {c.last_status}"
            for c in companies
        ) or "No company history logged yet."

        resumes_summary = "\n".join(
            f"- {r.version_label}: {r.applications_count} applications, {r.interviews_count} interviews, "
            f"skills added: {r.skills_added or []}"
            for r in resumes
        ) or "No resume versions logged yet."

        prompt = f"""You are a career coach analyzing a job seeker's real application data to give them \
specific, actionable recommendations.

Application outcomes:
{outcomes_summary}

Company interaction history:
{companies_summary}

Resume version performance:
{resumes_summary}

Based ONLY on this real data (don't invent companies or facts not present above), generate 3-5 short, \
specific, actionable recommendations. Cover things like: skills/keywords to add, which resume version is \
performing best and why, companies or role types to prioritize or avoid based on their actual outcomes, \
and salary expectations if salary data is present. If data is too sparse for a given angle, skip it rather \
than making something up.

Respond with ONLY a JSON array of strings (no markdown fences):
["...", "..."]"""

        result = groq_client.generate_json(prompt)
        if isinstance(result, list) and all(isinstance(r, str) for r in result) and result:
            return result

        # Fallback: a simple deterministic summary if the LLM is unavailable
        fallback = []
        if resumes:
            best = max(resumes, key=lambda r: r.interviews_count)
            fallback.append(
                f"'{best.version_label}' is your best-performing resume so far "
                f"({best.interviews_count} interviews from {best.applications_count} applications) - "
                f"consider using it as your default."
            )
        rejected = [c.company_name for c in companies if c.last_status == "rejected"]
        if rejected:
            fallback.append(f"Review your approach for: {', '.join(rejected[:3])} - previous applications there were rejected.")
        if not fallback:
            fallback.append("Keep logging applications and outcomes - recommendations will get sharper with more data.")
        return fallback