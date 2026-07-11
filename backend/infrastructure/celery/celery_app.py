# Celery setup module for running asynchronous long running jobs
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "autojobapply_workers",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True
)

@celery_app.task
def background_job_search(user_id: int):
    # Runs async search
    print(f"Triggered background job search for user {user_id}")
    return {"status": "success", "jobs_found": 15}

@celery_app.task
def background_resume_parse(resume_path: str):
    print(f"Parsing resume path: {resume_path}")
    return {"status": "success", "skills": ["Python"]}
