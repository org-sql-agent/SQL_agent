# agent.py
import os
from openai import OpenAI
from dotenv import load_dotenv
from functions import query_database
from train_model import predict_feature

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 定義 function 給 GPT
tools = [
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
            "description": "預測問題，例如預測性別、艙等、票價或是否生還",
            "parameters": {
                "type": "object",
                "properties": {
                    "Pclass": {"type": "integer", "description": "艙等（1, 2, 3）"},
                    "Sex": {
                        "type": "integer",
                        "description": "性別：male=1 或 female=0",
                    },
                    "Age": {"type": "number", "description": "年齡"},
                    "Fare": {"type": "number", "description": "票價"},
                    "Survived": {
                        "type": "integer",
                        "description": "是否生還（0 或 1）",
                    },
                    "target": {
                        "type": "string",
                        "enum": ["Pclass", "Sex", "Age", "Fare", "Survived"],
                        "description": "分析出要預測的特徵",
                    },
                },
                "required": ["Pclass", "Sex", "Age", "Fare", "Survived", "target"],
            },
        },
    },
]


def ai_agent(history, user_input):
    history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": user_input},
            {
                "role": "system",
                "content": """
你是一個 Titanic AI 助理。
你可以根據使用者問題，如果使用者問題需要訪問資料庫，將其轉換成 SQL 查詢，並使用 query_database 工具來獲取資料。
不要直接回答，必須使用工具完成查詢。
資料庫：SQLite titanic.db
資料表 passengers，欄位：
PassengerId: 乘客ID，
Survived: 是否生還（0 = 否，1 = 是
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

當使用者要求預測時:
1. 根據使用者的問題，確認要預測的特徵與給定的資訊，有給定資訊就是訓練特徵，未給的資訊就是預測標籤。
2. 使用者未輸入的資訊，請給定 None。 
3. 舉例: User: 票價8塊的20歲女生生還了，他是住在哪個艙等? Agent: X:{'Pclass':0,'Sex': 0, 'Age': 20, 'Fare': 8.0, 'Survived': 1,target:Pclass }。
""",
            },
        ]
        + history,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = eval(tool_call.function.arguments)
            print(f"Calling function: {function_name} with arguments: {arguments}")

            if function_name == "query_database":
                result = query_database(arguments["sql_query"])
                print(f"Function result: {result}")

                if result["status"] == "success":
                    # 用 GPT 畫圖 JSON
                    explain_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一個資料視覺化助手，請根據 SQL 查詢結果資料，回傳一個 Apache ECharts 的 option JSON 配置，用來畫圖。只要回傳 JSON，其他文字請省略。"
                            },
                            {"role": "user", "content": f"資料如下：\n{result['data']}"},
                        ]
                    )

                    echarts_json = explain_response.choices[0].message.content.strip()

                    # 用 GPT 幫圖表加中文摘要
                    summary_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一個資料分析助理，請根據查詢結果資料與使用者的問題，簡要生成一段中文摘要，說明圖表趨勢或重點。",
                            },
                            {"role": "user", "content": f"使用者的問題：{user_input}\n查詢結果：{result['data']}"},
                        ]
                    )

                    summary = summary_response.choices[0].message.content.strip()

                    history.append({
                        "role": "assistant",
                        "type": "echarts",
                        "content": echarts_json,
                        "summary": summary
                    })

                    return {
                        "type": "echarts",
                        "content": echarts_json,
                        "summary": summary
                    }
                else:
                    return {"type": "text", "data": None, "content": result["content"]}

            elif function_name == "predict_feature":
                print(f"Predicting survival with arguments: {arguments}")
                result = predict_feature(arguments)

            else:
                result = "未知功能"

        # 第二次請求：將結果交給 GPT 生成自然語言回應
        print(f"Function result: {result}")
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一個 Titanic AI 助理，請根據資料庫查詢結果或是預測結果回答",
                },
            ]
            + history
            + [{"role": "assistant", "content": f"資料庫回傳結果: {result}"}],
        )

        answer = final_response.choices[0].message.content
        history.append({"role": "assistant", "content": answer})
        return {"type": "text", "content": answer}

    else:
        # GPT 沒有選擇 function，直接回應
        answer = message.content
        history.append({"role": "assistant", "content": answer})
        return {"type": "text", "content": answer}
    


    