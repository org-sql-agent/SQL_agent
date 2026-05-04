import json

from openai import OpenAI

from app.db.dao.titanic_dao import TitanicDAO
from app.services.chart_service import ChartService
from app.services.compact.history_compactor import maybe_compact

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "執行 SQL 查詢 Titanic 乘客資料庫",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "SQL 查詢，例如 SELECT AVG(Age) FROM passengers WHERE Survived=1",
                    }
                },
                "required": ["sql_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_feature",
            "description": "即時訓練模型並預測指定特徵，例如預測性別、艙等、票價或是否生還",
            "parameters": {
                "type": "object",
                "properties": {
                    "Pclass": {"type": "integer", "description": "艙等（1, 2, 3）"},
                    "Sex": {"type": "integer", "description": "性別：male=0，female=1"},
                    "Age": {"type": "number", "description": "年齡"},
                    "Fare": {"type": "number", "description": "票價"},
                    "Survived": {"type": "integer", "description": "是否生還（0 或 1）"},
                    "target": {
                        "type": "string",
                        "enum": ["Pclass", "Sex", "Age", "Fare", "Survived"],
                        "description": "要預測的欄位",
                    },
                    "model_name": {
                        "type": "string",
                        "enum": [
                            "RandomForestClassifier",
                            "LogisticRegression",
                            "RandomForestRegressor",
                            "LinearRegression",
                        ],
                        "description": "要使用的模型名稱，若不指定則根據任務自動判斷",
                    },
                },
                "required": ["target"],
            },
        },
    },
]

_SYSTEM_PROMPT = """
你是一個 Titanic AI 助理。
你可以根據使用者問題，如果使用者問題需要訪問資料庫，將其轉換成 SQL 查詢，並使用 query_database 工具來獲取資料。
不要直接回答，必須使用工具完成查詢。
資料庫：SQLite titanic.db
資料表 passengers，欄位：
PassengerId: 乘客ID，
Survived: 是否生還（0 = 否，1 = 是,
Pclass: 艙等（1 = 頭等艙，2 = 二等艙，3 = 三等艙,
Name: 乘客姓名,
Sex: "male" 表示男性，"female" 表示女性,
Age: 年齡,
SibSp: 同行兄弟姊妹/配偶人數,
Parch: 同行父母/子女人數,
Ticket: 船票號碼,
Fare: 票價,
Cabin: 船艙號碼,
Embarked: 登船港口。
只能使用 SELECT 語句，不允許 DROP、DELETE、UPDATE、INSERT。

當使用者要求繪圖時：
1. 判斷需要的欄位，建立 SQL 查詢
2. 使用 query_database 工具查詢資料
3. 根據查詢結果，自行產生 ECharts 所需的 option JSON
4. 回傳 JSON 格式的圖表配置（option），不要轉成圖片，也不要使用 plot_data。

當使用者要求預測時：

1. 根據使用者的問題，確認要預測的特徵（target）與給定的欄位（features），有給定值的就是訓練用特徵，未給的欄位即為要預測的目標欄位。
2. 所有未給的欄位請填入 None。
3. 預測功能會即時訓練模型，不需要事先訓練。模型將根據目標欄位自動選擇分類或回歸模型。
4. 如有需要，也可使用者明確指定模型名稱（model_name），
   支援：`RandomForestClassifier`, `LogisticRegression`, `RandomForestRegressor`, `LinearRegression`。
5. 輸出結果將包括預測值、信心度（若可用）、特徵重要性，並自動以圖表呈現。

舉例：
User: 票價8塊的20歲女生生還了，她住在哪個艙等？
Agent tool_call: predict_feature(
  {
    "Pclass": None,
    "Sex": 0,
    "Age": 20,
    "Fare": 8.0,
    "Survived": 1,
    "target": "Pclass"
  }
)
"""


class AgentService:
    def __init__(self, dao: TitanicDAO, chart_service: ChartService, client: OpenAI, model: str):
        self.dao = dao
        self.chart_service = chart_service
        self.client = client
        self.model = model

    def run(self, history: list, user_input: str) -> tuple[dict, list]:
        compacted_base = maybe_compact(history, user_input, self.client, self.model)
        llm_history = list(compacted_base)
        llm_history.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": _SYSTEM_PROMPT}] + llm_history,
            tools=_TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return {"type": "text", "content": message.content}, compacted_base

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Calling function: {function_name} with arguments: {arguments}")

            if function_name == "query_database":
                result = self._handle_query_database(arguments, llm_history, user_input)
            elif function_name == "predict_feature":
                result = self._handle_predict_feature(arguments, llm_history, user_input)
            else:
                print(f"Unknown function: {function_name}")
                continue

            if result is not None:
                return result, compacted_base

        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一個 Titanic AI 助理，請根據資料庫查詢結果或是預測結果回答"},
            ] + llm_history,
        )
        return {"type": "text", "content": final_response.choices[0].message.content}, compacted_base

    def _handle_query_database(self, arguments: dict, history: list, user_input: str) -> dict | None:
        result = self.dao.query(arguments["sql_query"])
        print(f"Function result: {result}")

        if result["status"] != "success":
            return {"type": "text", "data": None, "content": result.get("message", "資料庫查詢失敗")}

        echarts_json = self.chart_service.generate_echarts(result["data"])
        summary = self.chart_service.generate_summary(user_input, result["data"])

        history.append({"role": "assistant", "type": "echarts", "content": echarts_json, "summary": summary})
        return {"type": "echarts", "content": echarts_json, "summary": summary}

    def _handle_predict_feature(self, arguments: dict, history: list, user_input: str) -> dict | None:
        print(f"Predicting with arguments: {arguments}")
        result = self.dao.predict(arguments)

        history.append({"role": "function", "name": "predict_feature", "content": json.dumps(result)})

        explanation = self.chart_service.generate_prediction_explanation(user_input, result)

        if result.get("feature_importance"):
            echarts_json = self.chart_service.generate_feature_importance_chart(result)
            history.append({"role": "assistant", "type": "echarts", "content": echarts_json, "summary": explanation})
            return {"type": "echarts", "content": echarts_json, "summary": explanation}

        history.append({"role": "assistant", "content": explanation})
        return {"type": "text", "content": explanation}
