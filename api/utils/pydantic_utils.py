# ────────────────────────────────────────────────
# Pydantic Utils
# ────────────────────────────────────────────────
def to_camel_case(string: str) -> str:
    parts = string.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])

def to_snake_case(string: str) -> str:
    return ''.join(['_' + i.lower() if i.isupper() else i for i in string]).lstrip('_')