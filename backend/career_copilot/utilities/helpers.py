def check_keyword_match(text: str, keywords: list) -> float:
    if not text or not keywords:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    return (matches / len(keywords)) * 100
