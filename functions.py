import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64
import pickle
import matplotlib
import sqlite3
from train_model import train_model

# 載入資料 & 模型
df = pd.read_csv("data/train.csv")
with open("model/titanic_model.pkl", "rb") as f:
    model = pickle.load(f)


def query_database(sql_query: str) -> dict:
    try:
        conn = sqlite3.connect("titanic.db")
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return {
            "status": "success",
            "data": df.to_dict(orient="records"),
            "message": f"查詢完成，共 {len(df)} 筆資料",
        }
    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}
