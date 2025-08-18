import sqlite3
import pandas as pd

df = pd.read_csv("data/train.csv")

conn = sqlite3.connect("titanic.db")
df.to_sql("passengers", conn, if_exists="replace", index=False)
conn.close()

print("資料已匯入 titanic.db")
