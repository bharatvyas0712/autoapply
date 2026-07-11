import hashlib

def generate_job_hash(company: str, title: str, location: str) -> str:
    """
    Generates a unique hash for a job based on its core properties to prevent duplicates.
    """
    raw_str = f"{str(company).lower().strip()}|{str(title).lower().strip()}|{str(location).lower().strip()}"
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest()

def clean_text(text: str) -> str:
    """
    Cleans up whitespace from scraped text.
    """
    if not text:
        return ""
    return " ".join(text.split())
