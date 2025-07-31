import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder


# 載入資料


def train_model(user_args: dict):
    print("開始訓練模型...")

    # 讀取 Titanic 資料集
    df = pd.read_csv("data/train.csv")
    print("資料集載入完成，開始特徵工程...")
    df = df[["Pclass", "Sex", "Age", "Fare", "Survived"]]

    # 特徵工程
    df["Sex"] = LabelEncoder().fit_transform(df["Sex"])
    df["Age"].fillna(df["Age"].mean(), inplace=True)
    df["Fare"].fillna(df["Fare"].mean(), inplace=True)

    # 轉換 user_args 的鍵名
    user_args_fixed = {k: v for k, v in user_args.items()}
    print(f"使用者輸入的欄位: {user_args_fixed}")
    # 特徵 X 是使用者有給值的欄位

    # 找出 y_col
    y_col = [user_args["target"]]

    # 找出 X_col
    X_cols = [k for k in user_args if k not in ["target", user_args["target"]]]

    print(f"X 欄位: {X_cols}, y 欄位: {y_col}")
    if len(y_col) != 1:
        return {
            "status": "error",
            "message": f"必須只缺一個欄位作為預測目標，目前缺少的欄位數量為 {len(y_col)}",
        }

    y_col = y_col[0]
    print(f"使用欄位作為 X: {X_cols}，預測目標 Y: {y_col}")

    # 建立 X 與 y
    X = df[X_cols]
    y = df[y_col]

    # 建立模型
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression()
    model.fit(X_train, y_train)
    model_score = model.score(X_test, y_test)
    print("模型準確率:", model.score(X_test, y_test))

    return model, X_cols, y_col, model_score


def predict_feature(params: dict):
    import pandas as pd
    import sqlite3
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.metrics import classification_report, mean_squared_error

    target = params["target"]
    features = [f for f in ["Pclass", "Sex", "Age", "Fare", "Survived"] if f != target]
    model_name = params.get("model_name")  # 可選參數

    # 載入資料
    conn = sqlite3.connect("titanic.db")
    df = pd.read_sql_query("SELECT * FROM passengers", conn)
    conn.close()
    df = df[features + [target]].dropna()
    df["Sex"] = df["Sex"].map({"male": 0, "female": 1})

    X, y = df[features], df[target]
    is_classification = y.nunique() <= 10 and y.dtype in [int, 'int64']

    # 🔍 模型選擇邏輯
    if not model_name:
        model_name = (
            "RandomForestClassifier" if is_classification else "RandomForestRegressor"
        )

    model_map = {
        "RandomForestClassifier": RandomForestClassifier(),
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForestRegressor": RandomForestRegressor(),
        "LinearRegression": LinearRegression()
    }

    if model_name not in model_map:
        return {"error": f"未知模型: {model_name}"}

    model = model_map[model_name]
    model.fit(X, y)

    # 預測
    input_data = pd.DataFrame([params], columns=features)
    predicted = model.predict(input_data)[0]

    # 信心度
    confidence = None
    if is_classification and hasattr(model, "predict_proba"):
        confidence = float(model.predict_proba(input_data).max())

    result = {
        "target": str(target),
        "features_used": [str(f) for f in features],
        "model_name": str(model_name),
        "predicted": predicted.item() if hasattr(predicted, 'item') else predicted,
        "confidence": float(confidence) if confidence is not None else None,
        "feature_importance": [float(x) for x in model.feature_importances_] if hasattr(model, "feature_importances_") else [],
    }

    return result