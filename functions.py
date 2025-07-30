import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64
import pickle
import matplotlib
import sqlite3
from train_model import train_model

# matplotlib.rcParams["font.sans-serif"] = ["SimHei"]  # 黑體字型
# matplotlib.rcParams["axes.unicode_minus"] = False  # 避免負號顯示錯誤

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


# def plot_data(plot_type: str) -> dict:
#     try:
#         plt.figure(figsize=(6, 4))
#         if "艙等" in plot_type:
#             sns.barplot(x="Pclass", y="Survived", data=df)
#             plt.title("各艙等生還率")
#         elif "性別" in plot_type:
#             sns.barplot(x="Sex", y="Survived", data=df)
#             plt.title("性別生還率")
#         else:
#             return {
#                 "status": "error",
#                 "data": None,
#                 "message": "目前僅支援 '艙等' 或 '性別' 視覺化",
#             }

#         buffer = io.BytesIO()
#         plt.savefig(buffer, format="png")
#         buffer.seek(0)
#         img_base64 = base64.b64encode(buffer.read()).decode()
#         plt.close()

#         return {
#             "status": "success",
#             "data": {"image_base64": img_base64},
#             "message": "圖表產生完成",
#         }
#     except Exception as e:
#         return {"status": "error", "data": None, "message": str(e)}


def plot_data(
    sql_query: str, plot_type: str = "hist", x: str = None, y: str = None
) -> dict:
    try:
        conn = sqlite3.connect("titanic.db")
        df = pd.read_sql_query(sql_query, conn)
        conn.close()

        plt.figure(figsize=(6, 4))
        print(df)
        if plot_type == "bar":
            if x and y:
                sns.barplot(x=x, y=y, data=df)
            else:
                return {"status": "error", "message": "bar 圖需要 x 和 y"}
        elif plot_type == "hist":
            if x:
                sns.histplot(df[x], bins=20, kde=True)
            else:
                return {"status": "error", "message": "hist 需要指定 x"}
        elif plot_type == "pie":
            if x and y:
                print(f"Pie chart with x: {x}, y: {y}")
                print("df[y]", df[y])
                plt.pie(df[y], labels=df[x], autopct="%1.1f%%")

            else:
                return {
                    "status": "error",
                    "message": "pie 需要指定 x，且如果 y 存在需對應數值",
                }
        elif plot_type == "scatter":
            if x and y:
                sns.scatterplot(x=x, y=y, data=df)
            else:
                return {"status": "error", "message": "scatter 需要 x 和 y"}
        else:
            return {"status": "error", "message": "不支援的圖表類型"}

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return {
            "status": "success",
            "data": {"image_base64": img_base64},
            "message": "圖表產生完成",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
