import json
import re
from typing import Any


def clean_markdown_json(content: str) -> dict[str, Any] | None:
    try:
        cleaned = re.sub(r"```json|```", "", content).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
