from repository import AsyncSessionLocal, ResumeVersion
from sqlalchemy.future import select
from typing import Dict, Any, List

class ResumeMemory:
    """Tracks multiple resume versions and details performance logs (interviews per application count)."""
    
    @staticmethod
    async def register_version(user_id: int, label: str, path: str, skills: List[str], projects: List[str]):
        async with AsyncSessionLocal() as db:
            rv = ResumeVersion(
                user_id=user_id,
                version_label=label,
                file_path=path,
                skills_added=skills,
                projects_added=projects
            )
            db.add(rv)
            await db.commit()

    @staticmethod
    async def increment_applications(version_id: int):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ResumeVersion).where(ResumeVersion.id == version_id))
            rv = result.scalars().first()
            if rv:
                rv.applications_count += 1
                await db.commit()

    @staticmethod
    async def increment_interviews(version_id: int):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ResumeVersion).where(ResumeVersion.id == version_id))
            rv = result.scalars().first()
            if rv:
                rv.interviews_count += 1
                await db.commit()
                
    @staticmethod
    async def get_versions(user_id: int) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ResumeVersion).where(ResumeVersion.user_id == user_id))
            return [r.to_dict() for r in result.scalars().all()]
