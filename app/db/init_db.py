import sqlite3

import pandas as pd

from app.config.settings import DATABASE_PATH, TRAIN_DATA_PATH

df = pd.read_csv(TRAIN_DATA_PATH)

conn = sqlite3.connect(DATABASE_PATH)
df.to_sql("passengers", conn, if_exists="replace", index=False)
conn.close()

print(f"資料已匯入 {DATABASE_PATH}")
