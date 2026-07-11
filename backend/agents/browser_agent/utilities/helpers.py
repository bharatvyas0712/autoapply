import os
import time
import uuid

def generate_session_id() -> str:
    return str(uuid.uuid4())[:12]

def generate_screenshot_filename(job_id: int, stage: str) -> str:
    ts = int(time.time())
    return f"job_{job_id}_{stage}_{ts}.png"

def sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in name)
