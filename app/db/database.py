import sqlite3

import pandas as pd

from app.core.service.config import DATABASE_PATH


def query_database(sql_query: str) -> dict:
    try:
        print('sssss',DATABASE_PATH)
        conn = sqlite3.connect("/Users/emma/david/SQL_agent/model/titanic.db")
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return {
            "status": "success",
            "data": df.to_dict(orient="records"),
            "message": f"查詢完成，共 {len(df)} 筆資料",
        }
    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}
