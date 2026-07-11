import json

def parse_json_safely(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {}
