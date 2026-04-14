import base64
import os

import requests
import streamlit as st
from streamlit_echarts import st_echarts

from app.utils.json_utils import clean_markdown_json

SERVICE_API_URL = os.getenv("SERVICE_API_URL", "http://localhost:8080/Service")

st.set_page_config(page_title="Titanic AI Agent", layout="wide")
st.title("Titanic AI Agent 🚢 ")

user_input = st.text_input(
    "請輸入問題，例如：'生還率多少？' 或 '畫出生還率和艙等關係' 或 '預測我是否生還'"
)

if "history" not in st.session_state:
    st.session_state["history"] = []

if st.button("送出") and user_input.strip():
    with st.spinner("AI 分析中..."):
        st.session_state["history"].append({"role": "user", "content": user_input})

        try:
            response = requests.post(
                SERVICE_API_URL,
                json={
                    "text": user_input,
                    "history": st.session_state["history"],
                },
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()["data"]
        except requests.RequestException as exc:
            st.error(f"API 呼叫失敗: {exc}")
            st.stop()
        except (KeyError, ValueError) as exc:
            st.error(f"API 回應格式錯誤: {exc}")
            st.stop()

        print(f"AI Response type: {result['type']}")

        assistant_message = {
            "role": "assistant",
            "type": result.get("type"),
            "content": result.get("content", ""),
            "summary": result.get("summary"),
        }

        if result.get("data"):
            assistant_message["data"] = result["data"]

        st.session_state["history"].append(assistant_message)

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
