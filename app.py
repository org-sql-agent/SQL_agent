# app.py
import streamlit as st
from agent import ai_agent
import base64
import json
import re
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Titanic AI Agent", layout="wide")
st.title("Titanic AI Agent 🚢 ")

user_input = st.text_input(
    "請輸入問題，例如：'生還率多少？' 或 '畫出生還率和艙等關係' 或 '預測我是否生還'"
)

if "history" not in st.session_state:
    st.session_state["history"] = []

def clean_markdown_json(content: str) -> dict:
    """
    將 GPT 回傳的 markdown 格式 JSON 移除 ```json ... ``` 並轉成 dict
    """
    try:
        cleaned = re.sub(r"```json|```", "", content).strip()
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"JSON 解碼失敗: {e}")
        return None

if st.button("送出") and user_input.strip():
    with st.spinner("AI 分析中..."):
        result = ai_agent(st.session_state["history"], user_input)
        print(f"AI Response type: {result['type']}")

        if result["type"] == "image":
            img_data = result["data"].get("image_base64", None)
            if img_data:
                st.image(base64.b64decode(img_data), use_container_width=True)
                st.caption(f"🤖 {result['content']}")
            else:
                st.error("圖片資料缺失")

        elif result["type"] == "echarts":
            option = clean_markdown_json(result["content"])
            if option:
                st_echarts(options=option, height="500px", key="latest-chart")
                st.caption(f"🤖 {result.get('summary', '（未提供摘要）')}")
            else:
                st.error("圖表資料解析失敗")

        else:  # text or fallback
            st.write(result["content"])

st.subheader("對話紀錄")
for i, h in enumerate(st.session_state["history"]):
    if h["role"] == "user":
        st.write(f"User👤 {h['content']}")

    elif h["role"] == "assistant":
        if h.get("type") == "image":
            st.image(base64.b64decode(h["image_base64"]), use_container_width=True)
            st.caption(f"🤖 {h['content']}")

        elif h.get("type") == "echarts":
            option = clean_markdown_json(h["content"])
            if option:
                st_echarts(options=option, height="500px", key=f"chart-{i}")
                st.caption(f"🤖 {h.get('summary', '（未提供摘要）')}")
            else:
                st.error("圖表載入失敗")

        else:
            st.write(f"🤖 {h['content']}")