import re
import sqlite3

import pandas as pd

from app.config.settings import DATABASE_PATH

_ALL_FEATURES = ("Pclass", "Sex", "Age", "Fare", "Survived")

_BLOCKED_KEYWORDS = (
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


class TitanicDAO:
    def query(self, sql_query: str) -> dict:
        normalized = sql_query.strip()
        if not normalized:
            return {"status": "error", "data": None, "message": "SQL 查詢不可為空。"}
        if ";" in normalized:
            return {
                "status": "error",
                "data": None,
                "message": "只允許單一 SELECT 查詢，禁止使用分號 (;)。",
            }
        if not re.match(r"(?is)^select\b", normalized):
            return {"status": "error", "data": None, "message": "只允許 SELECT 查詢。"}
        if re.search(rf"(?i)\b({'|'.join(_BLOCKED_KEYWORDS)})\b", normalized):
            return {
                "status": "error",
                "data": None,
                "message": "SQL 包含不允許的關鍵字。",
            }

        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                df = pd.read_sql_query(sql_query, conn)
            return {
                "status": "success",
                "data": df.to_dict(orient="records"),
                "message": f"查詢完成，共 {len(df)} 筆資料",
            }
        except Exception as e:
            return {"status": "error", "data": None, "message": str(e)}

    def predict(self, params: dict) -> dict:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.linear_model import LinearRegression, LogisticRegression

        target = params["target"]
        model_name = params.get("model_name")
        features = [f for f in _ALL_FEATURES if f != target]

        with sqlite3.connect(DATABASE_PATH) as conn:
            df = pd.read_sql_query("SELECT * FROM passengers", conn)

        df["Sex"] = df["Sex"].map({"male": 0, "female": 1})
        feature_df = df[features + [target]].dropna().copy()
        X, y = feature_df[features], feature_df[target]
        is_classification = y.nunique() <= 10 and y.dtype in [int, "int64"]

        if not model_name:
            model_name = (
                "RandomForestClassifier"
                if is_classification
                else "RandomForestRegressor"
            )

        model_map = {
            "RandomForestClassifier": RandomForestClassifier,
            "LogisticRegression": lambda: LogisticRegression(max_iter=1000),
            "RandomForestRegressor": RandomForestRegressor,
            "LinearRegression": LinearRegression,
        }
        if model_name not in model_map:
            return {"error": f"未知模型: {model_name}"}

        model = model_map[model_name]()
        model.fit(X, y)

        input_data = pd.DataFrame([params], columns=features)
        for col in features:
            if input_data[col].isna().any():
                if pd.api.types.is_numeric_dtype(X[col]):
                    input_data[col] = input_data[col].fillna(X[col].mean())
                else:
                    input_data[col] = input_data[col].fillna(X[col].mode()[0])

        predicted = model.predict(input_data)[0]
        confidence = None
        if is_classification and hasattr(model, "predict_proba"):
            confidence = float(model.predict_proba(input_data).max())

        return {
            "target": str(target),
            "features_used": [str(f) for f in features],
            "model_name": str(model_name),
            "predicted": predicted.item() if hasattr(predicted, "item") else predicted,
            "confidence": float(confidence) if confidence is not None else None,
            "feature_importance": (
                [float(x) for x in model.feature_importances_]
                if hasattr(model, "feature_importances_")
                else []
            ),
        }
