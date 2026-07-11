from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy import desc
from repository import AsyncSessionLocal, BrowserSession, BrowserLog, ApplicationExecution, Screenshot, BrowserError
from agent import BrowserAgent
from state_manager import state_manager
from browser_manager import browser_manager
from utilities.logger import get_logger
import datetime

logger = get_logger("BrowserService")

class BrowserService:
    @staticmethod
    async def start_session(user_id: int, browser_type: str = "chromium") -> str:
        """Starts a persistent browser session."""
        from session_manager import session_manager
        session_id = await session_manager.create_session(user_id)
        
        async with AsyncSessionLocal() as db:
            db_sess = BrowserSession(
                user_id=user_id,
                session_id=session_id,
                browser_type=browser_type,
                status="running"
            )
            db.add(db_sess)
            await db.commit()
            
        return session_id

    @staticmethod
    async def stop_session(session_id: str):
        """Stops an active browser session."""
        from session_manager import session_manager
        await session_manager.close_session(session_id)
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(BrowserSession).where(BrowserSession.session_id == session_id))
            db_sess = result.scalars().first()
            if db_sess:
                db_sess.status = "stopped"
                db_sess.stopped_at = datetime.datetime.utcnow()
                await db.commit()
        
        # Shut down browser manager if no active sessions are running
        if not session_manager.active_sessions:
            await browser_manager.close()

    @staticmethod
    async def apply_to_job(
        user_id: int,
        session_id: str,
        job_id: int,
        job_url: str,
        form_data: Dict[str, Any],
        resume_path: str,
        cover_letter_path: str = ""
    ) -> Dict[str, Any]:
        """Runs the browser automation flow for a job and logs to DB."""
        
        async with AsyncSessionLocal() as db:
            execution = ApplicationExecution(
                user_id=user_id,
                job_id=job_id,
                session_id=session_id,
                job_url=job_url,
                status="running"
            )
            db.add(execution)
            await db.commit()
            await db.refresh(execution)
            execution_id = execution.id

        # Run the automation agent
        result = await BrowserAgent.apply_to_job(
            job_id=job_id,
            job_url=job_url,
            form_data=form_data,
            resume_path=resume_path,
            cover_letter_path=cover_letter_path
        )
        
        # Update database with results
        async with AsyncSessionLocal() as db:
            res_exec = await db.execute(select(ApplicationExecution).where(ApplicationExecution.id == execution_id))
            db_exec = res_exec.scalars().first()
            if db_exec:
                db_exec.status = result.get("status", "failed")
                db_exec.current_step = result.get("current_step", "end")
                db_exec.completed_steps = result.get("completed_steps", [])
                db_exec.pending_steps = result.get("pending_steps", [])
                db_exec.retry_count = result.get("retry_count", 0)
                db_exec.completed_at = datetime.datetime.utcnow()
                
                # Check for errors
                errors = result.get("errors", [])
                if errors:
                    db_exec.error_message = "\n".join(errors)
                    db_error = BrowserError(
                        execution_id=execution_id,
                        error_type="ExecutionError",
                        message=db_exec.error_message
                    )
                    db.add(db_error)
                
                await db.commit()
                
        return result

    @staticmethod
    async def get_logs(session_id: str, limit: int = 100) -> List[BrowserLog]:
        async with AsyncSessionLocal() as db:
            stmt = select(BrowserLog).where(BrowserLog.session_id == session_id).order_by(desc(BrowserLog.timestamp)).limit(limit)
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]

    @staticmethod
    async def get_screenshots(execution_id: int) -> List[Screenshot]:
        async with AsyncSessionLocal() as db:
            stmt = select(Screenshot).where(Screenshot.execution_id == execution_id).order_by(desc(Screenshot.created_at))
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
