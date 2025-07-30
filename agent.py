import os
from openai import OpenAI
from dotenv import load_dotenv
from functions import query_database, plot_data
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
            "name": "plot_data",
            "description": "根據 SQL 查詢結果繪製圖表",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {"type": "string", "description": "SQL 查詢語句"},
                    "plot_type": {
                        "type": "string",
                        "enum": ["bar", "hist", "pie", "scatter"],
                        "description": "圖表類型",
                    },
                    "x": {"type": "string", "description": "x 軸欄位"},
                    "y": {
                        "type": "string",
                        "description": "y 軸欄位（對於 bar/scatter/pie 必須指定）",
                    },
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
    # 第一次請求：讓 GPT-4 判斷要呼叫哪個 function
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
                PassengerId, Survived, Pclass, Name, Sex, Age, SibSp, Parch, Ticket, Fare, Cabin, Embarked。
                只能使用 SELECT 語句，不允許 DROP、DELETE、UPDATE、INSERT。
                當使用者要求繪圖時：
                1. 判斷需要的欄位
                2. 建立 SQL 查詢
                3. 決定圖表類型：條形圖(bar)、直方圖(hist)、圓餅圖(pie)、散點圖(scatter)
                4. 呼叫 plot_data，並傳入 sql_query、plot_type 以及 x, y（若需要）
                如果使用者沒有指定圖表類型，預設使用 hist。

                當使用者要求預測時:
                1. 根據使用者的問題，確認要預測的特徵與給定的資訊，有給定資訊就是訓練特徵，未給的資訊就是預測標籤。
                2.使用者未輸入的資訊，請給定None。 
                3.舉例: User:票價8塊的20歲女生生還了，他是住在哪個艙等? Agent: X:{'Pclass':0,'Sex': 0, 'Age': 20, 'Fare': 8.0, 'Survived': 1,target:Pclass }。
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

            elif function_name == "plot_data":
                result = plot_data(
                    arguments["sql_query"],
                    arguments.get("plot_type", "hist"),
                    arguments.get("x"),
                    arguments.get("y"),
                )
                if result["status"] == "success":
                    df = query_database(arguments["sql_query"])["data"]
                    # 簡化 SQL 結果給 GPT
                    sql_summary = f"這張圖表使用的資料來自 SQL: {arguments['sql_query']}，圖表類型是 {arguments.get('plot_type', 'hist')}，圖中的資料為{df}。請幫我用中文簡短描述這張圖顯示的重點趨勢。"

                    explanation_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一個資料分析助理，請用簡潔專業的中文描述圖表重點。",
                            },
                            {"role": "user", "content": sql_summary},
                        ],
                    )

                    explanation = explanation_response.choices[
                        0
                    ].message.content.strip()

                    history.append(
                        {
                            "role": "assistant",
                            "type": "image",
                            "content": explanation,
                            "image_base64": result["data"]["image_base64"],
                        }
                    )

                    return {
                        "type": "image",
                        "data": result["data"],
                        "content": explanation,
                    }
                else:
                    return {"type": "text", "data": None, "content": result["content"]}

            elif function_name == "predict_feature":
                print(f"Predicting survival with arguments: {arguments}")

                result = predict_feature(arguments)
            else:
                result = "未知功能"

        # 第二次請求：將結果交給 GPT-4 生成自然語言回應
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
