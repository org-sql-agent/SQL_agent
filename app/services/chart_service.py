from openai import OpenAI


class ChartService:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def generate_echarts(self, data) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一個資料視覺化助手，請根據 SQL 查詢結果資料，回傳一個 Apache ECharts 的 option JSON 配置，用來畫圖。只要回傳 JSON，其他文字請省略。",
                },
                {"role": "user", "content": f"資料如下：\n{data}"},
            ],
        )
        return response.choices[0].message.content.strip()

    def generate_summary(self, user_input: str, data) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一個資料分析助理，請根據查詢結果資料與使用者的問題，簡要生成一段中文摘要，說明圖表趨勢或重點。",
                },
                {
                    "role": "user",
                    "content": f"使用者的問題：{user_input}\n查詢結果：{data}",
                },
            ],
        )
        return response.choices[0].message.content.strip()

    def generate_prediction_explanation(self, user_input: str, result: dict) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一個 Titanic 機器學習預測分析助手。請根據模型預測結果與特徵，簡要用中文解釋模型預測了什麼、可信度為何，以及哪些特徵對結果最重要。",
                },
                {
                    "role": "user",
                    "content": f"使用者問題：{user_input}\n預測結果：{result}",
                },
            ],
        )
        return response.choices[0].message.content.strip()

    def generate_feature_importance_chart(self, result: dict) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一個資料視覺化助手，請根據特徵與重要性分數，產生一份 Apache ECharts 的 option JSON 配置，用來畫出特徵重要性的條狀圖。只回傳 JSON。",
                },
                {
                    "role": "user",
                    "content": f"特徵：{result['features_used']}\n重要性：{result['feature_importance']}",
                },
            ],
        )
        return response.choices[0].message.content.strip()
