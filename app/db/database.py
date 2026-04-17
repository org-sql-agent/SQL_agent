import re
import sqlite3

import pandas as pd

from app.core.service.config import DATABASE_PATH


def _validate_sql_query(sql_query: str) -> str | None:
    normalized = sql_query.strip()
    if not normalized:
        return "SQL 查詢不可為空。"

    # Block statement chaining to avoid multi-statement execution.
    if ";" in normalized:
        return "只允許單一 SELECT 查詢，禁止使用分號 (;)。"

    if not re.match(r"(?is)^select\b", normalized):
        return "只允許 SELECT 查詢。"

    blocked_keywords = (
        "drop",
        "delete",
        "update",
        "insert",
        "alter",
        "create",
        "replace",
        "truncate",
        "attach",
        "detach",
        "pragma",
    )
    if re.search(rf"(?i)\b({'|'.join(blocked_keywords)})\b", normalized):
        return "SQL 包含不允許的關鍵字。"

    return None


def query_database(sql_query: str) -> dict:
    try:
        validation_error = _validate_sql_query(sql_query)
        if validation_error:
            return {"status": "error", "data": None, "message": validation_error}

        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query(sql_query, conn)

        return {
            "status": "success",
            "data": df.to_dict(orient="records"),
            "message": f"查詢完成，共 {len(df)} 筆資料",
        }
    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}
