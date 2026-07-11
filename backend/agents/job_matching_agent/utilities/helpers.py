import json

def parse_json_safely(data):
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return data
    if not data:
        return {}
    try:
        return json.loads(data)
    except:
        return {}
