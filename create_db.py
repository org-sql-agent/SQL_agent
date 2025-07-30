import sqlite3
import pandas as pd

# 讀取 Titanic 資料
df = pd.read_csv("data/train.csv")

# 建立 SQLite DB
conn = sqlite3.connect("titanic.db")
df.to_sql("passengers", conn, if_exists="replace", index=False)
conn.close()

print("資料已匯入 titanic.db")
